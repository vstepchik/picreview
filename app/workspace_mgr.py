import datetime
import logging
import os
from dataclasses import dataclass, replace
from datetime import timedelta, datetime
from pathlib import Path
from time import time
from typing import Optional, List, Set, Dict

from app.model.image_data import ImageData
from app.model.workspace import Workspace
from app.repository import Repository

_log = logging.getLogger(__name__)


class WorkspaceManager:
    # todo: watch workspace path and update on changes
    __current_workspace: Optional[Workspace] = None
    __repository: Repository

    @dataclass(frozen=True)
    class WorkspaceRescanDelta:
        files_missing: List[Path]
        files_updated: List[Path]

    def __init__(self, repo: Repository):
        self.__repository = repo
        _log.info("PicReview backend initialized")

    @property
    def current_workspace(self) -> Optional[Workspace]:
        return self.__current_workspace

    def get_current_workspace_dir(self) -> Optional[Workspace]:
        return Path(self.__current_workspace.path) if self.__current_workspace is not None else None

    def set_workspace_as_current(self, ws_id: Optional[int]):
        self.__current_workspace = self.__repository.get_workspace(ws_id) if ws_id else None
        if self.__current_workspace is not None:
            _log.info(f"New workspace dir: {self.__current_workspace.path}")
        else:
            _log.info(f"Workspace closed")

    def create_new_workspace(self, path: Path, name: str, set_current: bool = True) -> Optional[Workspace]:
        path = path.absolute()
        if not path.is_dir():
            logging.warning(f"{path} is not a directory")
            return None

        ws = Workspace(
            id=None,
            name=name,
            path=str(path),
            last_used_at=datetime.now(),
        )
        ws = self.__repository.persist_workspace(ws)
        if set_current:
            self.__current_workspace = ws
            self.refresh_current_workspace()
        return ws

    def rm_workspace(self, ws_id: int):
        if self.__current_workspace is not None and self.__current_workspace.id == ws_id:
            self.__current_workspace = None
        self.__repository.rm_workspace(ws_id)

    def refresh_current_workspace(self):
        if self.__current_workspace is None:
            _log.info("No workspace - do nothing")
            return
        ws_id = self.__current_workspace.id
        delta = self._rescan_current_workspace_and_get_delta()
        _log.info(f"Scan results: -{len(delta.files_missing)} +{len(delta.files_updated)}")

        for f in delta.files_updated:
            img_data = ImageData.from_file(workspace_id=ws_id, path=f)
            existing_image = self.__repository.get_image(ws_id, str(f))
            if existing_image is not None:  # keep image rank if the image already existed in the workspace
                img_data = replace(img_data, rank=existing_image.rank)
            self.__repository.persist_image(img_data)
        for f in delta.files_missing:
            self.__repository.rm_image(workspace_id=ws_id, path=str(f))

    def _rescan_current_workspace_and_get_delta(self) -> Optional[WorkspaceRescanDelta]:
        if self.__current_workspace is None:
            _log.info("No workspace - no delta")
            return
        ws_id = self.__current_workspace.id
        image_paths_found: List[Path] = self._scan_current_workspace()
        image_data_in_db: List[ImageData] = self.__repository.get_all_images_for_workspace(workspace_id=ws_id)
        unprocessed_paths_in_workspace: Dict[Path, ImageData] = {
            Path(i.path): i for i in image_data_in_db
        }
        updated_image_paths: Set[Path] = set()
        for img_path in image_paths_found:
            i = ImageData.from_file(img_path, ws_id, with_thumbnail=False)
            if i is None:
                _log.warning(f"Image found but could not be read: {img_path}")
            elif self.__repository.is_image_outdated(ws_id, str(img_path), i.last_updated_at):
                _log.info(f"Found updated image: {img_path}")
                updated_image_paths.add(img_path)
                unprocessed_paths_in_workspace.pop(img_path, None)
            else:
                _log.debug(f"Image {img_path} is up to date")
                unprocessed_paths_in_workspace.pop(img_path, None)

        return WorkspaceManager.WorkspaceRescanDelta(
            files_missing=sorted(Path(p) for p in unprocessed_paths_in_workspace.keys()),
            files_updated=sorted(Path(p) for p in updated_image_paths),
        )

    def _scan_current_workspace(self) -> Optional[List[Path]]:
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
        image_files: List[Path] = sorted(Path(p) for p in set(WorkspaceManager._find_images(ws_path)))
        _log.info(f"{len(image_files)} images found in workspace in {timedelta(seconds=time() - t)}")
        return image_files

    @staticmethod
    def _find_images(scan_path: Path):
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff')
        for entry in os.scandir(scan_path):
            try:
                if entry.is_dir():
                    yield from WorkspaceManager._find_images(entry.path)
                elif entry.is_file() and entry.name.lower().endswith(image_extensions):
                    yield entry.path
            except PermissionError:
                _log.debug(f"No permission to read {entry} - skipping")
