from dataclasses import dataclass
from mimetypes import guess_type
from typing import Optional

from aiofiles import open, os


@dataclass
class Media:
    path: str
    content: bytes
    mime: str
    alt: Optional[str] = None

    @classmethod
    async def from_img(cls, img: str, alt: Optional[str] = None) -> "Media":
        if not await os.path.exists(img):
            raise ValueError(f"File {img} does not exist")

        mime, *_ = guess_type(img)
        if not isinstance(mime, str):
            raise ValueError(f"Could not guess mime type for {img}")

        async with open(img, "rb") as handler:
            contents = await handler.read()

        return cls(img, contents, mime, alt)

    def check_alt_text(self):
        while not self.alt:
            alt = input(f"Enter an alt text for {self.path}: ")
            self.alt = alt.strip() or None
