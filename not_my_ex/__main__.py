from asyncio import gather, get_event_loop
from sys import stderr
from typing import List

from httpx import AsyncClient
from typer import run

from not_my_ex.bluesky import Bluesky
from not_my_ex.client import ClientError
from not_my_ex.mastodon import Mastodon
from not_my_ex.posts import Media, Post
from not_my_ex.settings import BLUESKY, CLIENTS_AVAILABLE, MASTODON

CLIENTS = {BLUESKY: Bluesky, MASTODON: Mastodon}


async def media_from(path: str) -> Media:
    alt = input(f"Enter an alt text for {path}: ")
    return await Media.from_img(path, alt=alt)


def check_language(post: Post) -> None:
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


async def post_and_print_url(key: str, http: AsyncClient, post: Post) -> None:
    try:
        client = CLIENTS[key](http)
    except KeyError:
        raise ValueError(f"Unknown client {key}, options are: {', '.join(CLIENTS)}")

    try:
        await client.auth()
        url = await client.post(post)
    except ClientError as exc:
        print(str(exc), file=stderr)
        return

    print(f"[{client.name}] {url}")


async def main(text: str, images: List[str] = []) -> None:
    load = tuple(media_from(path) for path in images)
    imgs = await gather(*load)
    post = Post(text, imgs or None)
    check_language(post)
    async with AsyncClient() as http:
        tasks = tuple(post_and_print_url(key, http, post) for key in CLIENTS_AVAILABLE)
        await gather(*tasks)


def wrapper(text: str, images: List[str] = []) -> None:
    loop = get_event_loop()
    loop.run_until_complete(main(text, images))


def cli() -> None:
    run(wrapper)


if __name__ == "__main__":
    cli()
