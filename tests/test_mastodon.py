from unittest.mock import ANY, AsyncMock, Mock, patch

from pytest import mark, raises

from not_my_ex.client import ClientError
from not_my_ex.mastodon import Mastodon
from not_my_ex.media import Media
from not_my_ex.post import Post


@mark.asyncio
async def test_mastodon_client_post_raises_error_from_server(auth):
    client, response = AsyncMock(), Mock()
    response.status_code = 401
    response.json.return_value = {"error": "oops"}
    client.post.return_value = response
    post = Post("Hello")
    with raises(ClientError):
        await Mastodon(client, auth.mastodon).post(post)


@mark.asyncio
async def test_mastodon_client_post(auth):
    client, response = AsyncMock(), Mock()
    response.status_code = 200
    response.json.return_value = {"url": "https://tech.lgbt/@cuducos/42"}
    client.post.return_value = response
    mastodon = Mastodon(client, auth.mastodon)
    post = Post("Hello world, the answer is 42")

    assert await mastodon.post(post) == "https://tech.lgbt/@cuducos/42"
    client.post.assert_called_once_with(
        f"{auth.mastodon.instance}/api/v1/statuses",
        headers={"Authorization": "Bearer 40two"},
        json={"status": "Hello world, the answer is 42", "language": "en"},
    )


@mark.asyncio
async def test_mastodon_client_upload(auth):
    client, response = AsyncMock(), Mock()
    response.status_code = 200
    response.json.return_value = {"id": 42}
    client.post.return_value = response
    mastodon = Mastodon(client, auth.mastodon)
    media = Media("/tmp/42.png", b"42", "image/png", "desc")

    resp = await mastodon.upload(media)
    assert resp == "42"
    client.post.assert_called_once_with(
        f"{auth.mastodon.instance}/api/v2/media",
        headers={"Authorization": "Bearer 40two"},
        data={"description": "desc"},
        files={"file": ("image.png", ANY, "image/png")},
    )


@mark.asyncio
async def test_mastodon_client_upload_with_post_processing(auth):
    client, response = AsyncMock(), Mock()
    response.status_code = 202
    response.json.return_value = {"id": 42}
    processing, ok = Mock(), Mock()
    processing.status_code = 206
    ok.status_code = 200
    client.post.return_value = response
    client.get.side_effect = (processing, ok)
    mastodon = Mastodon(client, auth.mastodon)
    media = Media("/tmp/42.png", b"42", "image/png", "desc")
    assert await mastodon.upload(media) == "42"
    assert 2 == client.get.call_count


@mark.asyncio
async def test_mastodon_client_post_with_media(auth):
    with patch.object(Mastodon, "upload", new_callable=AsyncMock) as upload:
        upload.return_value = 42
        client, response = AsyncMock(), Mock()
        response.status_code = 200
        response.json.return_value = {"url": "https://tech.lgbt/@cuducos/42"}
        client.post.return_value = response
        mastodon = Mastodon(client, auth.mastodon)
        post = Post(
            "Hello world, the answer is 42",
            media=(Media("/tmp/42.png", b"42", "image/png", "my alt text"),),
        )

        assert await mastodon.post(post) == "https://tech.lgbt/@cuducos/42"
        client.post.assert_called_once_with(
            f"{auth.mastodon.instance}/api/v1/statuses",
            headers={"Authorization": "Bearer 40two"},
            json={
                "status": "Hello world, the answer is 42",
                "language": "en",
                "media_ids": [42],
            },
        )
