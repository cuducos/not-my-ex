from dataclasses import dataclass
from typing import Iterable, Optional

from eld import LanguageDetector  # type: ignore

from not_my_ex.language import Language
from not_my_ex.media import Media


class PostTooLongError(Exception):
    pass


@dataclass
class Post:
    text: str
    limit: int = 300
    media: Optional[Iterable[Media]] = None
    lang: Optional[str] = None

    def __post_init__(self):
        if len(self.text) > self.limit:
            raise PostTooLongError(
                f"Text cannot be longer than {self.limit} characters. This text is "
                f"{len(self.text)} characters long."
            )

        if not self.lang:
            detector = LanguageDetector()
            self.lang = detector.detect(self.text).language

    def check_language(self):
        if self.lang:
            answer = input(f"Is the post language {self.lang}? [y/n] ")
            if answer.lower() == "y":
                return

        lang = Language()
        lang.ask()
        self.lang = lang.name
