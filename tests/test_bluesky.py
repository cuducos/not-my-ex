from unittest.mock import ANY, AsyncMock, Mock

from pytest import mark, raises

from not_my_ex.bluesky import Bluesky
from not_my_ex.client import ClientError
from not_my_ex.media import Media
from not_my_ex.post import Post


@mark.asyncio
async def test_bluesky_client_uses_the_correct_credentials(auth):
    client, response = AsyncMock(), Mock()
    response.status_code = 200
    response.json.return_value = {
        "accessJwt": "a very long string",
        "did": "42",
        "handle": "cuducos",
    }
    client.post.return_value = response
    await Bluesky(client, auth.bluesky).auth()
    client.post.assert_called_once_with(
        f"{auth.bluesky.agent}/xrpc/com.atproto.server.createSession",
        json={"identifier": auth.bluesky.email, "password": auth.bluesky.password},
    )


@mark.asyncio
async def test_bluesky_client_raises_error_for_invalid_credentials(auth):
    client, response = AsyncMock(), Mock()
    response.status_code = 401
    response.json.return_value = {"error": "SomeError", "message": "Oops"}
    client.post.return_value = response
    with raises(ClientError, match="SomeError: Oops"):
        await Bluesky(client, auth.bluesky).auth()


@mark.asyncio
async def test_bluesky_client_gets_a_jwt_token_and_did(auth):
    client, response = AsyncMock(), Mock()
    response.status_code = 200
    response.json.return_value = {
        "accessJwt": "a very long string",
        "did": "42",
        "handle": "cuducos",
    }
    client.post.return_value = response
    bluesky = Bluesky(client, auth.bluesky)
    await bluesky.auth()
    assert bluesky.token == "a very long string"
    assert bluesky.did == "42"
    assert bluesky.handle == "cuducos"


@mark.asyncio
async def test_bluesky_client_post_data(auth):
    client, response = AsyncMock(), Mock()
    client.post.return_value = response
    bluesky = Bluesky(client, auth.bluesky)
    bluesky.is_authenticated = True
    bluesky.did = "42"
    data = await bluesky.data(Post("hello world, the answer is 42"))
    assert data == {
        "repo": "42",
        "collection": "app.bsky.feed.post",
        "record": {
            "$type": "app.bsky.feed.post",
            "text": "hello world, the answer is 42",
            "createdAt": ANY,
            "langs": ["en"],
        },
    }


@mark.asyncio
async def test_bluesky_client_post(auth):
    client, response = AsyncMock(), Mock()
    response.status_code = 200
    response.json.return_value = {
        "uri": "at://did:plc:42/app.bsky.feed.post/fOrTy2",
        "cid": "meh",
    }
    client.post.return_value = response
    bluesky = Bluesky(client, auth.bluesky)
    bluesky.is_authenticated = True
    bluesky.token = "forty-two"
    bluesky.did = "42"
    bluesky.handle = "cuducos"
    post = Post("Hello")
    assert await bluesky.post(post) == "https://bsky.app/profile/cuducos/post/fOrTy2"


@mark.asyncio
async def test_bluesky_client_post_raises_error_from_server(auth):
    client, response = AsyncMock(), Mock()
    response.status_code = 501
    response.json.return_value = {
        "error": "SomeError",
        "message": "Oops",
    }
    client.post.return_value = response
    bluesky = Bluesky(client, auth.bluesky)
    bluesky.is_authenticated = True
    post = Post("Hello")
    with raises(ClientError):
        await bluesky.post(post)


@mark.asyncio
async def test_bluesky_client_post_data_includes_urls_in_facets(auth):
    client = AsyncMock()
    bluesky = Bluesky(client, auth.bluesky)
    bluesky.is_authenticated = True
    text = "✨ example mentioning @atproto.com to share the URL 👨‍❤️‍👨 https://en.wikipedia.org/wiki/CBOR."
    data = await bluesky.data(Post(text))
    assert data["record"]["facets"] == [
        {
            "index": {"byteStart": 74, "byteEnd": 108},
            "features": [
                {
                    "$type": "app.bsky.richtext.facet#link",
                    "uri": "https://en.wikipedia.org/wiki/CBOR",
                }
            ],
        }
    ]


@mark.asyncio
async def test_bluesky_client_post_data_includes_urls_and_hashtag_in_facets(auth):
    client = AsyncMock()
    bluesky = Bluesky(client, auth.bluesky)
    bluesky.is_authenticated = True
    text = "✨ example mentioning @atproto.com to #share the URL 👨‍❤️‍👨 https://en.wikipedia.org/wiki/CBOR#42."
    data = await bluesky.data(Post(text))
    assert data["record"]["facets"] == [
        {
            "features": [
                {
                    "$type": "app.bsky.richtext.facet#link",
                    "uri": "https://en.wikipedia.org/wiki/CBOR#42",
                },
            ],
            "index": {
                "byteEnd": 112,
                "byteStart": 75,
            },
        },
        {
            "features": [
                {
                    "$type": "app.bsky.richtext.facet#tag",
                    "tag": "share",
                },
            ],
            "index": {
                "byteEnd": 45,
                "byteStart": 39,
            },
        },
    ]


@mark.asyncio
async def test_bluesky_client_post_data_includes_images_blobs(auth):
    client, response = AsyncMock(), Mock()
    response.status_code = 200
    response.json.return_value = {"blob": "42"}
    client.post.return_value = response
    bluesky = Bluesky(client, auth.bluesky)
    bluesky.is_authenticated = True
    bluesky.token = "token"
    bluesky.did = "did"
    media = Media("/tmp/42.png", b"42", "image/png", "my alt text")
    post = Post("hi", media=(media,))
    data = await bluesky.data(post)
    client.post.assert_any_call(
        f"{auth.bluesky.agent}/xrpc/com.atproto.repo.uploadBlob",
        headers={
            "Authorization": "Bearer token",
            "Content-type": "image/png",
        },
        data=b"42",
    )
    assert data["record"]["embed"] == {
        "$type": "app.bsky.embed.images",
        "images": [{"alt": "my alt text", "image": "42"}],
    }
