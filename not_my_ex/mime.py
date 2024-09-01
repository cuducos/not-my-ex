from mimetypes import guess_type
from typing import Optional

GUESSES = {"image/jpeg": ("jpg", "jpeg"), "image/png": ("png",)}


def mime_for(path: str, contents: bytes) -> Optional[str]:
    mime, *_ = guess_type(path)
    if isinstance(mime, str):
        return mime

    for mime, guesses in GUESSES.items():
        for guess in guesses:
            if guess.upper().encode() in contents[:128]:
                return mime
            if guess.encode() in contents[:128]:
                return mime

    return None
