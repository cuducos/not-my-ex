from asyncio import gather, get_event_loop
from pathlib import Path
from typing import List

from httpx import AsyncClient
from typer import run

from not_my_ex.bluesky import Bluesky, BlueskyError
from not_my_ex.mastodon import Mastodon, MastodonError
from not_my_ex.posts import Media, Post
from not_my_ex.settings import BLUESKY, CLIENTS_AVAILABLE, MASTODON


def media_from(path):
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)

    alt = input(f"Enter an alt text for {path.name}: ")
    return Media.from_img(path, alt=alt)


def check_language(post):
    answer = input(f"Is the post language {post.lang}? [y/n] ")
    if answer.lower() == "y":
        return

    lang = None
    while not lang:
        lang = input("Enter the language (2-letter ISO 639-1 code): ")
        if lang.isalpha() and len(lang) == 2:
            break

        lang = None

    post.lang = lang


async def post_and_print_url(cls, http_client, post):
    client = cls(http_client)
    await client.auth()

    try:
        output = await client.post(post)
    except (BlueskyError, MastodonError) as exc:
        output = str(exc)

    *_, name = client.__class__.__name__.split(".")
    print(f"[{name}] {output}")


async def main(text, images):
    clients = (
        cls
        for key, cls in ((BLUESKY, Bluesky), (MASTODON, Mastodon))
        if key in CLIENTS_AVAILABLE
    )
    images = tuple(media_from(path) for path in images)
    post = Post(text, images or None)
    check_language(post)
    async with AsyncClient() as http:
        tasks = tuple(post_and_print_url(cls, http, post) for cls in clients)
        await gather(*tasks)


def wrapper(text: str, images: List[str] = []):
    loop = get_event_loop()
    loop.run_until_complete(main(text, images))


def cli():
    run(wrapper)


if __name__ == "__main__":
    cli()
