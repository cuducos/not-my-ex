from sys import stderr
from typing import Optional, Union

from typer import colors, echo, style


def error(err: Union[Exception, str], details: Optional[str] = None):
    if isinstance(err, Exception):
        title = err.__class__.__name__
        details = str(err)
    else:
        title = err

    msg = style(title, bold=True, fg=colors.RED)
    if details:
        msg += details

    echo(msg, file=stderr)
    exit(1)
