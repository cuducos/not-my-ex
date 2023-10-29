from unittest.mock import patch

from pytest import mark, raises

from not_my_ex.media import Media
from not_my_ex.post import Post, PostTooLongError


def test_post():
    post = Post("forty-two")
    assert "forty-two" == post.text
    assert post.media is None
    assert "en" == post.lang


@mark.asyncio
async def test_post_with_media(image):
    img, *_ = image
    media = await Media.from_img(img)
    post = Post("forty-two", media=(media,))
    assert 1 == len(post.media)


def test_post_raises_error_when_too_long():
    with raises(PostTooLongError):
        Post("forty-two" * 42)


@mark.parametrize("answer", ("y", "Y"))
def test_post_check_right_language(answer):
    with patch("not_my_ex.post.input") as mock:
        mock.return_value = answer
        post = Post("Here comes a beautiful post")

        with patch("not_my_ex.post.Language") as lang:
            post.check_language()
            lang.assert_not_called()


@mark.parametrize("answer", ("", " ", "N", "xpto"))
def test_post_check_wrong_language(answer):
    with patch("not_my_ex.post.input") as mock:
        mock.return_value = answer
        post = Post("Here comes a beautiful post")
        assert "pt" != post.lang

        with patch("not_my_ex.post.Language") as lang:
            lang.return_value.name = "pt"
            post.check_language()

        assert "pt" == post.lang
