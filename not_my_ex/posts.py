from dataclasses import dataclass
from mimetypes import guess_type
from pathlib import Path
from typing import Iterable, Optional

from eld import LanguageDetector

from not_my_ex.settings import LIMIT


class PostTooLongError(Exception):
    pass


@dataclass
class Media:
    content: bytes
    mime: str
    alt: str

    @classmethod
    def from_img(cls, img, alt):
        path = Path(img)
        mime, *_ = guess_type(path)
        return cls(path.read_bytes(), mime, alt)


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
