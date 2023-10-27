from pathlib import Path
from typing import List

from typer import run

from not_my_ex.bluesky import Bluesky
from not_my_ex.mastodon import Mastodon
from not_my_ex.posts import Media, Post
from not_my_ex.settings import BLUESKY, CLIENTS_AVAILABLE, MASTODON


def clients():
    clients = {BLUESKY: Bluesky, MASTODON: Mastodon}
    yield from (cls() for key, cls in clients.items() if key in CLIENTS_AVAILABLE)


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


def main(text: str, images: List[str] = []):
    images = tuple(media_from(path) for path in images)
    post = Post(text, images or None)
    check_language(post)
    for client in clients():
        print(client.post(post))


def cli():
    run(main)


if __name__ == "__main__":
    cli()
