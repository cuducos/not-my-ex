from base64 import urlsafe_b64encode
from dataclasses import dataclass
from os import getenv, urandom
from pathlib import Path
from pickle import dumps, loads
from typing import Optional, Union

from appdirs import user_cache_dir
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.hashes import SHA512
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from not_my_ex import settings

SALT_SIZE = 42


def cache():
    return Path(user_cache_dir("not-my-ex")) / "auth"


@dataclass
class BlueskyAuth:
    agent: str
    email: str
    password: str


@dataclass
class MastodonAuth:
    instance: str
    token: str


@dataclass
class AuthData:
    bluesky: Optional[BlueskyAuth] = None
    mastodon: Optional[MastodonAuth] = None
    language: Optional[str] = None


class EnvironmentVariableNotFoundError(Exception): ...


class Auth:
    def __init__(self):
        self.data = AuthData()

    def for_client(self, key):
        if key == settings.BLUESKY:
            return self.bluesky
        if key == settings.MASTODON:
            return self.mastodon
        raise ValueError("Invalid client")

    def invalidate(self, key):
        if key == settings.BLUESKY:
            self.data.bluesky = None
        if key == settings.MASTODON:
            self.data.mastodon = None

    @property
    def bluesky(self) -> Optional[BlueskyAuth]:
        return self.data.bluesky

    @property
    def mastodon(self) -> Optional[MastodonAuth]:
        return self.data.mastodon

    @property
    def language(self) -> Optional[str]:
        return self.data.language

    @property
    def clients(self):
        clients = (
            (settings.BLUESKY, self.bluesky is not None),
            (settings.MASTODON, self.mastodon is not None),
        )
        return tuple(key for key, configured in clients if configured)

    def assure_configured(self):
        if not self.clients:
            raise EnvironmentVariableNotFoundError(
                "No clients available. Please set at least one of the following "
                "environment variables (or run `not-my-ex config`):\n"
                "- NOT_MY_EX_BSKY_EMAIL and NOT_MY_EX_BSKY_PASSWORD"
                "- NOT_MY_EX_MASTODON_TOKEN"
            )

    @property
    def limit(self):
        if self.bluesky:
            return 300
        return 1024

    @property
    def image_size_limit(self):
        if self.bluesky:
            return 1024 * 1024


class FernetWithPassword(Fernet):
    def __init__(self, password: bytes, salt: bytes) -> None:
        kdf = PBKDF2HMAC(algorithm=SHA512(), length=32, salt=salt, iterations=2**19)
        key = urlsafe_b64encode(kdf.derive(password))
        super().__init__(key)


class EncryptedAuth(Auth):
    """This class manages authentication information (API tokens, logins, etc.) stored
    locally in an encrypted password-protected file."""

    def __init__(self, password: str) -> None:
        self.path = cache()
        if self.path.exists():
            with self.path.open("rb") as cursor:
                self.salt = cursor.read(SALT_SIZE)
                encrypted = cursor.read()
            self.algorithm = FernetWithPassword(password.encode("utf-8"), self.salt)
            self.data = loads(self.algorithm.decrypt(encrypted))
        else:
            self.salt = urandom(SALT_SIZE)
            self.algorithm = FernetWithPassword(password.encode("utf-8"), self.salt)
            self.data = AuthData()

    def persist(self, data: Union[BlueskyAuth, MastodonAuth, str]) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(exist_ok=True)

        if isinstance(data, BlueskyAuth):
            self.data.bluesky = data
        if isinstance(data, MastodonAuth):
            self.data.mastodon = data
        if isinstance(data, str):
            self.data.language = data

        with self.path.open("wb") as cursor:
            cursor.write(self.salt)
            cursor.write(self.algorithm.encrypt(dumps(self.data)))

    def save_bluesky(
        self, email: str, password: str, agent: Optional[str] = None
    ) -> None:
        assert email, "Email cannot be empty"
        assert password, "Password cannot be empty"
        self.persist(
            BlueskyAuth(
                agent or settings.DEFAULT_BLUESKY_AGENT,
                email,
                password,
            )
        )

    def save_mastodon(self, token: str, instance: Optional[str] = None) -> None:
        assert token, "Token cannot be empty"
        self.persist(
            MastodonAuth(
                instance or settings.DEFAULT_MASTODON_INSTANCE,
                token,
            )
        )

    def save_language(self, language: str) -> None:
        self.persist(language)


class EnvAuth(Auth):
    """This class offers the same `Auth` API but loading credentials from environment
    variables instead."""

    def __init__(self) -> None:
        self.data = AuthData()
        self.data.language = getenv("NOT_MY_EX_DEFAULT_LANG")

        bluesky_agent = getenv("NOT_MY_EX_BSKY_AGENT", settings.DEFAULT_BLUESKY_AGENT)
        bluesky_email = getenv("NOT_MY_EX_BSKY_EMAIL", "")
        bluesky_password = getenv("NOT_MY_EX_BSKY_PASSWORD", "")
        if all((bluesky_agent, bluesky_email, bluesky_password)):
            self.data.bluesky = BlueskyAuth(
                bluesky_agent, bluesky_email, bluesky_password
            )

        mastodon_token = getenv("NOT_MY_EX_MASTODON_TOKEN", "")
        mastodon_instance = getenv(
            "NOT_MY_EX_MASTODON_INSTANCE", settings.DEFAULT_MASTODON_INSTANCE
        )
        if all((mastodon_instance, mastodon_token)):
            self.data.mastodon = MastodonAuth(mastodon_instance, mastodon_token)


def authenticate(password: Optional[str] = None) -> Auth:
    if password and cache().exists():
        return EncryptedAuth(password)
    return EnvAuth()
