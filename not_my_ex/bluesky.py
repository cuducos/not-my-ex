from asyncio import gather
from datetime import datetime, timezone
from re import compile
from string import punctuation

from backoff import expo, on_exception
from httpx import AsyncClient, ReadTimeout, Response

from not_my_ex.auth import BlueskyAuth
from not_my_ex.card import Card
from not_my_ex.client import Client
from not_my_ex.media import Media
from not_my_ex.post import Post

PUNCTUATION = set(punctuation)
HASHTAG = compile(r"#\S+")
URL = compile(
    r"(http(s?):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-]))"
)


class BlueskyCredentialsNotFoundError(Exception):
    pass


class Bluesky(Client):
    def __init__(self, client: AsyncClient, auth: BlueskyAuth) -> None:
        self.agent = auth.agent
        self.credentials = {"identifier": auth.email, "password": auth.password}
        self.token, self.did, self.handle = None, None, None
        self.is_authenticated = False
        super().__init__(client)

    async def auth(self) -> None:
        resp = await self.client.post(
            f"{self.agent}/xrpc/com.atproto.server.createSession",
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
        url = f"{self.agent}/xrpc/{resource}"
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
        return {"alt": media.alt or "", "image": data["blob"]}

    async def data(self, post):
        if not self.is_authenticated:
            await self.auth()

        created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
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

        first_link = None
        if matches := URL.findall(post.text):
            data["record"]["facets"] = data["record"].get("facets", [])
            start = 0
            source = post.text.encode()
            for url, *_ in matches:
                if not first_link:
                    first_link = url

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

        url_intervals = tuple(
            (url["index"]["byteStart"], url["index"]["byteEnd"])
            for url in data["record"].get("facets", [])
        )

        def is_inside_url(pos):
            for start, end in url_intervals:
                if start < pos < end:
                    return True
            return False

        if matches := HASHTAG.findall(post.text):
            data["record"]["facets"] = data["record"].get("facets", [])
            start = 0
            source = post.text.encode()
            for hashtag in matches:
                if hashtag.removeprefix("#").isdigit():
                    continue
                while hashtag[-1:] in PUNCTUATION:
                    hashtag = hashtag[:-1]
                if len(hashtag) < 2:
                    continue
                target = hashtag.encode()
                start = source.find(target, start)
                if is_inside_url(start):
                    continue
                end = start + len(target)
                data["record"]["facets"].append(
                    {
                        "index": {"byteStart": start, "byteEnd": end},
                        "features": [
                            {
                                "$type": "app.bsky.richtext.facet#tag",
                                "tag": hashtag.removeprefix("#"),
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
        elif first_link:
            card = await Card.from_url(first_link)
            if card:
                embed = {
                    "$type": "app.bsky.embed.external",
                    "external": {
                        "uri": card.uri,
                        "title": card.title,
                    },
                }
                if card.description:
                    embed["external"]["description"] = card.description
                if card.media:
                    uploaded = await self.upload(card.media)
                    embed["external"]["thumb"] = uploaded["image"]
                data["record"]["embed"] = embed

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
