import asyncio
import sys

from machine_learning.spacebot.server import InMemorySpaceBotServer
from machine_learning.spacebot.client import TerminalSpaceBotClient


# TODO: use separate threads for client and server (and support multiple clients)
# TODO: use gRPC instead of direct calls so that typescript client could be plugged in seamleslessly

# TODO: put common stuff for future chatbots into common library

# TODO: docstrings
# TODO: type hint cleanup
# TODO: tests (cheese historian failure case)(Really? failure case)
# TODO: lint errors
# TODO: README

# TODO: contribute some evals to get GPT 4 access and see if that fixes the prompt injection issues
# (https://github.com/openai/evals)

# TODO: consider getting multiple choices for prompt and using those (instead of re-fetch)
# TODO: consider making an enum for role in messages
# TODO: consider making message a proto for py and ts to share

# TODO: start a real bug/task list in GitHub for anything not done on check-in
async def main() -> int:
    server = InMemorySpaceBotServer()
    client = TerminalSpaceBotClient(server)

    await client.initialize()
    if client.valid:
        retcode = await client.run()
    else:
        retcode = 1

    return retcode


if __name__ == '__main__':
    retcode = asyncio.run(main())

    sys.exit(retcode)
