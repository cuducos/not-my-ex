from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from cryptography.fernet import InvalidToken
from pytest import fixture, raises

from not_my_ex.auth import Auth
from not_my_ex.settings import DEFAULT_BLUESKY_AGENT, DEFAULT_MASTODON_INSTANCE

PASSWORD = "forty2"
BSKY_EMAIL = "email"
BSKY_PASSWORD = "password"
BSKY_AGENT = "agent"
MSTDN_TOKEN = "token"
MSTDN_INSTANCE = "instance"


@fixture(autouse=True)
def user_cache_dir():
    with TemporaryDirectory() as tmp:
        path = Path(tmp)
        app_cache = str(path / "not-my-ex")
        with patch("not_my_ex.auth.user_cache_dir", return_value=app_cache):
            yield


def test_assert_auth_with_right_password():
    auth = Auth(PASSWORD)
    assert not auth.path.exists()
    assert not auth.data.bluesky
    assert not auth.data.mastodon

    auth.save_bluesky_auth(BSKY_EMAIL, BSKY_PASSWORD)
    assert auth.path.exists()
    assert auth.data.bluesky.email == BSKY_EMAIL
    assert auth.data.bluesky.password == BSKY_PASSWORD
    assert auth.data.bluesky.agent == DEFAULT_BLUESKY_AGENT
    assert not auth.data.mastodon

    auth.save_mastodon_auth(MSTDN_TOKEN)
    assert auth.path.exists()
    assert auth.data.mastodon.token == MSTDN_TOKEN
    assert auth.data.mastodon.instance == DEFAULT_MASTODON_INSTANCE

    # and let's make sure the first write still persisted
    assert auth.data.bluesky.email == BSKY_EMAIL
    assert auth.data.bluesky.password == BSKY_PASSWORD
    assert auth.data.bluesky.agent == DEFAULT_BLUESKY_AGENT


def test_assert_auth_with_right_password_and_custom_instances():
    auth = Auth(PASSWORD)
    auth.save_bluesky_auth(BSKY_EMAIL, BSKY_PASSWORD, BSKY_AGENT)
    auth.save_mastodon_auth(MSTDN_TOKEN, MSTDN_INSTANCE)
    assert auth.data.bluesky.agent == BSKY_AGENT
    assert auth.data.mastodon.instance == MSTDN_INSTANCE


def test_assert_auth_wrong_password_attempt():
    auth = Auth(PASSWORD)
    auth.save_bluesky_auth(BSKY_EMAIL, BSKY_PASSWORD, BSKY_AGENT)
    auth.save_mastodon_auth(MSTDN_TOKEN, MSTDN_INSTANCE)

    with raises(InvalidToken):
        Auth("admin")
