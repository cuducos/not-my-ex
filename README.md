# Not my ex

Tiny CLI to post simultaneously to Mastodon and Bluesky.

<small>Obviously, based on [`cuducos/from-my-ex`](https://github.com/cuducos/from-my-ex).</small>

It supports:
* Post status updates to both networks with a simple CLI command
* Posting with images
* Including alt text for images
* Setting post language

It does not support:
* Tagging other users (they would have different IDs and servers in each platform)

## Getting started

### Requirements

* Python 3.9 or newer
* [Poetry](https://python-poetry.org)

#### Environment variables

##### To repost in [Bluesky](https://bsky.app)

| Name | Description | Example | Default value |
|---|---|---|---|
| `NOT_MY_EX_BSKY_AGENT` | Bluesky instance | `"https://bsky.social"` | `"https://bsky.social"` |
| `NOT_MY_EX_BSKY_EMAIL` | Email used in Bluesky | `"cuducos@mailinator.com"` | `None` |
| `NOT_MY_EX_BSKY_PASSWORD` | Password used in Bluesky | As created in [App Passwords](https://bsky.app/settings/app-passwords). | `None` |

Not setting `NOT_MY_EX_BSKY_EMAIL` **or** `NOT_MY_EX_BSKY_PASSWORD` disables Bluesky reposting.

##### To repost in [Mastodon](https://joinmastodon.org/)

| Name | Description | Example | Default value |
|---|---|---|---|
| `NOT_MY_EX_MASTODON_INSTANCE` | Mastodon instance | `"https://tech.lgbt"` | `"https://mastodon.social"` |
| `NOT_MY_EX_MASTODON_TOKEN` | Mastodon access token | Go to your _Settings_, _Development_ and then create an app to get the access token. Select the `write:statuses` and `write:media` scopes. | `None` |

Not setting `NOT_MY_EX_MASTODON_TOKEN` disables Mastodon reposting.

## Install

```console
$ pip install not-my-ex
```

## Usage


### CLI

```console
$ not-my-ex "Magic, madness, heaven, sin " --images /tmp/1989.gif
```

You can skip `--images` or pass multiple images  (e.g. `--images taylor.jpg --images swift.gif`).

### API

```python
from asyncio import gather

from httpx import AsyncClient

from not_my_ex.bluesky import Bluesky
from not_my_ex.mastodon import Mastodon
from not_my_ex.media import Media
from not_my_ex.post import Post


async def main():
    media_tasks = tuple(
        Media.from_img(path, alt=alt)
        for path, alt in (("taylor.jpg", "Taylor"), ("swift.jpg", "Swift"))
    )
    media = await gather(*media_tasks)

    post = Post(text="Magic, madness, heaven, sin ", media=media, lang="en")
    async with AsyncClient() as http:
        post_tasks = tuple(cls(http).post(post) for cls in (Bluesky, Mastodon))
        await gather(*post_tasks)
```

In `Post`, both `media` and `lang` are optional. In `Media`, `alt` is optional.

## Contributing

The tests include [Ruff](https://docs.astral.sh/ruff/) and [Mypy](https://www.mypy-lang.org/):

```console
$ poetry install
$ poetry run pytest
```
