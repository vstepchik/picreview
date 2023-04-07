import datetime
import logging
import os
from datetime import timedelta, datetime
from pathlib import Path
from time import time
from typing import Optional

import PIL.Image

from app.model.image_data import ImageData
from app.model.workspace import Workspace
from app.repository import Repository

_log = logging.getLogger(__name__)


class WorkspaceManager:
    # todo: watch workspace path and update on changes
    __current_workspace: Optional[Workspace] = None
    __repository: Repository

    def __init__(self, repo: Repository):
        self.__repository = repo
        _log.info("PicReview backend initialized")

    def get_current_workspace_dir(self) -> Optional[Workspace]:
        return Path(self.__current_workspace.path) if self.__current_workspace is not None else None

    def set_workspace_as_current(self, ws_id: Optional[int]):
        self.__current_workspace = self.__repository.get_workspace(ws_id) if ws_id else None
        if self.__current_workspace is not None:
            _log.info(f"New workspace dir: {self.__current_workspace.path}")
        else:
            _log.info(f"Workspace closed")

    def create_new_workspace(self, path: Path, name: str, start_scan: bool = True) -> Optional[Workspace]:
        path = path.absolute()
        if not path.is_dir():
            logging.warning(f"{path} is not a directory")
            return None

        ws = Workspace(
            id=None,
            name=name,
            path=str(path),
            last_used_at=datetime.datetime.now(),
        )
        self.__repository.persist_workspace(ws)
        if start_scan:
            self.scan_current_workspace()
        return ws

    def rm_workspace(self, ws_id: int):
        if self.__current_workspace is not None and self.__current_workspace.id == ws_id:
            self.__current_workspace = None
        self.__repository.rm_workspace(ws_id)

    def scan_current_workspace(self):
        if self.__current_workspace is None:
            _log.debug("No workspace - no scan")
            return
        ws_path = Path(self.__current_workspace.path)
        if ws_path is None:
            _log.warning("No current workspace set")
            return
        if not ws_path.exists():
            _log.warning(f"Current workspace dir does not exist: {ws_path}")
            return
        if not ws_path.is_dir():
            _log.warning(f"Current workspace is not a directory: {ws_path}")
            return

        _log.info(f"Scanning workspace...")
        t = time()
        image_files = sorted(set(WorkspaceManager.find_images(ws_path)))
        _log.info(f"{len(image_files)} images found in workspace in {timedelta(seconds=time() - t)}")

    def import_image(self, ws_id: int, path: Path) -> Optional[ImageData]:
        try:
            img: PIL.Image = PIL.Image.open(path)
            stats = path.stat()
            img_w, img_h = img.size
        except FileNotFoundError:
            _log.info(f"File {path} not found")
            return None
        except PIL.UnidentifiedImageError as e:
            _log.error(f"Couldn't open image {path}", e)
            return None

        return ImageData(
            workspace_id=ws_id,
            path=str(path),
            size=stats.st_size,
            last_updated_at=datetime.fromtimestamp(stats.st_mtime_ns / 1e9),
            width=img_w,
            height=img_h,
            rank=0,
        ).with_populated_thumbnail()

    @staticmethod
    def find_images(scan_path: Path):
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
        for entry in os.scandir(scan_path):
            try:
                if entry.is_dir():
                    yield from WorkspaceManager.find_images(entry.path)
                elif entry.is_file() and entry.name.lower().endswith(image_extensions):
                    yield entry.path
            except PermissionError:
                _log.debug(f"No permission to read {entry} - skipping")
