import uuid
from abc import ABC, abstractmethod

from machine_learning.spacebot.spacebot_pb2 import SpaceBotResult


class SpaceBotServer(ABC):

    @abstractmethod
    async def create_chat(self, sessionId: uuid.UUID) -> SpaceBotResult:
        pass

    @abstractmethod
    async def end_chat(self, sessionId: uuid.UUID) -> None:
        pass

    @abstractmethod
    async def fetch_alien_msg(self, sessionId: uuid.UUID) -> SpaceBotResult:
        pass

    @abstractmethod
    async def process_user_msg(self, sessionId: uuid.UUID,
                               user_msg: str) -> SpaceBotResult:
        pass


class SpaceBotClient(ABC):

    @abstractmethod
    async def run(self) -> int:
        pass
