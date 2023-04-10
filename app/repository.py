import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from sqlite3 import Error, Connection
from typing import List, Optional, Any, Tuple

from app.model.image_data import ImageData
from app.model.workspace import Workspace

_log = logging.getLogger(__name__)


class Repository:
    __connection: Connection = None

    def __init__(self, db_file: Path):
        try:
            self.__connection = sqlite3.connect(db_file)
            _log.debug(f"Using sqlite version {sqlite3.version}")
            self._ensure_schema()
        except Error as e:
            _log.error("Couldn't connect to the database", exc_info=e)
            raise e

    def __del__(self):
        if self.__connection is not None:
            self.__connection.close()
            del self.__connection

    def _ensure_schema(self):
        _log.debug("Ensuring schema is initialized")
        cur = self.__connection.cursor()
        cur.execute("PRAGMA foreign_keys = ON;")
        try:
            cur.executescript(SQL_CREATE_WORKSPACE_TABLE)
            cur.executescript(SQL_CREATE_IMAGE_TABLE)
            cur.connection.commit()
        finally:
            cur.close()

    @staticmethod
    def _dataclass_to_upsert_query(table_name: str, obj: Any) -> Tuple[str, Tuple[Any]]:
        # Convert the dataclass object to a dictionary
        workspace_dict = vars(obj)

        column_names = ', '.join(workspace_dict.keys())
        placeholders = ', '.join('?' * len(workspace_dict))
        query = f"INSERT OR REPLACE INTO {table_name} ({column_names}) VALUES ({placeholders})"
        return query, tuple(workspace_dict.values())

    # WORKSPACE #

    def get_all_workspaces(self) -> List[Workspace]:
        cur = self.__connection.cursor()
        cur.row_factory = Workspace.row_factory
        try:
            cur.execute("SELECT * FROM workspace ORDER BY last_used_at DESC, name ASC")
            return cur.fetchall()
        finally:
            cur.close()

    def get_workspace(self, id_pk: int) -> Optional[Workspace]:
        cur = self.__connection.cursor()
        cur.row_factory = Workspace.row_factory
        try:
            cur.execute("SELECT * FROM workspace WHERE id=?", (id_pk,))
            return cur.fetchone()
        finally:
            cur.close()

    def persist_workspace(self, obj: Workspace) -> Workspace:
        cur = self.__connection.cursor()
        cur.row_factory = Workspace.row_factory
        try:
            query, values = self._dataclass_to_upsert_query("workspace", obj)
            cur.execute(query, values)
            cur.connection.commit()
            # Retrieve the just inserted record
            cur.execute("SELECT * FROM workspace WHERE rowid=?", (cur.lastrowid,))
            return cur.fetchone()
        finally:
            cur.close()

    def rm_workspace(self, id_pk: int):
        cur = self.__connection.cursor()
        try:
            cur.execute("DELETE FROM workspace WHERE id=?", (id_pk,))
            cur.connection.commit()
        finally:
            cur.close()

    # IMAGE DATA #

    def get_all_images_for_workspace(self, workspace_id: int) -> List[ImageData]:
        cur = self.__connection.cursor()
        cur.row_factory = ImageData.row_factory
        try:
            query = "SELECT * FROM image_data WHERE workspace_id=? ORDER BY workspace_id ASC, path ASC"
            cur.execute(query, (workspace_id,))
            return cur.fetchall()
        finally:
            cur.close()

    def get_image(self, workspace_id: int, path: str) -> Optional[ImageData]:
        cur = self.__connection.cursor()
        cur.row_factory = ImageData.row_factory
        try:
            cur.execute("SELECT * FROM image_data WHERE workspace_id=? AND path=?", (workspace_id, path))
            return cur.fetchone()
        finally:
            cur.close()

    def is_image_outdated(self, workspace_id: int, path: str, last_updated_at: datetime) -> bool:
        cur = self.__connection.cursor()
        cur.row_factory = ImageData.row_factory
        try:
            query = "SELECT * FROM image_data WHERE workspace_id=? AND path=? AND last_updated_at >= ?"
            cur.execute(query, (workspace_id, path, last_updated_at))
            return cur.fetchone() is None
        finally:
            cur.close()

    def persist_image(self, obj: ImageData) -> ImageData:
        cur = self.__connection.cursor()
        cur.row_factory = ImageData.row_factory
        try:
            query, values = self._dataclass_to_upsert_query("image_data", obj)
            cur.execute(query, values)
            cur.connection.commit()
            # Retrieve the just inserted record
            cur.execute("SELECT * FROM image_data WHERE rowid=?", (cur.lastrowid,))
            return cur.fetchone()
        finally:
            cur.close()

    def rm_image(self, workspace_id: int, path: str):
        cur = self.__connection.cursor()
        try:
            cur.execute("DELETE FROM image_data WHERE workspace_id=? AND path=?", (workspace_id, path))
            cur.connection.commit()
        finally:
            cur.close()


SQL_CREATE_WORKSPACE_TABLE = """
CREATE TABLE IF NOT EXISTS workspace (
    id              integer PRIMARY KEY AUTOINCREMENT,
    name            text    NOT NULL,
    path            text    NOT NULL,
    last_used_at    text
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_workspace_name
ON workspace(name);
CREATE INDEX IF NOT EXISTS        idx_workspace_last_used_at
ON workspace(last_used_at);
"""

SQL_CREATE_IMAGE_TABLE = """
CREATE TABLE IF NOT EXISTS image_data (
    workspace_id    integer NOT NULL,
    path            text    NOT NULL,
    
    size            integer NOT NULL,
    last_updated_at text    NOT NULL,
    width           integer NOT NULL,
    height          integer NOT NULL,
    thumbnail       blob    NULL,
    rank            integer DEFAULT 0 NOT NULL,
    
    PRIMARY KEY     (workspace_id, path),
    CONSTRAINT      fk_workspace
        FOREIGN KEY (workspace_id)
        REFERENCES  workspace(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS        idx_image_data_path
ON image_data(path);
CREATE INDEX IF NOT EXISTS        idx_image_data_last_updated_at
ON image_data(last_updated_at);
CREATE INDEX IF NOT EXISTS        idx_image_data_rank
ON image_data(rank);
"""
