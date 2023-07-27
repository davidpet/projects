"""Server-side SpaceBot code."""

import threading
import grpc
import sys
import time
import signal
from concurrent import futures
import google.protobuf

from machine_learning.common import utilities
from machine_learning.common.openai_api import Chat, fetch_api_key, load_prompt_injection_declination_instructions, load_prompt_injection_instructions, meta_prompt, meta_prompt_y, moderation, moderation_flagged
from machine_learning.common.openai_api import Examples, StringDictionary
from machine_learning.spacebot.constants import DEFAULT_PORT

from machine_learning.spacebot.spacebot_pb2 import SpaceBotStatus, SpaceBotResult, CreateChatRequest, EndChatRequest, FetchAlienMessageRequest, ProcessUserMessageRequest
from machine_learning.spacebot.spacebot_pb2_grpc import SpaceBotServiceServicer, add_SpaceBotServiceServicer_to_server

TEMPERATURE = 1.0
DEFAULT_SERVER = 'localhost'


class InMemorySpaceBotServer(SpaceBotServiceServicer):
    """
    SpaceBot server that keeps all its data in memory.

    Later, when SpaceBot moves to the cloud, this will need
    to be replaced with one that uses FireStore or something.
    But this implementation is useful for simple local runs.

    Attributes:
        sessions (dict[str, Chat], static): the currently open sessions
        server (grpc.Server): the grpc server instance wrapped by this instance
        lock (threading.Lock): lock used for making self.sessions thread-safe
        messages (StringDictionary): string messages from the `server_messages`
                                     folder to be loaded on construction.
        errors (StringDictionary): error messages from the `server_messages`
                                   folder to be loaded on construction.
        injection_examples (Examples): few-shot learning examples for detecting
                                       prompt injections.  Loaded from
                                       `server_messages` on construction.
        declination_examples (Examples): few-shot learning examples for
                                         politely declining a prompt injection.
                                         Loaded from `server_messages` on
                                         construction.
        valid (bool): set to true if constructor finishes with no errors, which
                      includes setting of the API key.
    """

    sessions: dict[str, Chat] = {}

    server: grpc.Server
    lock: threading.Lock

    messages: StringDictionary
    errors: StringDictionary
    injection_examples: Examples
    declination_examples: Examples

    valid: bool

    def __init__(self, server: grpc.Server):
        """
        Create a new instance.

        Messages are loaded from disk and API key is fetched.

        Args:
            server (grpc.Server): the grpc server wrapped by the instance.
        """

        self.server = server
        self.lock = threading.Lock()

        self.messages: StringDictionary = {}
        self.errors: StringDictionary = {}
        self.injection_examples: Examples = {}
        self.declination_examples: Examples = {}

        self._load_msgs()
        self.valid = fetch_api_key()

    def _load_msgs(self) -> None:
        """
        Load messages from disk for things like errors, prompt injections, etc.
        """

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

    def CreateChat(self, request: CreateChatRequest,
                   context: grpc.ServicerContext) -> SpaceBotResult:
        """
        Create a new chat session.

        Takes session ID from client and adds into self.sessions storage.

        Fails is session ID already exists.

        Args:
            request (CreateChatRequest): the request from the client
            context (grpc.ServicerContext): unused (needed by gRPC interface)

        Returns:
            SpaceBotResult: result for the client
        """

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

    def EndChat(
            self, request: EndChatRequest,
            context: grpc.ServicerContext) -> google.protobuf.empty_pb2.Empty:
        """
        End a chat session, removing the session's chat history from storage.

        Args:
            request (EndChatRequest): request from client
            context (grpc.ServicerContext): unused (needed by gRPC interface)

        Returns:
            google.protobuf.empty_pb2.Empty: nothing to return
        """

        with self.lock:
            if request.session_id in self.sessions:
                del self.sessions[request.session_id]
        return google.protobuf.empty_pb2.Empty()

    def _fetch_alien_msg(self, session_id: str, retries: int = 3) -> str | None:
        """
        Try to get a new alien message from the OpenAI API.

        Retry the given number of times if the alien message fails OpenAI's
        own Moderation API for inappropriate content.

        Args:
            session_id (str): the client session
            retries (int, optional): number of times to try before failing. Defaults to 3.

        Returns:
            str | None: the new alien message, or None if fails Moderation API.
        """

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

    def FetchAlienMessage(self, request: FetchAlienMessageRequest,
                          context: grpc.ServicerContext) -> SpaceBotResult:
        """
        Try to get a new alien message from the OpenAI API.

        The main reason it can fail is if OpenAI keeps returning messages
        that fail their own Moderation API.  It's unlikely.

        Args:
            request (FetchAlienMessageRequest): the request from the client
            context (grpc.ServicerContext): unused (needed by gRPC interface)

        Returns:
            SpaceBotResult: result for the client
        """

        alien_msg = self._fetch_alien_msg(request.session_id)
        if alien_msg:
            return SpaceBotResult(message=alien_msg)
        else:
            return SpaceBotResult(status=SpaceBotStatus.FATAL_ERROR,
                                  message=self.errors['moderationErrorAlien'])

    def _fetch_rejection_msg(self, user_msg: str) -> SpaceBotResult:
        """
        Under the assumption that user_msg is a prompt injection,
        try to get a message to politely decline to follow the
        user's line of thought.

        The result will be passed through the Moderation API just to be safe,
        and thus could fail for that reason.

        Args:
            user_msg (str): the user message containing the prompt injection

        Returns:
            SpaceBotResult: result for the client
        """

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

    def ProcessUserMessage(self, request: ProcessUserMessageRequest,
                           context: grpc.ServicerContext) -> SpaceBotResult:
        """
        Take a new user message and try to add it to the chat history.

        All the various failure modes in SpaceBotResult can be returned.
        For instance, the user can fail the Moderation API or try to
        commit a prompt injection.

        Args:
            request (ProcessUserMessageRequest): the request from the client
            context (grpc.ServicerContext): unused (needed by gRPC interface)

        Returns:
            SpaceBotResult: result for the client
        """

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
            rejection_msg_result = self._fetch_rejection_msg(
                request.user_message)
            if rejection_msg_result.status == SpaceBotStatus.ALIEN_ERROR:
                chat.add_assistant_msg(rejection_msg_result.message)
            return rejection_msg_result

        # Normal case.
        return SpaceBotResult()


def main(port: str) -> int:
    """
    The main server program loop.

    Loads the grpc server and wraps it with an InMemorySpaceBotServer instance.

    Can respond to quit messages either via SIGINT or ctrl-c.

    Args:
        port (str): the port to listen on

    Raises:
        KeyboardInterrupt: used to respond to quit signals

    Returns:
        int: exit code for the terminal
    """

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
