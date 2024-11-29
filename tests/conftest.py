from base64 import b64decode
from os import environ
from pathlib import Path
from tempfile import NamedTemporaryFile

from pytest import fixture

from not_my_ex.auth import EnvAuth

ONE_PIXEL_IMAGE = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAAC0lEQVQIW2NgAAIAAAUAAR4"
    "f7BQAAAAASUVORK5CYII="
)
SETTINGS = {
    "BSKY_EMAIL": "python@mailinator.com",
    "BSKY_PASSWORD": "forty2",
    "MASTODON_TOKEN": "40two",
}


def pytest_configure(config):
    for key, value in SETTINGS.items():
        environ[f"NOT_MY_EX_{key}"] = value
    return config


@fixture
def image():
    with NamedTemporaryFile(suffix=".png") as tmp:
        content = b64decode(ONE_PIXEL_IMAGE)
        path = Path(tmp.name)
        path.write_bytes(content)
        yield (path, content)


@fixture
def auth():
    return EnvAuth()
