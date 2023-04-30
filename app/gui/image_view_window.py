import imgui

from app.pic_review import PicReview


class ImageViewWindow:
    _backend: PicReview

    def __init__(self, backend: PicReview) -> None:
        self._backend = backend

    def render(self):
        ws = self._backend.get_current_workspace()
        if ws is None:
            return
        with imgui.begin("Image View", closable=True):
            imgui.text("Image View")
