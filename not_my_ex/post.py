from dataclasses import dataclass
from typing import Iterable, Optional

from eld import LanguageDetector  # type: ignore

from not_my_ex.language import Language
from not_my_ex.media import Media
from not_my_ex.settings import LIMIT


class PostTooLongError(Exception):
    pass


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

    def check_language(self):
        answer = input(f"Is the post language {self.lang}? [y/n] ")
        if answer.lower() == "y":
            return

        lang = Language()
        lang.ask()
        self.lang = lang.name
