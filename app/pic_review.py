import logging
from pathlib import Path
from typing import Optional

from app.repository import Repository
from app.workspace_mgr import WorkspaceManager

_log = logging.getLogger(__name__)


class PicReview:
    __workspace_path: Optional[Path] = None
    __repo: Repository
    __workspace_manager: WorkspaceManager

    def __init__(self, db_file: Path):
        self.__repo = Repository(db_file)
        self.__workspace_manager = WorkspaceManager(self.__repo)
        _log.info("PicReview backend initialized")

    def get_workspace_dir(self) -> Optional[Path]:
        return self.__workspace_manager.get_workspace_dir()

    def set_workspace_dir(self, path: Path, start_scan: bool = True):
        self.__workspace_manager.set_workspace_dir(path=path, start_scan=start_scan)
