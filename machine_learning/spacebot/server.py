import asyncio
import uuid

from machine_learning.common import utilities
from machine_learning.common.openai_api import Chat, fetch_api_key, load_prompt_injection_declination_instructions, load_prompt_injection_instructions, meta_prompt, meta_prompt_y, moderation, moderation_flagged
from machine_learning.common.openai_api import Examples, StringDictionary

from machine_learning.spacebot.definitions import SpaceBotServer
from machine_learning.spacebot.spacebot_pb2 import SpaceBotStatus, SpaceBotResult

TEMPERATURE = 1.0


class InMemorySpaceBotServer(SpaceBotServer):
    sessions: dict[str, Chat] = {}

    def __init__(self):
        self.lock = asyncio.Lock()

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

    async def create_chat(self, sessionId: uuid.UUID) -> SpaceBotResult:
        if not self.valid:
            return SpaceBotResult(status=SpaceBotStatus.FATAL_ERROR,
                                  message=self.errors['apiKeyError'])

        async with self.lock:
            if sessionId in self.sessions:
                return SpaceBotResult(
                    status=SpaceBotStatus.FATAL_ERROR,
                    message=self.errors['sessionAlreadyExists'])
            chat = Chat(temperature=TEMPERATURE)
            self.sessions[sessionId] = chat
        chat.add_system_msg(self.messages['system'])

        return SpaceBotResult()

    async def end_chat(self, sessionId: uuid.UUID) -> None:
        async with self.lock:
            if sessionId in self.sessions:
                del self.sessions[sessionId]

    async def _fetch_alien_msg(self,
                               sessionId: uuid.UUID,
                               retries: int = 3) -> str | None:
        async with self.lock:
            chat = self.sessions[sessionId]

        alien_msg = chat.predict_assistant_msg()
        if moderation(alien_msg, fn=moderation_flagged):
            chat.remove_msg()
            retries -= 1
            if retries:
                return self._fetch_alien_msg(sessionId, retries)
            else:
                return None
        return alien_msg

    async def fetch_alien_msg(self, sessionId: uuid.UUID) -> SpaceBotResult:
        alien_msg = await self._fetch_alien_msg(sessionId)
        if alien_msg:
            return SpaceBotResult(message=alien_msg)
        else:
            return SpaceBotResult(status=SpaceBotStatus.FATAL_ERROR,
                                  message=self.errors['moderationErrorAlien'])

    async def _fetch_rejection_msg(self, user_msg: str) -> SpaceBotResult:
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

    async def process_user_msg(self, sessionId: uuid.UUID,
                               user_msg: str) -> SpaceBotResult:
        async with self.lock:
            chat = self.sessions[sessionId]

        # Reject message if moderation issue.
        if moderation(user_msg, fn=moderation_flagged):
            return SpaceBotResult(status=SpaceBotStatus.NONFATAL_ERROR,
                                  message=self.errors['moderationErrorUser'])
        chat.add_user_msg(user_msg)

        # Reject prompt injections.
        if meta_prompt(user_msg=user_msg,
                       meta_msg=self.messages['injections'],
                       system_msg=self.messages['system'],
                       examples=self.injection_examples,
                       fn=meta_prompt_y):
            #print('Prompt Injection Detected!')
            rejection_msg_result = await self._fetch_rejection_msg(user_msg)
            if rejection_msg_result.status == SpaceBotStatus.ALIEN_ERROR:
                chat.add_assistant_msg(rejection_msg_result.message)
            return rejection_msg_result

        # Normal case.
        return SpaceBotResult()
