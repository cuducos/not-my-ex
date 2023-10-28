from dataclasses import dataclass
from mimetypes import guess_type
from pathlib import Path
from typing import Iterable, Optional

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
    def from_img(cls, img: Path, alt: str) -> "Media":
        mime, *_ = guess_type(img)
        if not isinstance(mime, str):
            raise ValueError(f"Could not guess mime type for {img}")
        return cls(img.read_bytes(), mime, alt)


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
