from asyncio import get_event_loop
from importlib import import_module
from importlib.metadata import version

from typer import Typer

from not_my_ex.auth import EnvAuth
from not_my_ex.cli.config import clean, config
from not_my_ex.cli.post import post


def register_gui_if_available(app):
    try:
        module = import_module("not_my_ex.gui")
    except ImportError:
        return

    def gui() -> None:
        """Opens the GUI to creaet and post."""
        auth = EnvAuth()
        auth.assure_configured()
        loop = get_event_loop()
        loop.run_until_complete(module.gui)

    app.command()(gui)


def cli():
    app = Typer(
        name=f"not-my-ex {version('not_my_ex')}",
        help="not-my-ex posts micro blogging to Mastodon and Bluesky.",
    )

    app.command()(post)
    app.command()(clean)
    app.command()(config)
    register_gui_if_available(app)
    app()
