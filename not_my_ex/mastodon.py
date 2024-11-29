from asyncio import gather
from io import BytesIO

from backoff import expo, on_exception
from httpx import AsyncClient, Response

from not_my_ex.auth import MastodonAuth
from not_my_ex.client import Client
from not_my_ex.media import Media
from not_my_ex.post import Post


class MediaNotReadyError(Exception):
    pass


class MastodonCredentialsNotFoundError(Exception):
    pass


class Mastodon(Client):
    def __init__(self, client: AsyncClient, auth: MastodonAuth) -> None:
        self.instance = auth.instance
        self.headers = {"Authorization": f"Bearer {auth.token}"}
        super().__init__(client)

    async def request(self, path: str, **kwargs) -> Response:
        return await self.client.post(
            f"{self.instance}{path}", headers=self.headers, **kwargs
        )

    @on_exception(expo, MediaNotReadyError, max_tries=42)
    async def wait_media_processing(self, media_id) -> None:
        resp = await self.client.get(
            f"{self.instance}/api/v1/media/{media_id}",
            headers=self.headers,
        )
        if resp.status_code != 200:
            raise MediaNotReadyError(resp)

    async def upload(self, media: Media) -> str:
        data = {"description": media.alt} if media.alt else None
        ext = media.mime.split("/")[1]

        with BytesIO(media.content) as attachment:
            files = {"file": (f"image.{ext}", attachment, media.mime)}
            resp = await self.request("/api/v2/media", data=data, files=files)

        if resp.status_code not in (202, 200):
            self.raise_from(resp)

        data = resp.json() or {}
        media_id = str(data["id"])
        if resp.status_code == 202:
            await self.wait_media_processing(media_id)

        return media_id

    async def post(self, post: Post) -> str:
        data = {"status": post.text, "language": post.lang}
        if post.media:
            uploads = tuple(self.upload(media) for media in post.media)
            data["media_ids"] = await gather(*uploads)  # type: ignore

        resp = await self.request("/api/v1/statuses", json=data)
        if resp.status_code != 200:
            self.raise_from(resp)

        data = resp.json()
        return str(data["url"])
