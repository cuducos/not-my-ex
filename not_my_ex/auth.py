from base64 import urlsafe_b64encode
from dataclasses import dataclass
from os import urandom
from pathlib import Path
from pickle import dumps, loads
from typing import Optional, Union

from appdirs import user_cache_dir
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.hashes import SHA512
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from not_my_ex.settings import DEFAULT_BLUESKY_AGENT, DEFAULT_MASTODON_INSTANCE

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


class FernetWithPassword(Fernet):
    def __init__(self, password: bytes, salt: bytes) -> None:
        kdf = PBKDF2HMAC(algorithm=SHA512(), length=32, salt=salt, iterations=2**19)
        key = urlsafe_b64encode(kdf.derive(password))
        super().__init__(key)


class Auth:
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

    @property
    def bluesky(self) -> Optional[BlueskyAuth]:
        return self.data.bluesky

    @property
    def mastodon(self) -> Optional[MastodonAuth]:
        return self.data.mastodon

    @property
    def language(self) -> Optional[str]:
        return self.data.language

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

    def save_bluesky_auth(
        self, email: str, password: str, agent: Optional[str] = None
    ) -> None:
        assert email, "Email cannot be empty"
        assert password, "Password cannot be empty"
        self.persist(BlueskyAuth(agent or DEFAULT_BLUESKY_AGENT, email, password))

    def save_mastodon_auth(self, token: str, instance: Optional[str] = None) -> None:
        assert token, "Token cannot be empty"
        self.persist(MastodonAuth(instance or DEFAULT_MASTODON_INSTANCE, token))

    def save_language(self, language: str) -> None:
        self.persist(language)
