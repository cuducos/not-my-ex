from os import getenv


class EnvironmentVariableNotFoundError(Exception):
    pass


BLUESKY = "bsky"
MASTODON = "mstdn"

DEFAULT_BLUESKY_AGENT = "https://bsky.social"
BSKY_AGENT = getenv("NOT_MY_EX_BSKY_AGENT", DEFAULT_BLUESKY_AGENT)
BSKY_EMAIL = getenv("NOT_MY_EX_BSKY_EMAIL")
BSKY_PASSWORD = getenv("NOT_MY_EX_BSKY_PASSWORD")

DEFAULT_MASTODON_INSTANCE = "https://mastodon.social"
MASTODON_INSTANCE = getenv("NOT_MY_EX_MASTODON_INSTANCE", DEFAULT_MASTODON_INSTANCE)
MASTODON_TOKEN = getenv("NOT_MY_EX_MASTODON_TOKEN")

DEFAULT_LANG = getenv("NOT_MY_EX_DEFAULT_LANG")

CLIENTS_AVAILABLE = set(
    key
    for key, value in (
        (BLUESKY, BSKY_EMAIL and BSKY_PASSWORD),
        (MASTODON, MASTODON_TOKEN),
    )
    if value
)

LIMIT = 300 if BLUESKY in CLIENTS_AVAILABLE else 1024

IMAGE_SIZE_LIMIT = 1024 * 1024 if BLUESKY in CLIENTS_AVAILABLE else None

if not CLIENTS_AVAILABLE:
    raise EnvironmentVariableNotFoundError(
        "No clients available. Please set at least one of the following environment "
        "variables:\n"
        "- NOT_MY_EX_BSKY_EMAIL and NOT_MY_EX_BSKY_PASSWORD"
        "- NOT_MY_EX_MASTODON_TOKEN"
    )
