import logging
import sys
from collections import namedtuple
from dataclasses import dataclass, field, fields, replace
from datetime import datetime
from io import BytesIO
from pathlib import Path
from sqlite3 import Cursor, Row
from typing import Optional, Self, Tuple

import PIL.Image

from app.utils import sizeof_fmt

_log = logging.getLogger(__name__)


@dataclass(eq=True, frozen=True)
class ImageData:
    workspace_id: int
    path: str

    size: int
    last_updated_at: datetime
    width: int
    height: int

    rank: int
    thumbnail: Optional[bytes] = field(compare=False, hash=False, repr=False, default=None)

    @property
    def dimensions(self):
        return self.width, self.height

    def with_populated_thumbnail(self, thumb_max_size: Tuple[int, int] | int = 64, force_reload: bool = False) -> Self:
        assert type(thumb_max_size) is int \
               or type(thumb_max_size) is tuple, f"thumbnail max size has wrong type: {type(thumb_max_size)}"
        thumb_size = (thumb_max_size, thumb_max_size) if type(thumb_max_size) is int else thumb_max_size
        assert thumb_size[0] > 0, "thumbnail width must be > 0"
        assert thumb_size[1] > 0, "thumbnail height must be > 0"

        if not force_reload and self.thumbnail is not None:
            return self

        try:
            with PIL.Image.open(self.path) as img:
                img.thumbnail(thumb_size)
                img = img.convert(mode='P', palette=PIL.Image.Palette.ADAPTIVE, colors=256)
                img_bytes = BytesIO()
                img.save(img_bytes, 'PNG', optimize=True)
        except FileNotFoundError:
            _log.info(f"File {self.path} not found")
            return None
        except PIL.UnidentifiedImageError as e:
            _log.error(f"Couldn't open image {self.path}", e)
            return None

        _log.debug(f"Populated image with thumbnail, now object size is {sizeof_fmt(self.memory_footprint)}")
        return replace(self, thumbnail=img_bytes.getvalue())

    @property
    def memory_footprint(self) -> int:
        return sum(sys.getsizeof(getattr(self, f.name)) for f in fields(self))

    @staticmethod
    def from_file(path: Path, workspace_id: int, with_thumbnail: bool = True) -> Optional['ImageData']:
        try:
            with PIL.Image.open(path) as img:
                stats = path.stat()
                img_w, img_h = img.size
        except FileNotFoundError:
            _log.info(f"File {path} not found")
            return None
        except PIL.UnidentifiedImageError as e:
            _log.error(f"Couldn't open image {path}", e)
            return None

        image_data = ImageData(
            workspace_id=workspace_id,
            path=str(path),
            size=stats.st_size,
            last_updated_at=datetime.fromtimestamp(stats.st_mtime_ns / 1e9),
            width=img_w,
            height=img_h,
            rank=0,
        )
        return image_data.with_populated_thumbnail() if with_thumbnail else image_data

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
