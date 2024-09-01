from unittest.mock import AsyncMock, patch

from httpx import AsyncClient, HTTPStatusError, Request, Response
from pytest import mark

from not_my_ex.card import Card

MOCK_HTML = """
<html>
<head>
    <meta property="og:title" content="Sample Page Title">
    <meta property="og:url" content="http://example.com/sample-page">
    <meta property="og:description" content="This is a sample description">
    <meta property="og:image" content="http://example.com/sample-image.jpg">
</head>
<body></body>
</html>
"""
MOCK_IMAGE = b"fake_image_bytes"


@mark.asyncio
async def test_card_success():
    with patch.object(
        AsyncClient,
        "get",
        AsyncMock(
            side_effect=[
                Response(200, content=MOCK_HTML.encode("utf-8")),
                Response(200, content=MOCK_IMAGE),
            ]
        ),
    ):
        card = await Card.from_url("http://example.com/sample-page")
        assert card is not None
        assert card.title == "Sample Page Title"
        assert card.uri == "http://example.com/sample-page"
        assert card.description == "This is a sample description"
        assert card.thumb == MOCK_IMAGE
        assert card.mime == "image/jpeg"


@mark.asyncio
async def test_card_failure():
    with patch.object(
        AsyncClient,
        "get",
        AsyncMock(
            side_effect=HTTPStatusError(
                "Error",
                request=Request("GET", "http://example.com/sample-page"),
                response=Response(404),
            )
        ),
    ):
        card = await Card.from_url("http://example.com/sample-page")
        assert card is None
