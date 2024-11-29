from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from cryptography.fernet import InvalidToken
from pytest import fixture, raises

from not_my_ex.auth import EncryptedAuth
from not_my_ex.settings import DEFAULT_BLUESKY_AGENT, DEFAULT_MASTODON_INSTANCE

PASSWORD = "forty2"
BSKY_EMAIL = "email"
BSKY_PASSWORD = "password"
BSKY_AGENT = "agent"
MSTDN_TOKEN = "token"
MSTDN_INSTANCE = "instance"
LANG = "pt"


@fixture(autouse=True)
def user_cache_dir():
    with TemporaryDirectory() as tmp:
        path = Path(tmp)
        app_cache = str(path / "not-my-ex")
        with patch("not_my_ex.auth.user_cache_dir", return_value=app_cache):
            yield


def test_assert_auth_with_right_password():
    auth = EncryptedAuth(PASSWORD)
    assert not auth.path.exists()
    assert not auth.bluesky
    assert not auth.mastodon

    auth.save_language(LANG)
    assert auth.path.exists()
    assert auth.language == LANG
    assert not auth.bluesky
    assert not auth.mastodon

    auth.save_bluesky(BSKY_EMAIL, BSKY_PASSWORD)
    assert auth.language == LANG
    assert auth.bluesky.email == BSKY_EMAIL
    assert auth.bluesky.password == BSKY_PASSWORD
    assert auth.bluesky.agent == DEFAULT_BLUESKY_AGENT
    assert not auth.mastodon

    auth.save_mastodon(MSTDN_TOKEN)
    assert auth.language == LANG
    assert auth.bluesky.email == BSKY_EMAIL
    assert auth.bluesky.password == BSKY_PASSWORD
    assert auth.bluesky.agent == DEFAULT_BLUESKY_AGENT
    assert auth.mastodon.token == MSTDN_TOKEN
    assert auth.mastodon.instance == DEFAULT_MASTODON_INSTANCE


def test_assert_auth_with_right_password_and_custom_instances():
    auth = EncryptedAuth(PASSWORD)
    auth.save_bluesky(BSKY_EMAIL, BSKY_PASSWORD, BSKY_AGENT)
    auth.save_mastodon(MSTDN_TOKEN, MSTDN_INSTANCE)
    assert auth.bluesky.agent == BSKY_AGENT
    assert auth.mastodon.instance == MSTDN_INSTANCE


def test_assert_auth_wrong_password_attempt():
    auth = EncryptedAuth(PASSWORD)
    auth.save_bluesky(BSKY_EMAIL, BSKY_PASSWORD, BSKY_AGENT)
    auth.save_mastodon(MSTDN_TOKEN, MSTDN_INSTANCE)

    with raises(InvalidToken):
        EncryptedAuth("admin")
