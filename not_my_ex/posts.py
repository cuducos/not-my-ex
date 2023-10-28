from dataclasses import dataclass
from mimetypes import guess_type
from typing import Iterable, Optional

from aiofiles import open, os
from eld import LanguageDetector  # type: ignore

from not_my_ex.settings import LIMIT


class PostTooLongError(Exception):
    pass


@dataclass
class Media:
    content: bytes
    mime: str
    alt: str

    @classmethod
    async def from_img(cls, img: str, alt: str) -> "Media":
        if not await os.path.exists(img):
            raise ValueError(f"File {img} does not exist")

        mime, *_ = guess_type(img)
        if not isinstance(mime, str):
            raise ValueError(f"Could not guess mime type for {img}")

        async with open(img, "rb") as handler:
            contents = await handler.read()

        return cls(contents, mime, alt)


@dataclass
class Post:
    text: str
    media: Optional[Iterable[Media]] = None
    lang: Optional[str] = None

    def __post_init__(self):
        if len(self.text) > LIMIT:
            raise PostTooLongError(f"Text cannot be longer than {LIMIT} characters")

        if not self.lang:
            detector = LanguageDetector()
            self.lang = detector.detect(self.text).language
