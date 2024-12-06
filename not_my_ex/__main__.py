from importlib.metadata import version

from typer import Typer

from not_my_ex.cli.config import clean, config
from not_my_ex.cli.post import post


def cli():
    app = Typer(
        name=f"not-my-ex {version('not_my_ex')}",
        help="not-my-ex posts micro blogging to Mastodon and Bluesky.",
    )

    app.command()(post)
    app.command()(clean)
    app.command()(config)
    app()


if __name__ == "__main__":
    cli()
