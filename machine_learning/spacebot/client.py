import asyncio
import uuid
from termcolor import colored
from typing import Callable

from machine_learning.spacebot.definitions import SpaceBotServer, SpaceBotClient

from machine_learning.spacebot.machine_learning.spacebot.spacebot_pb2 import SpaceBotStatus

USER_INPUT_MSG = f'{colored("User:", "blue")} '


class TerminalSpaceBotClient(SpaceBotClient):

    def __init__(self,
                 server: SpaceBotServer,
                 input_fn: Callable[..., str] = None,
                 print_fn: Callable[[str], None] = None):
        self.valid = False

        if not input_fn:
            input_fn = input
        if not print_fn:
            print_fn = print
        self.input_fn = input_fn
        self.print_fn = print_fn

        self.session = uuid.uuid4()
        self.server = server

    def _print(self, text: str | None = None) -> None:
        if text is None:
            self.print_fn()
        else:
            self.print_fn(text)

    def _input(self, label: str) -> str:
        return self.input_fn(label)

    def _print_separator(self):
        self._print()
        self._print()

    def _print_alien_msg(self, msg: str) -> None:
        entity_name = colored('Alien:', 'red')
        text = colored(msg, 'white')
        self._print(f'{entity_name} {text}')

    async def _fetch_and_print_alien_msg(self) -> bool:
        alien_msg_result = await self.server.fetch_alien_msg(self.session)
        if alien_msg_result.status != SpaceBotStatus.SUCCESS:
            if alien_msg_result.message:
                self._print(alien_msg_result.message)
            return False
        self._print_alien_msg(alien_msg_result.message)
        return True

    async def initialize(self) -> None:
        creation_result = await self.server.create_chat(self.session)
        if creation_result.status != SpaceBotStatus.SUCCESS:
            if creation_result.message:
                self._print(creation_result.message)
            return
        self.valid = True

    async def run(self) -> int:
        self._print_separator()
        retcode = 0

        # Get initial alien message.
        if not await self._fetch_and_print_alien_msg():
            retcode = 1
        else:
            while True:
                # Get next usesr message.
                user_msg = self._input(USER_INPUT_MSG).strip()
                # Exit if no message.
                if not user_msg:
                    self._print_alien_msg('Goodbye!')
                    break
                # Try to add the message
                user_msg_result = await self.server.process_user_msg(
                    self.session, user_msg)
                if user_msg_result.status == SpaceBotStatus.ALIEN_ERROR:
                    self._print_alien_msg(user_msg_result.message)
                    continue
                elif user_msg_result.status != SpaceBotStatus.SUCCESS:
                    if user_msg_result.message:
                        self._print(user_msg_result.message)
                    if user_msg_result.status == SpaceBotStatus.FATAL_ERROR:
                        retcode = 1
                        break
                    else:
                        continue
                # Get next alien message if all is well.
                if not await self._fetch_and_print_alien_msg():
                    retcode = 1
                    break
            await self.server.end_chat(self.session)

        self._print_separator()
        return retcode
