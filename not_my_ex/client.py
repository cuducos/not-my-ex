from abc import ABC, abstractmethod
from typing import Union

from httpx import Response

from not_my_ex.posts import Media, Post


class ClientError(Exception):
    pass


class Client(ABC):
    def __init__(self, client) -> None:
        self.client = client

    @property
    def name(self):
        return self.__class__.__name__.split(".")[-1]

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
    async def auth(self) -> None:
        pass

    @abstractmethod
    async def upload(self, media: Media) -> Union[str, dict]:
        pass

    @abstractmethod
    async def post(self, post: Post) -> str:
        pass

    @classmethod
    async def authenticated(cls, http_client) -> "Client":
        client = cls(http_client)
        await client.auth()
        return client
