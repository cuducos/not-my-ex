from asyncio import gather, run
from typing import Iterable, Optional

from httpx import AsyncClient

try:
    from wx import (
        ALIGN_CENTER,
        ALIGN_CENTER_VERTICAL,
        ALL,
        EVT_BUTTON,
        EVT_FILEPICKER_CHANGED,
        EVT_TEXT,
        EXPAND,
        HORIZONTAL,
        ICON_ERROR,
        ICON_INFORMATION,
        LEFT,
        OK,
        RIGHT,
        TE_MULTILINE,
        TOP,
        VERTICAL,
        BoxSizer,
        Button,
        Colour,
        FilePickerCtrl,
        Frame,
        MessageBox,
        Panel,
        StaticText,
        TextCtrl,
        Window,
    )
    from wxasync import AsyncBind, WxAsyncApp  # type: ignore
except ModuleNotFoundError:
    msg = (
        "The GUI is only available if `not-my-ex` is installed with the `gui` extra. "
        "For example, try `pip install not-my-ex[gui]` and then `not-my-ex-gui` again."
    )
    raise RuntimeError(msg)


from not_my_ex.bluesky import Bluesky
from not_my_ex.client import ClientError
from not_my_ex.mastodon import Mastodon
from not_my_ex.media import Media
from not_my_ex.post import Post
from not_my_ex.settings import BLUESKY, CLIENTS_AVAILABLE, DEFAULT_LANG, LIMIT, MASTODON

CLIENTS = {
    key: value
    for key, value in ((BLUESKY, Bluesky), (MASTODON, Mastodon))
    if key in CLIENTS_AVAILABLE
}
BLACK = Colour(0, 0, 0)
RED = Colour(128, 0, 0)
BORDER = 10


class NotMyExFrame(Frame):
    def __init__(self, http, *args, **kwargs) -> None:
        self.clients = {key: cls(http) for key, cls in CLIENTS.items()}
        self.labels = " & ".join(c.name for c in self.clients.values())
        super(NotMyExFrame, self).__init__(*args, **kwargs)
        panel = Panel(self)
        self.post = TextCtrl(panel, style=TE_MULTILINE)
        self.chars = StaticText(panel, label=f"0/{LIMIT}")
        self.images = tuple(
            FilePickerCtrl(
                panel,
                wildcard="Images (*.jpg;*.jpeg;*.png;*.gif)|*.jpg;*.jpeg;*.png;*.gif",
            )
            for _ in range(4)
        )
        self.alts = tuple(TextCtrl(panel, size=(50, -1)) for _ in range(4))
        self.lang = TextCtrl(panel, value=DEFAULT_LANG or "", size=(50, -1))
        self.button = Button(panel, label=f"Post to {self.labels}".replace("&", "&&"))
        self.button.Disable()

        self.post.Bind(EVT_TEXT, self.when_typing)
        self.lang.Bind(EVT_TEXT, self.when_typing)
        for img in self.images:
            img.Bind(EVT_FILEPICKER_CHANGED, self.validate)

        sizer = BoxSizer(VERTICAL)
        sizer.Add(StaticText(panel, label="New post:"), flag=LEFT | TOP, border=BORDER)
        sizer.Add(
            self.post,
            proportion=1,
            flag=EXPAND | LEFT | RIGHT | TOP,
            border=BORDER,
        )

        box = BoxSizer(HORIZONTAL)
        box.Add(
            StaticText(panel, label="Language (two-letter code):"),
            flag=ALIGN_CENTER_VERTICAL | LEFT,
            border=BORDER,
        )
        box.Add(
            self.lang,
            proportion=1,
            flag=ALIGN_CENTER_VERTICAL | RIGHT,
            border=BORDER,
        )
        box.AddStretchSpacer()
        box.Add(self.chars, flag=EXPAND | ALL, border=BORDER)
        sizer.Add(box, proportion=0, flag=EXPAND | ALL)

        sizer.Add(
            StaticText(panel, label="Images and their alternative texts (optional):"),
            flag=LEFT | TOP,
            border=BORDER,
        )
        for picker, alt in zip(self.images, self.alts):
            sizer.Add(picker, flag=EXPAND | LEFT | RIGHT | TOP, border=BORDER)
            sizer.Add(alt, flag=EXPAND | LEFT | RIGHT | TOP, border=BORDER)
            sizer.Add(Window(panel, size=(10, 10)), 0, EXPAND)

        sizer.Add(self.button, flag=ALIGN_CENTER | ALL, border=BORDER)

        panel.SetSizer(sizer)

        self.SetTitle(f"Not my ex: post to {self.labels}")
        self.SetSize((400, 645))

    @property
    def has_media(self):
        for img in self.images:
            if img.GetPath():
                return True
        return False

    async def media(self) -> Optional[Iterable[Media]]:
        imgs = tuple(
            Media.from_img(path, alt.GetValue() or None)
            for img, alt in zip(self.images, self.alts)
            if (path := img.GetPath())
        )
        if not imgs:
            return None
        return await gather(*imgs)

    def when_typing(self, event) -> None:
        text = self.post.GetValue()
        self.chars.SetLabel(f"{len(text)}/{LIMIT}")
        if len(text) > LIMIT:
            self.chars.SetForegroundColour(RED)
        else:
            self.chars.SetForegroundColour(BLACK)
        self.validate(event)

    def validate(self, _) -> bool:
        text = self.post.GetValue()
        lang = self.lang.GetValue()
        text_is_valid = 0 < len(text) < LIMIT
        if (text_is_valid or self.has_media) and len(lang) == 2:
            self.button.Enable()
            return True

        self.button.Disable()
        return False

    async def on_submit(self, event) -> None:
        if not self.validate(event):
            return

        self.button.Disable()
        self.button.SetLabel(f"Posting to {self.labels}…")

        text = self.post.GetValue()
        media = await self.media()
        lang = self.lang.GetValue()
        tasks = tuple(
            client.post(Post(text, media, lang)) for client in self.clients.values()
        )

        try:
            await gather(*tasks)
        except ClientError as e:
            MessageBox(str(e), "Error", OK | ICON_ERROR)
            self.Close()

        MessageBox("Stamped and sent!", "Success", OK | ICON_INFORMATION)
        self.Close()


async def wrapper() -> None:
    async with AsyncClient() as session:
        app = WxAsyncApp()
        frame = NotMyExFrame(session, None)
        AsyncBind(EVT_BUTTON, frame.on_submit, frame.button)
        frame.Show()
        app.SetTopWindow(frame)
        await app.MainLoop()


def gui():
    run(wrapper())
