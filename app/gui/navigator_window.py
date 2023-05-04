from typing import Optional, List

import imgui

from app.gui.components.texture import Texture
from app.pic_review import PicReview


class NavigatorWindow:
    _backend: PicReview
    _tx: Optional[List[Texture]] = None

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

        with imgui.begin("Navigator", closable=False):
            imgui.text(f"Navigator: {self._backend.get_current_workspace_images_rank_histogram()}")
            if self._tx is not None:
                with imgui.begin_child(label="images_area", border=True, flags=imgui.WINDOW_HORIZONTAL_SCROLLING_BAR):
                    for tx in self._tx:
                        tx.render()
                        # todo: render image rank - number, and also higher is rank is above current
                        # rank range, middle if within current range filter, and lower if rank is below the range filter
                        imgui.same_line()
