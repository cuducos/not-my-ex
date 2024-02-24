from asyncio import gather
from datetime import datetime
from re import compile

from backoff import expo, on_exception
from httpx import AsyncClient, ReadTimeout, Response
from pytz import UTC

from not_my_ex import settings
from not_my_ex.client import Client
from not_my_ex.media import Media
from not_my_ex.post import Post

URL = compile(
    r"(http(s?):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-]))"
)


class BlueskyCredentialsNotFoundError(Exception):
    pass


class Bluesky(Client):
    def __init__(self, client: AsyncClient) -> None:
        if settings.BLUESKY not in settings.CLIENTS_AVAILABLE:
            raise BlueskyCredentialsNotFoundError(
                "NOT_MY_EX_BSKY_EMAIL and/or NOT_MY_EX_BSKY_PASSWORD "
                "environment variables not set"
            )

        self.credentials = {
            "identifier": settings.BSKY_EMAIL,
            "password": settings.BSKY_PASSWORD,
        }
        self.token, self.did, self.handle = None, None, None
        self.is_authenticated = False
        super().__init__(client)

    async def auth(self) -> None:
        resp = await self.client.post(
            f"{settings.BSKY_AGENT}/xrpc/com.atproto.server.createSession",
            json=self.credentials,
        )
        if resp.status_code != 200:
            self.raise_from(resp)

        data = resp.json()
        self.token, self.did, self.handle = (
            data["accessJwt"],
            data["did"],
            data["handle"],
        )
        self.is_authenticated = True

    @on_exception(expo, ReadTimeout, max_tries=7)
    async def xrpc(self, resource: str, **kwargs) -> Response:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"
        url = f"{settings.BSKY_AGENT}/xrpc/{resource}"
        return await self.client.post(url, headers=headers, **kwargs)

    async def upload(self, media: Media) -> dict:
        if not self.is_authenticated:
            await self.auth()

        resp = await self.xrpc(
            "com.atproto.repo.uploadBlob",
            headers={"Content-type": media.mime},
            data=media.content,
        )
        if resp.status_code != 200:
            self.raise_from(resp)

        data = resp.json()
        return {"alt": media.alt, "image": data["blob"]}

    async def data(self, post):
        if not self.is_authenticated:
            await self.auth()

        created_at = datetime.utcnow().replace(microsecond=0, tzinfo=UTC).isoformat()
        data = {
            "repo": self.did,
            "collection": "app.bsky.feed.post",
            "record": {
                "$type": "app.bsky.feed.post",
                "text": post.text,
                "createdAt": created_at,
                "langs": [post.lang],
            },
        }

        if matches := URL.findall(post.text):
            data["record"]["facets"] = []
            start = 0
            source = post.text.encode()
            for url, *_ in matches:
                target = url.encode()
                start = source.find(target, start)
                end = start + len(target)
                data["record"]["facets"].append(
                    {
                        "index": {"byteStart": start, "byteEnd": end},
                        "features": [
                            {
                                "$type": "app.bsky.richtext.facet#link",
                                "uri": url,
                            }
                        ],
                    }
                )
                start = end

        if post.media:
            uploads = tuple(self.upload(media) for media in post.media)
            embed = await gather(*uploads)
            data["record"]["embed"] = {
                "$type": "app.bsky.embed.images",
                "images": embed,
            }

        return data

    async def url_from(self, resp: Response) -> str:
        data = resp.json()
        *_, post_id = data["uri"].split("/")
        return f"https://bsky.app/profile/{self.handle}/post/{post_id}"

    async def post(self, post: Post) -> str:
        if not self.is_authenticated:
            await self.auth()

        data = await self.data(post)
        resp = await self.xrpc("com.atproto.repo.createRecord", json=data)
        if resp.status_code != 200:
            self.raise_from(resp)

        return await self.url_from(resp)
