from os import getenv

from typer import (
    colors,
    confirm,
    echo,
    prompt,
    secho,
    style,
)

from not_my_ex.auth import EncryptedAuth, cache
from not_my_ex.settings import DEFAULT_BLUESKY_AGENT, DEFAULT_MASTODON_INSTANCE


def clean() -> None:
    """Delete local authentication credentials and language preferences."""
    path = cache()
    if not path.exists():
        secho(
            f"{path} not found, nothing to delete.",
            fg=colors.YELLOW,
            bold=True,
        )
        return

    confirm(f"Do you want to delete {path}?", abort=True)
    path.unlink()
    secho(f"{path} deleted", fg=colors.GREEN, bold=True)


def config() -> None:
    """Prompt to save authentication credentials and language preferences."""
    path = cache()
    not_my_ex = style("not-my-ex", bold=True)
    discouraged = style("highly discouraged", bold=True)

    if path.exists():
        password = prompt(
            f"Please, enter the password you used to configure {not_my_ex}",
            hide_input=True,
        )
    else:
        echo(
            "Create a password to protect the local credentials you are gonne use "
            f"configure {not_my_ex}. An empty password is allowed but {discouraged}."
        )
        password = prompt("Password", hide_input=True, confirmation_prompt=True)

    auth = EncryptedAuth(password)

    if confirm("Do you want to configure Bluesky?"):
        email = prompt("Email you used to create your Bkuesky account")
        app_password = prompt(
            (
                f"App password you created for {not_my_ex} "
                "(see https://bsky.app/settings/app-passwords)"
            ),
            hide_input=True,
        )
        echo("Bluesky requires a custom agent name. ")
        agent = prompt("Bluesky agent", default=DEFAULT_BLUESKY_AGENT)
        auth.save_bluesky(email, app_password, agent)

    if confirm("Do you want to configure Mastodon?"):
        settings = style("Settings", bold=True)
        development = style("Development", bold=True)
        write = " and ".join(
            style(txt, bold=True) for txt in ("write:statuses", "write:media")
        )
        token = prompt(
            (
                f"Token for {not_my_ex} (get one from {settings} » {development}) and "
                f"create one with {write} permissions)"
            ),
            hide_input=True,
        )
        instance = prompt("Mastodon instance", default=DEFAULT_MASTODON_INSTANCE)
        auth.save_mastodon(token, instance)

    language = prompt(
        "Preferred language for posts (2-letter ISO 639-1 code)",
        default=getenv("NOT_MY_EX_DEFAULT_LANG"),
    )
    auth.save_language(language)
    secho(f"Saved encrypted configuration at {path}", fg=colors.GREEN, bold=True)
