from pytest import raises

from not_my_ex.posts import Media, Post, PostTooLongError


def test_post():
    post = Post("forty-two")
    assert "forty-two" == post.text
    assert post.media is None
    assert "en" == post.lang


def test_post_with_media(image):
    img, *_ = image
    post = Post("forty-two", media=(Media.from_img(img, "one pixel"),))
    assert 1 == len(post.media)


def test_post_raises_error_when_too_long():
    with raises(PostTooLongError):
        Post("forty-two" * 42)
