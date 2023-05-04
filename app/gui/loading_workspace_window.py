import imgui

from app.gui.components.texture import Texture
from app.pic_review import PicReview


class LoadingWorkspaceWindow:
    _backend: PicReview

    def __init__(self, backend: PicReview) -> None:
        self._backend = backend

    def render(self):
        ws = self._backend.get_current_workspace()
        if ws is None:
            return

        if not self._tx:
            images = self._backend.get_current_workspace_images()
            if images:
                self._tx = [Texture.create_form(i.with_populated_thumbnail().thumbnail) for i in images]

        # todo: looks like thumbs are not persisted at the moment, let's generate them on ws refresh and persist, the progressbar should indicate
        with imgui.begin("Loading workspace", closable=False):
            imgui.text(f"Opening workspace {ws.name} @ {ws.path}")
            imgui.progress_bar(float_fraction=0.5, size=(20, 100), str_overlay="o hai")
