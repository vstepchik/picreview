import dataclasses
from collections import namedtuple
from datetime import datetime
from sqlite3 import Cursor, Row
from typing import Optional


@dataclasses.dataclass(eq=True, frozen=True)
class Workspace:
    id: Optional[int]
    name: str
    path: str
    last_used_at: Optional[datetime]

    @staticmethod
    def row_factory(cursor: Cursor, row: Row) -> 'Workspace':
        column_names = [column[0] for column in cursor.description]
        tpl = namedtuple("Row", column_names)(*row)
        return Workspace(
            id=tpl.id,
            name=tpl.name,
            path=tpl.path,
            last_used_at=datetime.fromisoformat(tpl.last_used_at),
        )
