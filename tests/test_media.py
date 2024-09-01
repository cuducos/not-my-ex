from unittest.mock import patch

from pytest import mark, raises

from not_my_ex.media import Media


@mark.asyncio
async def test_media_from_img(image):
    path, content = image
    media = await Media.from_img(path)
    assert content == media.content
    assert "image/png" == media.mime


@mark.asyncio
async def test_media_from_img_not_found():
    with raises(ValueError):
        await Media.from_img("/tmp/this-file-should-not-exist.png")


@mark.asyncio
async def test_media_from_img_without_mime_type(image):
    path, _ = image
    with patch("not_my_ex.media.mime_for") as guess:
        guess.return_value = None
        with raises(ValueError):
            await Media.from_img(path)


def test_media_check_alt_text_with_existing_alt_text():
    media = Media("path", b"content", "mime", "alt")
    with patch("not_my_ex.media.input") as mock:
        media.check_alt_text()
        mock.assert_not_called()


def test_media_check_alt_text_with_user_input():
    media = Media("path", b"content", "mime")
    with patch("not_my_ex.media.input") as mock:
        mock.return_value = "alt"
        media.check_alt_text()
    assert "alt" == media.alt
