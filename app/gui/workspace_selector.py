import logging
from pathlib import Path
from typing import Optional, List

import imgui

from app.gui.file_selector import FileSelector
from app.model.workspace import Workspace
from app.pic_review import PicReview

_log = logging.getLogger(__name__)
_BTN_WIDTH = 80


class WorkspaceSelector:
    _backend: PicReview

    _selected_ws_id: Optional[int] = None
    # create modal
    _input_path: str = ""
    _input_name: str = ""
    _show_create_dialog: bool = False
    _file_selector: FileSelector = FileSelector(filter_predicate=lambda path: path.is_dir())
    # delete modal
    _show_delete_ws_id: Optional[int] = None

    _workspaces: List[Workspace] = []

    def __init__(self, backend: PicReview) -> None:
        self._backend = backend
        self.refresh_data()

    def refresh_data(self):
        _log.debug("Refreshing workspaces")
        self._workspaces = self._backend.get_workspaces()
        if len(self._workspaces) > 0:
            self._selected_ws_id = self._workspaces[0].id

    def render(self):
        w, h = imgui.get_io().display_size
        imgui.set_next_window_position(w / 2, h / 2, imgui.APPEARING, 0.5, 0.5)
        opened = imgui.begin("Select workspace", False, imgui.WINDOW_ALWAYS_AUTO_RESIZE | imgui.WINDOW_NO_COLLAPSE)
        if opened:
            for ws in self._workspaces:
                opened, selected = imgui.selectable(ws.name, selected=ws.id == self._selected_ws_id)
                if opened:
                    self._selected_ws_id = ws.id
                imgui.same_line(300)
                imgui.text(ws.path)

            imgui.separator()
            if imgui.button("New", _BTN_WIDTH):
                self._show_create_dialog = True
            if self._selected_ws_id is not None:
                imgui.same_line(0, _BTN_WIDTH)
                if imgui.button("Open", _BTN_WIDTH):
                    self._backend.set_workspace_as_current(self._selected_ws_id, refresh=True)
                imgui.same_line()
                if imgui.button("Delete", _BTN_WIDTH):
                    self._show_delete_ws_id = self._selected_ws_id

            imgui.end()

        if self._show_create_dialog:
            self._render_ws_create_dialog()
        ws_to_delete = next((ws for ws in self._workspaces if ws.id == self._show_delete_ws_id), None)
        if ws_to_delete is not None:
            self._render_ws_delete_dialog(ws_to_delete)

    def _render_ws_delete_dialog(self, ws: Workspace):
        title = "Delete workspace?"
        imgui.open_popup(title)
        opened, visible = imgui.begin_popup_modal(
            title,
            True,
            imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_ALWAYS_AUTO_RESIZE,
        )
        if opened:
            imgui.text(f"name: {ws.name}")
            imgui.text(f"path: {ws.path}")
            imgui.text(f"last used: {ws.last_used_at}")
            imgui.separator()
            if imgui.button("Yes", _BTN_WIDTH):
                self._backend.rm_workspace(ws.id)
                self._hide_ws_delete_dialog()
                self.clear_ws_selection()
                self.refresh_data()
            imgui.same_line(0, 40)
            if imgui.button("No", _BTN_WIDTH):
                self._hide_ws_delete_dialog()
            imgui.end_popup()
        else:  # cross button clicked
            self._hide_ws_delete_dialog()

    def _hide_ws_delete_dialog(self):
        self._show_delete_ws_id = None

    def _render_ws_create_dialog(self):
        title = "Create workspace"
        imgui.open_popup(title)
        imgui.set_next_window_size(480, 640, imgui.FIRST_USE_EVER)
        opened, visible = imgui.begin_popup_modal(
            title,
            True,
        )
        if opened:
            imgui.begin_child("Work dir select", -1, -100, True)
            self._file_selector.render()
            if self._file_selector.selection_updated:
                self._input_path = str(self._file_selector.selection.absolute())
            imgui.end_child()
            _, self._input_path = imgui.input_text("Path", self._input_path, 1024)
            _, self._input_name = imgui.input_text("Name", self._input_name, 40)
            if imgui.button("Create", _BTN_WIDTH) and self._input_name.strip() != "":
                self._backend.create_new_workspace(Path(self._input_path), self._input_name.strip())
                self._input_name = ""
                self._hide_ws_create_dialog()
                self.refresh_data()
            imgui.end_popup()
        else:  # cross button clicked
            self._hide_ws_create_dialog()

    def _hide_ws_create_dialog(self):
        self._show_create_dialog = False

    def clear_ws_selection(self):
        self._selected_ws_id = None
