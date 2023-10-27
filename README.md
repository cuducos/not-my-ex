# Not my ex

Tiny CLI to post simultaneously to Mastodon and Bluesky.

<small>Obviously, based on [`cuducos/from-my-ex`](https://github.com/cuducos/from-my-ex).</small>

## Getting started

### Requirements

* Python 3.9 or newer
* [Poetry](https://python-poetry.org)

### Configuration

#### To repost in [Bluesky](https://bsky.app)

| Name | Description | Example | Default value |
|---|---|---|---|
| `NOT_MY_EX_BSKY_AGENT` | Bluesky instance | `"https://bsky.social"` | `"https://bsky.social"` |
| `NOT_MY_EX_BSKY_EMAIL` | Email used in Bluesky | `"cuducos@mailinator.com"` | `None` |
| `NOT_MY_EX_BSKY_PASSWORD` | Password used in Bluesky | As created in [App Passwords](https://bsky.app/settings/app-passwords) | `None` |

Not setting `NOT_MY_EX_BSKY_EMAIL` **or** `NOT_MY_EX_BSKY_PASSWORD` disables Bluesky reposting.

#### To repost in [Mastodon](https://joinmastodon.org/)

| Name | Description | Example | Default value |
|---|---|---|---|
| `NOT_MY_EX_MASTODON_INSTANCE` | Mastodon instance | `"https://tech.lgbt"` | `"https://mastodon.social"` |
| `NOT_MY_EX_MASTODON_TOKEN` | Mastodon access token | Go to your _Settings_, _Development_ and then create an app to get the access token. Select the `write:statuses` and `write:media` scopes. | `None` |

Not setting `NOT_MY_EX_MASTODON_TOKEN` disables Mastodon reposting.

## Usage

```console
$ poetry install
$ poetry shell
$ python -m not_my_ex "Magic, madness, heaven, sin " --images /tmp/1989.gif
$ exit
```

You can skip `--images` or pass multiple images  (e.g. `--images taylor.jpg --images swift.gif`).

## Contributing

The tests include [Ruff](https://docs.astral.sh/ruff/) and [`isort`](https://pycqa.github.io/isort/):

```console
$ poetry run ruff format . tests/
$ poetry run ruff . tests/
$ poetry run pytest
```
