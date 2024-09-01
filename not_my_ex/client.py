from abc import ABC, abstractmethod
from typing import Union

from httpx import Response

from not_my_ex.media import Media
from not_my_ex.post import Post


class ClientError(Exception):
    pass


class Client(ABC):
    def __init__(self, client) -> None:
        self.client = client

    @property
    def name(self):
        return self.__class__.__name__.split(".")[-1]

    @property
    def emoji(self):
        if self.name == "Bluesky":
            return "🦋"
        if self.name == "Mastodon":
            return "🐘"

    def raise_from(self, response: Response) -> None:
        data = response.json()
        if "message" in data:
            details = f"{data['error']}: {data['message']}"
        else:
            details = data["error"]
        msg = (
            f"Error from {self.name} server - {response.url} "
            f"HTTP Status {response.status_code} - {details}"
        )
        raise ClientError(msg)

    @abstractmethod
    async def upload(self, media: Media) -> Union[str, dict]:
        pass

    @abstractmethod
    async def post(self, post: Post) -> str:
        pass
