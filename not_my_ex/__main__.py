from asyncio import gather, get_event_loop
from sys import stderr
from typing import Annotated, List

from aiofiles import open, os
from httpx import AsyncClient
from typer import Option, run

from not_my_ex.bluesky import Bluesky
from not_my_ex.client import ClientError
from not_my_ex.mastodon import Mastodon
from not_my_ex.media import Media
from not_my_ex.post import Post
from not_my_ex.settings import BLUESKY, CLIENTS_AVAILABLE, MASTODON

CLIENTS = {BLUESKY: Bluesky, MASTODON: Mastodon}


async def post_and_print_url(key: str, http: AsyncClient, post: Post) -> None:
    try:
        cls = CLIENTS[key]
    except KeyError:
        raise ValueError(f"Unknown client {key}, options are: {', '.join(CLIENTS)}")

    client = cls(http)
    try:
        url = await cls(http).post(post)
    except ClientError as exc:
        print(str(exc), file=stderr)
        return

    print(f"[{client.name}] {url}")


async def media_from(path: str, ask_for_alt_text: bool) -> Media:
    media = await Media.from_img(path)
    if ask_for_alt_text:
        media.check_alt_text()
    return media


async def main(text: str, images: List[str], yes_to_all: bool) -> None:
    if len(images) > 4:
        raise ValueError("You can only post up to 4 images")

    if await os.path.exists(text):
        async with open(text) as handler:
            text = await handler.read()

    load = tuple(media_from(path, not yes_to_all) for path in images)
    imgs = await gather(*load)
    post = Post(text, imgs or None)
    if not yes_to_all:
        post.check_language()

    async with AsyncClient() as http:
        tasks = tuple(post_and_print_url(key, http, post) for key in CLIENTS_AVAILABLE)
        await gather(*tasks)


def wrapper(
    text: str,
    images: Annotated[
        List[str], Option(help="Path to the images to post (max. 4)")
    ] = [],
    yes_to_all: Annotated[
        bool,
        Option(
            "--yes-to-all",
            "-y",
            help="Do not ask for alt text for images and/or post language confirmation",
        ),
    ] = False,
) -> None:
    """not-my-ex post micro blogging to Mastodon and Bluesky.

    TEXT is the post text itself, or the path to a text file."""
    loop = get_event_loop()
    loop.run_until_complete(main(text, images, yes_to_all))


def cli() -> None:
    run(wrapper)


if __name__ == "__main__":
    cli()
