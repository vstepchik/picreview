import logging
import os
import platform
from pathlib import Path
from typing import List, Dict, Callable

import imgui

_log = logging.getLogger(__name__)
_TREE_FLAGS = imgui.TREE_NODE_OPEN_ON_ARROW | imgui.TREE_NODE_OPEN_ON_DOUBLE_CLICK


class FileSelector:
    _root: Path
    _roots: List[Path] = []
    _cache: Dict[Path, Dict] = {}
    filter_predicate: Callable[[Path], bool]
    selection: Path
    selection_updated: bool

    def __init__(
            self,
            root: Path = Path(os.path.sep),
            selected: Path = Path().absolute(),
            filter_predicate: Callable[[Path], bool] = lambda _: True,
    ):
        self._root = root
        self._refresh_roots()
        self.filter_predicate = filter_predicate
        self.selection = selected
        self.selection_updated = True
        self._cache = {}

    def _refresh_roots(self):
        if platform.system() == "Windows":
            letters = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
            self._roots = [Path(os.path.abspath(f"{x}:/")) for x in letters if os.path.exists(f"{x}:")]
        else:
            self._roots = [Path(os.path.abspath("/"))]

    def render(self):
        self.selection_updated = False
        for root in self._roots:
            if imgui.tree_node(str(root), _TREE_FLAGS | imgui.TREE_NODE_DEFAULT_OPEN):
                if root not in self._cache:
                    self._cache[root] = self._fill_entries(root)
                self._render_tree(root, self._cache[root])
                imgui.tree_pop()

    def _render_tree(self, current_path: Path, items: Dict[Path, dict]):
        for k, v in items.items():
            this_path_level = current_path.joinpath(k)
            selection_flag = imgui.TREE_NODE_SELECTED if self.selection == k.absolute() else 0
            if k.is_dir():
                if imgui.tree_node(k.name, _TREE_FLAGS | selection_flag):
                    if v is None:
                        entries = self._fill_entries(this_path_level)
                        items[k] = entries
                        self._render_tree(this_path_level, entries)
                    else:
                        self._render_tree(this_path_level, v)
                    imgui.tree_pop()
            else:
                if imgui.tree_node(k.name, _TREE_FLAGS | imgui.TREE_NODE_LEAF | selection_flag):
                    imgui.tree_pop()
            if imgui.is_item_clicked():
                self.selection = k.absolute()
                self.selection_updated = True
                _log.debug(f"New selection: {self.selection}")

    def _fill_entries(self, scan_path: Path) -> Dict[Path, Dict]:
        try:
            return {Path(entry.path): None for entry in os.scandir(scan_path) if self.filter_predicate(Path(entry.path))}
        except PermissionError:
            _log.debug(f"No permission to traverse {scan_path}")
            return {}
