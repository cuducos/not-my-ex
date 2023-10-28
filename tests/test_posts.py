from pytest import mark, raises

from not_my_ex.posts import Media, Post, PostTooLongError


def test_post():
    post = Post("forty-two")
    assert "forty-two" == post.text
    assert post.media is None
    assert "en" == post.lang


@mark.asyncio
async def test_post_with_media(image):
    img, *_ = image
    media = await Media.from_img(img, "one pixel")
    post = Post("forty-two", media=(media,))
    assert 1 == len(post.media)


def test_post_raises_error_when_too_long():
    with raises(PostTooLongError):
        Post("forty-two" * 42)
