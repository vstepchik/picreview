import dataclasses
import io
import os
from typing import Union, Tuple

import OpenGL.GL as GL
import imgui
from PIL import Image


@dataclasses.dataclass(frozen=True, eq=True)
class Texture:
    texture_id: int
    w: int
    h: int
    mem_size: int

    def render(self, w: float = None, h: float = None, keep_aspect_ratio: bool = True):
        if keep_aspect_ratio:
            w, h = w or self.w, h or self.h
            img_w, img_h = self._resize_to_fit_keeping_aspect_ratio((w, h))
            prev_cursor = imgui.get_cursor_pos()
            imgui.set_cursor_pos((prev_cursor.x + (w - img_w) * 0.5, prev_cursor.y))
            imgui.image(self.texture_id, img_w, img_h)
            imgui.set_cursor_pos((prev_cursor.x, prev_cursor.y))
            imgui.dummy(w, h)
        else:
            imgui.image(self.texture_id, w or self.w, h or self.h)

    def _resize_to_fit_keeping_aspect_ratio(self, target: Tuple[float, float]) -> Tuple[float, float]:
        target_w, target_h = target
        aspect_ratio = min(target_w / self.w, target_h / self.h)
        return self.w * aspect_ratio, self.h * aspect_ratio

    @staticmethod
    def create_form(source: Union[str, os.PathLike, bytes, Image]) -> 'Texture':
        if isinstance(source, str) or isinstance(source, os.PathLike):
            return Texture._load_from_path(str(source))
        elif isinstance(source, bytes):
            return Texture._load_from_bytes(source)
        elif isinstance(source, Image):
            return Texture._load_from_image(source)
        else:
            raise ValueError("The argument is not of type str, PathLike, or bytes")

    @staticmethod
    def _load_from_path(p: str) -> 'Texture':
        with Image.open(p) as image:
            return Texture._load_from_image(image)

    @staticmethod
    def _load_from_bytes(image_data: bytes) -> 'Texture':
        with io.BytesIO(image_data) as buffer:
            with Image.open(buffer) as image:
                return Texture._load_from_image(image)

    @staticmethod
    def _load_from_image(image: Image) -> 'Texture':
        image: Image = image.convert("RGB")
        width, height = image.size
        image_data: bytes = image.tobytes()
        texture_id = GL.glGenTextures(1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB, width, height, 0, GL.GL_RGB, GL.GL_UNSIGNED_BYTE, image_data)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        return Texture(texture_id=texture_id, w=width, h=height, mem_size=len(image_data))
