import logging
from pathlib import Path
from typing import Optional, List, Dict

from app.model.image_data import ImageData
from app.model.workspace import Workspace
from app.repository import Repository
from app.workspace_mgr import WorkspaceManager

_log = logging.getLogger(__name__)


class PicReview:
    __repo: Repository
    __workspace_manager: WorkspaceManager

    def __init__(self, db_file: Path):
        self.__repo = Repository(db_file)
        self.__workspace_manager = WorkspaceManager(self.__repo)
        _log.info("PicReview backend initialized")

    def get_workspace_dir(self) -> Optional[Path]:
        return self.__workspace_manager.get_current_workspace_dir()

    def create_new_workspace(self, path: Path, name: str, set_current: bool = True) -> Optional[Workspace]:
        _log.debug(f"Adding workspace name: {name}, path: {path}")
        return self.__workspace_manager.create_new_workspace(path=path, name=name, set_current=set_current)

    def set_workspace_as_current(self, ws_id: int, refresh: bool):
        self.__workspace_manager.set_workspace_as_current(ws_id)
        if refresh:
            self.__workspace_manager.refresh_current_workspace()

    def is_workspace_selected(self) -> bool:
        return self.__workspace_manager.get_current_workspace_dir() is not None

    def get_current_workspace(self) -> Optional[Workspace]:
        return self.__workspace_manager.current_workspace

    def get_current_workspace_images(self) -> Optional[List[ImageData]]:
        ws = self.get_current_workspace()
        if ws is None:
            return None
        return self.__repo.get_all_images_for_workspace(ws.id)

    def get_current_workspace_images_rank_histogram(self) -> Optional[Dict[int, int]]:
        ws = self.get_current_workspace()
        if ws is None:
            return None
        return self.__repo.get_image_rank_histogram(ws.id)

    def get_workspaces(self) -> List[Workspace]:
        return self.__repo.get_all_workspaces()

    def rm_workspace(self, ws_id: int):
        self.__workspace_manager.rm_workspace(ws_id)
