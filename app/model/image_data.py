import dataclasses
from collections import namedtuple
from datetime import datetime
from sqlite3 import Cursor, Row
from typing import Optional


@dataclasses.dataclass(eq=True, frozen=True)
class ImageData:
    workspace_id: int
    path: str

    size: int
    last_updated_at: datetime
    width: int
    height: int

    rank: int
    thumbnail: Optional[bytes]

    @property
    def dimensions(self):
        return self.width, self.height

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
