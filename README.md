# Not my ex [![PyPI](https://img.shields.io/pypi/v/not-my-ex)](https://pypi.org/project/not-my-ex/) [![Tests](https://img.shields.io/github/actions/workflow/status/cuducos/not-my-ex/pytest.yml)](https://github.com/cuducos/not-my-ex/actions/workflows/pytest.yml) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/not-my-ex)](https://pypi.org/project/not-my-ex/)

Tiny app to post simultaneously to Mastodon and Bluesky.

<small>Obviously, based on [`cuducos/from-my-ex`](https://github.com/cuducos/from-my-ex).</small>

It supports:

* Post status updates to both networks with a simple CLI command
* Posting with images
* Including alt text for images
* Setting post language

It does not support:

* Tagging other users (they would have different IDs and servers in each platform)

It used to have:

* A simple [GUI](https://en.wikipedia.org/wiki/Graphical_user_interface) (version 0.1.1), but dropped support to focus on CLI — there are other great GUI out there by now

## Getting started

### Requirements

* Python 3.9 or newer

#### Environment variables

##### General settings

| Name | Description | Example | Default value |
|---|---|---|---|
| `NOT_MY_EX_DEFAULT_LANG` | 2-letter ISO 639-1 code | `"pt"` | `None` |


##### To post to [Bluesky](https://bsky.app)

| Name | Description | Example | Default value |
|---|---|---|---|
| `NOT_MY_EX_BSKY_AGENT` | Bluesky instance | `"https://bsky.social"` | `"https://bsky.social"` |
| `NOT_MY_EX_BSKY_EMAIL` | Email used in Bluesky | `"cuducos@mailinator.com"` | `None` |
| `NOT_MY_EX_BSKY_PASSWORD` | Password used in Bluesky | As created in [App Passwords](https://bsky.app/settings/app-passwords). | `None` |

Not setting `NOT_MY_EX_BSKY_EMAIL` **or** `NOT_MY_EX_BSKY_PASSWORD` disables posting to Bluesky.

##### To post to [Mastodon](https://joinmastodon.org/)

| Name | Description | Example | Default value |
|---|---|---|---|
| `NOT_MY_EX_MASTODON_INSTANCE` | Mastodon instance | `"https://tech.lgbt"` | `"https://mastodon.social"` |
| `NOT_MY_EX_MASTODON_TOKEN` | Mastodon access token | Go to your _Settings_, _Development_ and then create an app to get the access token. Select the `write:statuses` and `write:media` scopes. | `None` |

Not setting `NOT_MY_EX_MASTODON_TOKEN` disables posting to Mastodon.

## Install

```console
$ pip install not-my-ex
```

## Usage

### CLI

```console
$ not-my-ex post "Magic, madness, heaven, sin" --images /tmp/1989.gif
```

You can skip `--images` or pass multiple images  (e.g. `--images taylor.jpg --images swift.gif`). Check `--help` for more details on commands and subcommands.

### API

```python
from asyncio import gather

from httpx import AsyncClient

from not_my_ex.auth import EnvAuth
from not_my_ex.bluesky import Bluesky
from not_my_ex.mastodon import Mastodon
from not_my_ex.media import Media
from not_my_ex.post import Post


async def main():
    auth = EnvAuth()
    media_tasks = tuple(
        Media.from_img(path, alt, auth.image_size_limit)
        for path, alt in (("taylor.jpg", "Taylor"), ("swift.jpg", "Swift"))
    )
    media = await gather(*media_tasks)

    post = Post("Magic, madness, heaven, sin", auth.limitm, media, "en")
    async with AsyncClient() as http:
        post_tasks = tuple(cls(http).post(post) for cls in (Bluesky, Mastodon))
        await gather(*post_tasks)
```

In `Post`, `limit`, `media` and `lang` are optional. In `Media`, both `alt` and `image_size_limit` are optional.

The usage of `auth.limit` and `auth.image_size_limit` makes sure the limits are set according to the authenticated clients.

## Contributing

Requires [`uv`](https://docs.astral.sh/uv) Python package manager. The tests include [Ruff](https://docs.astral.sh/ruff/) and [Mypy](https://www.mypy-lang.org/):

```console
$ uv run pytest
```
