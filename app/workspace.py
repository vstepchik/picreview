import logging
import os
from datetime import timedelta
from pathlib import Path
from time import time
from typing import Optional

_log = logging.getLogger(__name__)


class WorkspaceManager:
    # todo: watch workspace path and update on changes
    __workspace_path: Optional[Path] = None

    def __init__(self):
        _log.info("PicReview backend initialized")

    def get_workspace_dir(self) -> Optional[Path]:
        return self.__workspace_path

    def set_workspace_dir(self, path: Path, start_scan: bool = True):
        path = path.absolute()
        if not path.is_dir():
            logging.warning(f"{path} is not a directory")
            return

        self.__workspace_path = path
        _log.info(f"New workspace dir: {path}")
        if start_scan:
            self.scan_workspace()

    def scan_workspace(self):
        ws_path = self.__workspace_path
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

    @staticmethod
    def find_images(scan_path: Path):
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
        for entry in os.scandir(scan_path):
            if entry.is_dir():
                yield from WorkspaceManager.find_images(entry.path)
            elif entry.is_file() and entry.name.lower().endswith(image_extensions):
                yield entry.path
