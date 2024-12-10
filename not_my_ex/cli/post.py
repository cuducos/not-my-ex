from asyncio import gather, get_event_loop
from collections import namedtuple
from os import getenv
from pathlib import Path
from subprocess import call
from sys import stderr
from tempfile import NamedTemporaryFile
from typing import Annotated, List, Optional

from aiofiles import open, os
from httpx import AsyncClient
from typer import Argument, Option, echo, prompt, style

from not_my_ex.auth import Auth, authenticate, cache
from not_my_ex.bluesky import Bluesky
from not_my_ex.cli import error
from not_my_ex.client import ClientError
from not_my_ex.mastodon import Mastodon
from not_my_ex.media import ImageTooBigError, Media
from not_my_ex.post import Post, PostTooLongError
from not_my_ex.settings import BLUESKY, MASTODON

CLIENTS = {BLUESKY: Bluesky, MASTODON: Mastodon}

Sent = namedtuple("Sent", "url client emoji")


async def send(key: str, http: AsyncClient, auth: Auth, post: Post) -> Optional[Sent]:
    try:
        cls = CLIENTS[key]
    except KeyError:
        raise ValueError(f"Unknown client {key}, options are: {', '.join(CLIENTS)}")

    client = cls(http, auth.for_client(key))
    try:
        url = await client.post(post)
    except ClientError as exc:
        print(str(exc), file=stderr)
        return None

    return Sent(url, client.name, client.emoji)


async def media_from(auth: Auth, path: str, ask_for_alt_text: bool) -> Media:
    media = await Media.from_img(path, None, auth.image_size_limit)
    if ask_for_alt_text:
        media.check_alt_text()
    return media


async def main(
    auth: Auth, text: str, images: List[str], lang: Optional[str], yes_to_all: bool
) -> None:
    if len(images) > 4:
        raise ValueError("You can only post up to 4 images")

    if await os.path.exists(text):
        async with open(text) as handler:
            text = await handler.read()

    load = tuple(media_from(auth, path, not yes_to_all) for path in images)
    try:
        imgs = await gather(*load)
    except ImageTooBigError as err:
        error(err)

    post = Post(text, auth.limit, imgs or None, lang)
    if not lang and not yes_to_all:
        post.check_language()

    async with AsyncClient() as http:
        tasks = tuple(send(key, http, auth, post) for key in auth.clients)
        posts = await gather(*tasks)

    for sent in posts:
        if sent:
            echo(f"{sent.emoji} {style(sent.client, bold=True)} {sent.url}")


def editor():
    with NamedTemporaryFile(prefix="not-my-ex-post", suffix=".txt") as tmp:
        call((getenv("EDITOR", "vim"), tmp.name))
        text = Path(tmp.name).read_text().strip()
    return text


def post(
    text: str = Argument(
        None,
        help=(
            "Text to post or path to a text file containing the content to post. "
            "If left blank, an editor (`EDITOR` environment variable) will open "
            "for you to type the post."
        ),
    ),
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
    skip_bluesky: Annotated[
        bool, Option("--skip-bluesky", help="Skip posting to Bluesky")
    ] = False,
    skip_mastodon: Annotated[
        bool, Option("--skip-mastodon", help="Skip posting to Mastodon")
    ] = False,
) -> None:
    """Post content. TEXT can be the post text itself, or the path to a text file."""
    loop = get_event_loop()
    text = text or editor()
    if not text:
        error("No text to post")

    password = None
    if cache().exists():
        not_my_ex = style("not-my-ex", bold=True)
        password = prompt(
            f"Please, enter the password you used to configure {not_my_ex}",
            hide_input=True,
        )

    auth = authenticate(password)
    if skip_bluesky:
        auth.invalidate(BLUESKY)
    if skip_mastodon:
        auth.invalidate(MASTODON)
    auth.assure_configured()

    try:
        loop.run_until_complete(main(auth, text, images, lang, yes_to_all))
    except PostTooLongError as err:
        error(err)
