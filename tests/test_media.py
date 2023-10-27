from not_my_ex.posts import Media


def test_media_from_img(image):
    path, content = image
    alt = "fourty-two"
    media = Media.from_img(path, alt=alt)
    assert content == media.content
    assert alt == media.alt
    assert "image/png" == media.mime
