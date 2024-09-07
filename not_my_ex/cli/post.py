from asyncio import gather, get_event_loop
from sys import stderr
from typing import Annotated, List, Optional

from aiofiles import open, os
from httpx import AsyncClient
from typer import Option, echo, style

from not_my_ex.bluesky import Bluesky
from not_my_ex.cli import error
from not_my_ex.client import ClientError
from not_my_ex.mastodon import Mastodon
from not_my_ex.media import ImageTooBigError, Media
from not_my_ex.post import Post, PostTooLongError
from not_my_ex.settings import (
    BLUESKY,
    CLIENTS_AVAILABLE,
    DEFAULT_LANG,
    MASTODON,
)

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

    echo(f"{client.emoji} {style(client.name, bold=True)} {url}")


async def media_from(path: str, ask_for_alt_text: bool) -> Media:
    media = await Media.from_img(path)
    if ask_for_alt_text:
        media.check_alt_text()
    return media


async def main(
    text: str, images: List[str], lang: Optional[str], yes_to_all: bool
) -> None:
    lang = lang or DEFAULT_LANG
    if len(images) > 4:
        raise ValueError("You can only post up to 4 images")

    if await os.path.exists(text):
        async with open(text) as handler:
            text = await handler.read()

    load = tuple(media_from(path, not yes_to_all) for path in images)
    try:
        imgs = await gather(*load)
    except ImageTooBigError as err:
        error(err)

    post = Post(text, imgs or None, lang)
    if not lang and not yes_to_all:
        post.check_language()

    async with AsyncClient() as http:
        tasks = tuple(post_and_print_url(key, http, post) for key in CLIENTS_AVAILABLE)
        await gather(*tasks)


def post(
    text: str,
    images: Annotated[
        List[str], Option("--images", "-i", help="Path to the images to post (max. 4)")
    ] = [],
    lang: Annotated[
        Optional[str],
        Option(
            "--lang",
            "-l",
            help="Language for the post (2-letter ISO 639-1 code)",
        ),
    ] = None,
    yes_to_all: Annotated[
        bool,
        Option(
            "--yes-to-all",
            "-y",
            help="Do not ask for alt text for images and/or post language confirmation",
        ),
    ] = False,
) -> None:
    """Post content. TEXT can be the post text itself, or the path to a text file."""
    loop = get_event_loop()
    try:
        loop.run_until_complete(main(text, images, lang, yes_to_all))
    except PostTooLongError as err:
        error(err)
