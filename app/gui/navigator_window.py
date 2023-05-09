from typing import Optional, List

import imgui
from imgui.core import _DrawList

from app.gui.components.texture import Texture
from app.pic_review import PicReview


class NavigatorWindow:
    _backend: PicReview
    _thumbs: Optional[List[Texture]] = None
    _thumb_size: float = 100.0
    _current_image: Optional[int] = None

    def __init__(self, backend: PicReview) -> None:
        self._backend = backend

    def render(self):
        ws = self._backend.get_current_workspace()
        if ws is None:
            return

        if not self._thumbs:
            images = self._backend.get_current_workspace_images()
            if images:
                self._thumbs = [Texture.create_form(i.with_populated_thumbnail().thumbnail) for i in images]
                self._current_image = 0

        with imgui.begin("Navigator", closable=False):
            dl: _DrawList = imgui.get_window_draw_list()
            imgui.text(f"Navigator: {self._backend.get_current_workspace_images_rank_histogram()}")
            if self._thumbs is not None:
                total_images = len(self._thumbs)

                spacing = 3.0
                thumb_and_spacing_w = spacing + self._thumb_size
                images_to_display = int(imgui.get_content_region_available_width() / thumb_and_spacing_w)
                visible_range = self._find_visible_range(total_images, images_to_display)
                imgui.text(str(visible_range))

                for i, tx in enumerate(self._thumbs[visible_range.start:visible_range.stop]):
                    i and imgui.same_line(spacing=spacing)
                    if i + visible_range.start == self._current_image:
                        cur = imgui.get_cursor_screen_pos()
                        tx.render(w=self._thumb_size, h=self._thumb_size, keep_aspect_ratio=True)
                        self._highlight_texture(dl, cur.x, cur.y)
                    else:
                        tx.render(w=self._thumb_size, h=self._thumb_size, keep_aspect_ratio=True)
                    # todo: render image rank - number, and also higher is rank is above current
                    # rank range, middle if within current range filter, and lower if rank is below the range filter
                self._draw_current_image_slider(total_images)

    def _find_visible_range(self, range_size: int, subrange_size: int) -> range:
        # Ensure subrange_size is not greater than range_size
        subrange_size = min(subrange_size, range_size)

        # Calculate the half size of the subrange
        half_size = (subrange_size - 1) // 2

        # Calculate the start and end of the subrange
        start = max(0, self._current_image - half_size)
        end = start + subrange_size

        # If the end goes beyond the range, adjust the start and end
        if end > range_size:
            end = range_size
            start = max(0, end - subrange_size)

        return range(start, end)

    def _draw_current_image_slider(self, total_images: int):
        imgui.push_item_width(-1.0)
        _changed, self._current_image = imgui.slider_int(
            label="Selected image",
            value=self._current_image,
            min_value=0,
            max_value=total_images - 1,
            format=f"%.f / {total_images}",
        )
        imgui.pop_item_width()

    def _highlight_texture(self, dl: _DrawList, x: float, y: float):
        highlight_color = imgui.get_color_u32_rgba(1, 1, 0, 1)
        dl.add_rect(x - 2, y - 2, x + self._thumb_size + 2, y + self._thumb_size + 2, highlight_color)
