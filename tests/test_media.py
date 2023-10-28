from pytest import mark

from not_my_ex.posts import Media


@mark.asyncio
async def test_media_from_img(image):
    path, content = image
    alt = "fourty-two"
    media = await Media.from_img(path, alt=alt)
    assert content == media.content
    assert alt == media.alt
    assert "image/png" == media.mime
