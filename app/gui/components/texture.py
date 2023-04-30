import dataclasses
import io
import os
from typing import Union

import OpenGL.GL as GL
import imgui
from PIL import Image


@dataclasses.dataclass(frozen=True, eq=True)
class Texture:
    texture_id: int
    w: int
    h: int
    mem_size: int

    def render(self, w: int = None, h: int = None):
        imgui.image(self.texture_id, w or self.w, h or self.h)

    # def __del__(self):
    #     GL.glDeleteTextures(self.texture_id)

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
