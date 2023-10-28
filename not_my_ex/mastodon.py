from asyncio import gather
from io import BytesIO

from backoff import expo, on_exception

from not_my_ex import settings


class MediaNotReadyError(Exception):
    pass


class MastodonCredentialsNotFoundError(Exception):
    pass


class MastodonError(Exception):
    def __init__(self, response, *args, **kwargs):
        data = response.json()
        msg = (
            f"Error from Mastodon instance server - "
            f"[HTTP Status {response.status_code}] {data['error']}"
        )
        super().__init__(msg, *args, **kwargs)


class Mastodon:
    def __init__(self, client):
        if settings.MASTODON not in settings.CLIENTS_AVAILABLE:
            raise MastodonCredentialsNotFoundError(
                "NOT_MY_EX_MASTODON_TOKEN environment variables not set"
            )
        self.client = client
        self.headers = {"Authorization": f"Bearer {settings.MASTODON_TOKEN}"}

    async def auth(self):
        return

    async def req(self, path, **kwargs):
        return await self.client.post(
            f"{settings.MASTODON_INSTANCE}{path}", headers=self.headers, **kwargs
        )

    @on_exception(expo, MediaNotReadyError, max_tries=42)
    async def wait_media_processing(self, media_id):
        resp = await self.client.get(
            f"{settings.MASTODON_INSTANCE}/api/v1/media/{media_id}",
            headers=self.headers,
        )
        if resp.status_code != 200:
            raise MediaNotReadyError(resp)

    async def upload(self, media):
        data = {"description": media.alt} if media.alt else None
        ext = media.mime.split("/")[1]

        with BytesIO(media.content) as attachment:
            files = {"file": (f"image.{ext}", attachment, media.mime)}
            resp = await self.req("/api/v2/media", data=data, files=files)

        if resp.status_code not in (202, 200):
            raise MastodonError(resp)

        data = resp.json()
        media_id = data["id"]
        if resp.status_code == 202:
            await self.wait_media_processing(media_id)

        return media_id

    async def post(self, status):
        data = {"status": status.text, "language": status.lang}
        if status.media:
            uploads = tuple(self.upload(media) for media in status.media)
            data["media_ids"] = await gather(*uploads)

        resp = await self.req("/api/v1/statuses", json=data)
        if resp.status_code != 200:
            raise MastodonError(resp)

        data = resp.json()
        return data["url"]
