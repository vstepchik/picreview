import logging
from pathlib import Path
from typing import Optional

from app.workspace import WorkspaceManager

_log = logging.getLogger(__name__)


class PicReview:
    __workspace_path: Optional[Path] = None
    __workspace_manager: WorkspaceManager

    def __init__(self):
        self.__workspace_manager = WorkspaceManager()
        _log.info("PicReview backend initialized")

    def get_workspace_dir(self) -> Optional[Path]:
        return self.__workspace_manager.get_workspace_dir()

    def set_workspace_dir(self, path: Path, start_scan: bool = True):
        self.__workspace_manager.set_workspace_dir(path=path, start_scan=start_scan)
