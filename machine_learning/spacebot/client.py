"""Client-side SpaceBot code."""

import grpc
import uuid
import sys
from termcolor import colored
from typing import Callable

from machine_learning.spacebot.constants import DEFAULT_PORT

from machine_learning.spacebot.spacebot_pb2 import SpaceBotStatus, CreateChatRequest, FetchAlienMessageRequest, ProcessUserMessageRequest, EndChatRequest
from machine_learning.spacebot.spacebot_pb2_grpc import SpaceBotServiceStub

USER_INPUT_MSG = f'{colored("User:", "blue")} '
DEFAULT_SERVER = 'localhost'


class TerminalSpaceBotClient:
    """
    SpaceBot chat client that runs as a terminal process.

    Attributes:
        valid (bool): whether the client initialized successfully
        input_fn (Callable[...,str]): function to use for getting input from
                                      the user.
        print_fn (Callable[str]): function to use for printing to the terminal.
        session (str): session ID to use for this client instance
        channel (grpc.Channel): the channel to use for grpc communications
                                with the server
        stub (SpaceBotServiceStub): the grpc stub to use for calling the server
    """

    valid: bool

    input_fn: Callable[..., str]
    print_fn: Callable[[str], None]

    session: str

    channel: grpc.Channel
    stub: SpaceBotServiceStub

    def __init__(self,
                 server_address: str,
                 input_fn: Callable[..., str] | None = None,
                 print_fn: Callable[[str], None] | None = None):
        """
        Create a new instance.

        All attributes will be set, but self.valid will still be False until
        you call self.initialize() to finish setting up.

        Args:
            server_address (str): full address (inc. port) to use for connecting
                                  to SpaceBot server.
            input_fn (Callable[..., str] | None, optional): Function to use for
                                                            user input.
                                                            Defaults to None,
                                                            which means to use
                                                            built-in input().
            print_fn (Callable[[str], None] | None, optional): Function to use
                                                               for printing.
                                                               Defaults to None
                                                               which means to
                                                               use built-in
                                                               print().
        """

        self.valid = False

        if not input_fn:
            input_fn = input
        if not print_fn:
            print_fn = print
        self.input_fn = input_fn
        self.print_fn = print_fn

        self.session = str(uuid.uuid4())
        self.channel = grpc.insecure_channel(server_address)
        self.stub = SpaceBotServiceStub(self.channel)

    def _print(self, text: str | None = None) -> None:
        if text is None:
            self.print_fn()
        else:
            self.print_fn(text)

    def _input(self, label: str) -> str:
        return self.input_fn(label)

    def _print_separator(self) -> None:
        self._print()
        self._print()

    def _print_alien_msg(self, msg: str) -> None:
        """
        Print a single alien message to the terminal with label.

        Args:
            msg (str): the message to print
        """

        entity_name = colored('Alien:', 'red')
        text = colored(msg, 'white')
        self._print(f'{entity_name} {text}')

    def _fetch_and_print_alien_msg(self) -> bool:
        """
        Get an alien message from the server and print it to the terminal.

        If the server returns a message, that will be printed regardless
        of success or failure.
        However, on failure, the message will be printed as raw text instead
        of as an alien message.
        On failure with no message, nothing will be printed.

        Returns:
            bool: true on success
        """

        alien_msg_result = self.stub.FetchAlienMessage(
            FetchAlienMessageRequest(session_id=self.session))
        if alien_msg_result.status != SpaceBotStatus.SUCCESS:
            if alien_msg_result.message:
                self._print(alien_msg_result.message)
            return False
        self._print_alien_msg(alien_msg_result.message)
        return True

    def initialize(self) -> None:
        """
        Perform initial handshake with the server and start the chat history.

        NOTE: the client does not maintain chat history.  The server maintains
              it based on the session ID and the client just sends the next
              message.

        This needs to be called (and succeed) for self.valid to become True.

        Any error from the server will be printed as naked text.
        """

        creation_result = self.stub.CreateChat(
            CreateChatRequest(session_id=self.session))
        if creation_result.status != SpaceBotStatus.SUCCESS:
            if creation_result.message:
                self._print(creation_result.message)
            return
        self.valid = True

    def run(self) -> int:
        """
        Run the main client program loop until terminatation.

        Each loop will get a message from the user and then the alien, printing
        errors as needed, etc.

        Loop will terminate if one of the following occurs:
        1. User hits Enter without entering any text
        2. Server reports a fatal error

        After termination, the server will be signalled that the session is
        over.

        Returns:
            int: exit code for the terminal
        """

        self._print_separator()
        retcode = 0
        # Get initial alien message.
        if not self._fetch_and_print_alien_msg():
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
                user_msg_result = self.stub.ProcessUserMessage(
                    ProcessUserMessageRequest(session_id=self.session,
                                              user_message=user_msg))
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
                if not self._fetch_and_print_alien_msg():
                    retcode = 1
                    break
            self.stub.EndChat(EndChatRequest(session_id=self.session))

        self._print_separator()
        return retcode


def main(port: str) -> int:
    """
    Main client program execution on given port number.

    Will instantiate and manage TerminalSpaceBotClient instance.

    Args:
        port (str): the server port to connect to

    Returns:
        int: exit code for the terminal
    """

    client = TerminalSpaceBotClient(f'{DEFAULT_SERVER}:{port}')
    client.initialize()
    if client.valid:
        retcode = client.run()
    else:
        retcode = 1

    return retcode


if __name__ == "__main__":
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        port = sys.argv[1]

    sys.exit(main(port))
