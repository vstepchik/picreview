import dataclasses
import logging
from collections import namedtuple
from datetime import datetime
from io import BytesIO
from sqlite3 import Cursor, Row
from typing import Optional, Self, Tuple

import PIL.Image

_log = logging.getLogger(__name__)


@dataclasses.dataclass(eq=True, frozen=True)
class ImageData:
    workspace_id: int
    path: str

    size: int
    last_updated_at: datetime
    width: int
    height: int

    rank: int
    thumbnail: Optional[bytes] = None

    @property
    def dimensions(self):
        return self.width, self.height

    def with_populated_thumbnail(self, thumbnail_max_size: Tuple[int, int] | int = 128) -> Self:
        assert thumbnail_max_size is int or thumbnail_max_size is tuple, "thumbnail max size has wrong type"
        thumb_size = (thumbnail_max_size, thumbnail_max_size) if thumbnail_max_size is int else thumbnail_max_size
        assert thumb_size[0] > 0, "thumbnail width must be > 0"
        assert thumb_size[1] > 0, "thumbnail height must be > 0"
        try:
            img: PIL.Image = PIL.Image.open(self.path)
            img.thumbnail(thumbnail_max_size)
            img = img.convert(mode='P', palette=PIL.Image.Palette.ADAPTIVE, colors=256)
            img_bytes = BytesIO()
            img.save(img_bytes, 'PNG', optimize=True)
        except FileNotFoundError:
            _log.info(f"File {self.path} not found")
            return None
        except PIL.UnidentifiedImageError as e:
            _log.error(f"Couldn't open image {self.path}", e)
            return None

        return dataclasses.replace(self, thumbnail=img_bytes.getvalue())

    @staticmethod
    def row_factory(cursor: Cursor, row: Row) -> 'ImageData':
        column_names = [column[0] for column in cursor.description]
        tpl = namedtuple("Row", column_names)(*row)
        return ImageData(
            workspace_id=tpl.workspace_id,
            path=tpl.path,

            size=tpl.size,
            last_updated_at=datetime.fromisoformat(tpl.last_updated_at),
            width=tpl.width,
            height=tpl.height,

            rank=tpl.rank,
            thumbnail=tpl.thumbnail,
        )
