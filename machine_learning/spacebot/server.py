import threading
import grpc
import sys
import time
import signal
from concurrent import futures

from machine_learning.common import utilities
from machine_learning.common.openai_api import Chat, fetch_api_key, load_prompt_injection_declination_instructions, load_prompt_injection_instructions, meta_prompt, meta_prompt_y, moderation, moderation_flagged
from machine_learning.common.openai_api import Examples, StringDictionary
from machine_learning.spacebot.constants import DEFAULT_PORT

import google.protobuf
from machine_learning.spacebot.spacebot_pb2 import SpaceBotStatus, SpaceBotResult, CreateChatRequest, EndChatRequest, FetchAlienMessageRequest, ProcessUserMessageRequest
from machine_learning.spacebot.spacebot_pb2_grpc import SpaceBotServiceServicer, add_SpaceBotServiceServicer_to_server

TEMPERATURE = 1.0
DEFAULT_SERVER = 'localhost'

class InMemorySpaceBotServer(SpaceBotServiceServicer):
    sessions: dict[str, Chat] = {}

    def __init__(self, server: grpc.Server):
        self.server = server
        self.lock = threading.Lock()

        self.messages: StringDictionary = {}
        self.errors: StringDictionary = {}
        self.injection_examples: Examples = {}
        self.declination_examples: Examples = {}

        self._load_msgs()
        self.valid = fetch_api_key()

    def _load_msgs(self) -> None:
        self.errors = utilities.load_json_data_file(
            'server_messages/server_errors.json')
        self.messages = utilities.load_data_files(files={
            'system': 'server_messages/alien_system.txt',
        })
        self.injection_examples = utilities.load_json_data_file(
            'server_messages/prompt_injection_examples.json')
        self.declination_examples = utilities.load_json_data_file(
            'server_messages/prompt_injection_declination_examples.json')

        self.messages['injections'] = load_prompt_injection_instructions()
        self.messages[
            'injection_decline'] = load_prompt_injection_declination_instructions(
            )

    def CreateChat(self, request: CreateChatRequest, context: grpc.ServicerContext) -> SpaceBotResult:
        if not self.valid:
            return SpaceBotResult(status=SpaceBotStatus.FATAL_ERROR,
                                  message=self.errors['apiKeyError'])

        with self.lock:
            if request.session_id in self.sessions:
                return SpaceBotResult(
                    status=SpaceBotStatus.FATAL_ERROR,
                    message=self.errors['sessionAlreadyExists'])
            chat = Chat(temperature=TEMPERATURE)
            self.sessions[request.session_id] = chat
        chat.add_system_msg(self.messages['system'])

        return SpaceBotResult()

    def EndChat(self, request: EndChatRequest, context: grpc.ServicerContext) -> google.protobuf.empty_pb2.Empty:
        with self.lock:
            if request.session_id in self.sessions:
                del self.sessions[request.session_id]
        return google.protobuf.empty_pb2.Empty()

    def _fetch_alien_msg(self,
                               session_id: str,
                               retries: int = 3) -> str | None:
        with self.lock:
            chat = self.sessions[session_id]

        alien_msg = chat.predict_assistant_msg()
        if moderation(alien_msg, fn=moderation_flagged):
            chat.remove_msg()
            retries -= 1
            if retries:
                return self._fetch_alien_msg(session_id, retries)
            else:
                return None
        return alien_msg

    def FetchAlienMessage(self, request: FetchAlienMessageRequest, context: grpc.ServicerContext) -> SpaceBotResult:
        alien_msg = self._fetch_alien_msg(request.session_id)
        if alien_msg:
            return SpaceBotResult(message=alien_msg)
        else:
            return SpaceBotResult(status=SpaceBotStatus.FATAL_ERROR,
                                  message=self.errors['moderationErrorAlien'])

    def _fetch_rejection_msg(self, user_msg: str) -> SpaceBotResult:
        rejection_msg = meta_prompt(user_msg=user_msg,
                                    meta_msg=self.messages['injection_decline'],
                                    system_msg=self.messages['system'],
                                    examples=self.declination_examples,
                                    output_delim=None)

        if moderation(rejection_msg, fn=moderation_flagged):
            return SpaceBotResult(status=SpaceBotStatus.FATAL_ERROR,
                                  message=self.errors['moderationErrorAlien'])
        return SpaceBotResult(status=SpaceBotStatus.ALIEN_ERROR,
                              message=rejection_msg)

    def ProcessUserMessage(self, request: ProcessUserMessageRequest, context: grpc.ServicerContext) -> SpaceBotResult:
        with self.lock:
            chat = self.sessions[request.session_id]

        # Reject message if moderation issue.
        if moderation(request.user_message, fn=moderation_flagged):
            return SpaceBotResult(status=SpaceBotStatus.NONFATAL_ERROR,
                                  message=self.errors['moderationErrorUser'])
        chat.add_user_msg(request.user_message)

        # Reject prompt injections.
        if meta_prompt(user_msg=request.user_message,
                       meta_msg=self.messages['injections'],
                       system_msg=self.messages['system'],
                       examples=self.injection_examples,
                       fn=meta_prompt_y):
            #print('Prompt Injection Detected!')
            rejection_msg_result = self._fetch_rejection_msg(request.user_message)
            if rejection_msg_result.status == SpaceBotStatus.ALIEN_ERROR:
                chat.add_assistant_msg(rejection_msg_result.message)
            return rejection_msg_result

        # Normal case.
        return SpaceBotResult()

def main(port: str) -> int:
    # Create a gRPC server
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server = InMemorySpaceBotServer(grpc_server)
    
    # Add the servicer to the server
    add_SpaceBotServiceServicer_to_server(server, grpc_server)

    # Listen on a port
    grpc_server.add_insecure_port(f'{DEFAULT_SERVER}:{port}')

    # Start the server
    grpc_server.start()
    # Set up signalling from shell script.
    should_quit = False
    def set_should_quit(*args):
        nonlocal should_quit
        should_quit = True
    signal.signal(signal.SIGINT, set_should_quit)
    # Listen for client connections and signals.
    try:
        print()
        print('Listening for client connections!')
        print()
        while not should_quit:
            time.sleep(1)
        # If quit from shell script, we need to raise the exception ourselves.
        # If quit from ctrl-c in direct execution, it will already be raised.
        raise KeyboardInterrupt
    # This will get triggered either from direct ctrl-c or from shell script SIGINT.
    except KeyboardInterrupt:
        print()
        print('Received stop signal!')
        print()
        grpc_server.stop(0)
        print()
        print('Stopping Server!')
        print()

    return 0

if __name__ == "__main__":
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        port = sys.argv[1]
    
    sys.exit(main(port))
