from io import BytesIO

from backoff import expo, on_exception
from httpx import get, post

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
    def __init__(self):
        if settings.MASTODON not in settings.CLIENTS_AVAILABLE:
            raise MastodonCredentialsNotFoundError(
                "NOT_MY_EX_MASTODON_TOKEN environment variables not set"
            )
        self.headers = {"Authorization": f"Bearer {settings.MASTODON_TOKEN}"}

    def req(self, path, **kwargs):
        return post(
            f"{settings.MASTODON_INSTANCE}{path}", headers=self.headers, **kwargs
        )

    @on_exception(expo, MediaNotReadyError, max_tries=422)
    def wait_media_processing(self, media_id):
        resp = get(
            f"{settings.MASTODON_INSTANCE}/api/v1/media/{media_id}",
            headers=self.headers,
        )
        if resp.status_code != 200:
            raise MediaNotReadyError(resp)

    def upload(self, media):
        data = {"description": media.alt} if media.alt else None
        ext = media.mime.split("/")[1]

        with BytesIO(media.content) as attachment:
            files = {"file": (f"image.{ext}", attachment, media.mime)}
            resp = self.req("/api/v2/media", data=data, files=files)

        if resp.status_code not in (202, 200):
            raise MastodonError(resp)

        media_id = resp.json()["id"]
        if resp.status_code == 202:
            self.wait_media_processing(media_id)

        return media_id

    def post(self, status):
        data = {"status": status.text, "language": status.lang}
        if status.media:
            data["media_ids"] = [self.upload(media) for media in status.media]

        resp = self.req("/api/v1/statuses", json=data)
        if resp.status_code != 200:
            raise MastodonError(resp)

        return resp.json()["url"]
