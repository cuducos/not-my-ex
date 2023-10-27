from unittest.mock import ANY, Mock, patch

from pytest import raises

from not_my_ex import settings
from not_my_ex.mastodon import Mastodon, MastodonCredentialsNotFoundError, MastodonError
from not_my_ex.posts import Media, Post


def test_mastodon_client_raises_error_when_not_set():
    with patch.object(settings, "CLIENTS_AVAILABLE", new_callable=set):
        with raises(MastodonCredentialsNotFoundError):
            Mastodon()


def test_mastodon_client_post_raises_error_from_server():
    with patch("not_my_ex.mastodon.post") as mock:
        mock.return_value.status_code = 401
        mock.return_value.json.return_value = {"error": "oops"}
        post = Post("Hello")
        with raises(MastodonError):
            Mastodon().post(post)


def test_mastodon_client_post():
    with patch("not_my_ex.mastodon.post") as mock:
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = {"url": "https://tech.lgbt/@cuducos/42"}
        mastodon = Mastodon()
        post = Post("Hello")

        assert mastodon.post(post) == "https://tech.lgbt/@cuducos/42"
        mock.assert_called_once_with(
            f"{settings.MASTODON_INSTANCE}/api/v1/statuses",
            headers={"Authorization": "Bearer 40two"},
            json={"status": post.text},
        )


def test_mastodon_client_upload():
    mastodon = Mastodon()
    media = Media(b"42", "image/png", "desc")

    with patch("not_my_ex.mastodon.post") as mock:
        mock.return_value.status_code = 200
        mock.return_value.json.return_value = {"id": 42}
        resp = mastodon.upload(media)

        assert resp == 42
        mock.assert_called_once_with(
            f"{settings.MASTODON_INSTANCE}/api/v2/media",
            headers={"Authorization": "Bearer 40two"},
            data={"description": "desc"},
            files={"file": ("image.png", ANY, "image/png")},
        )


def test_mastodon_client_upload_with_post_processing():
    mastodon = Mastodon()
    media = Media(b"42", "image/png", "desc")

    with patch("not_my_ex.mastodon.post") as post:
        post.return_value.status_code = 202
        post.return_value.json.return_value = {"id": 42}

        with patch("not_my_ex.mastodon.get") as get:
            processing, ok = Mock(), Mock()
            processing.status_code = 206
            ok.status_code = 200
            get.side_effect = (processing, processing, ok)

            assert mastodon.upload(media) == 42
            assert 3 == get.call_count


def test_mastodon_client_post_with_media():
    with patch.object(Mastodon, "upload") as upload:
        upload.return_value = 42
        with patch("not_my_ex.mastodon.post") as mock:
            mock.return_value.status_code = 200
            mock.return_value.json.return_value = {
                "url": "https://tech.lgbt/@cuducos/42"
            }
            mastodon = Mastodon()
            post = Post("Hello", (Media(b"42", "image/png", "my alt text"),))

            assert mastodon.post(post) == "https://tech.lgbt/@cuducos/42"
            mock.assert_called_once_with(
                f"{settings.MASTODON_INSTANCE}/api/v1/statuses",
                headers={"Authorization": "Bearer 40two"},
                json={"status": post.text, "media_ids": [42]},
            )
