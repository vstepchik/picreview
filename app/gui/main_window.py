import logging
import sys
from pathlib import Path
from typing import Optional

import OpenGL.GL as GL
import glfw
import imgui
from app.gui.workspace_selector import WorkspaceSelector
from app.pic_review import PicReview
from imgui.integrations.glfw import GlfwRenderer

_log = logging.getLogger(__name__)


class MainWindow:
    _backend: PicReview
    __window_title: str
    __window_title_postfix: str = ""
    __imgui_ini_file_location: Path
    __window = None

    __started: bool = False

    __show_demo: bool = False
    __show_style_editor: bool = False
    __show_metrics: bool = False

    __workspace_selector: WorkspaceSelector

    def __init__(self, window_title: str, backend: PicReview, imgui_ini_file_location: Path = Path("imgui.ini")):
        self.__window_title = window_title
        self.__imgui_ini_file_location = imgui_ini_file_location.absolute()
        self._backend = backend

    def update_title(self, title: Optional[str] = None, postfix: Optional[str] = None):
        if title is not None:
            self.__window_title = title
        if postfix is not None:
            self.__window_title_postfix = postfix
        glfw.set_window_title(self.__window, self.__window_title + self.__window_title_postfix)

    def show(self):
        if self.__started:
            _log.warning("Window has been shown already")
            return

        _log.info("Initializing GUI")
        self.__window = MainWindow.__glfw_init_window(self.__window_title)
        imgui.create_context()
        imgui.get_io().ini_file_name = str(self.__imgui_ini_file_location).encode()
        _log.debug(f"imgui ini file location: {imgui.get_io().ini_file_name}")
        window_renderer = GlfwRenderer(self.__window)
        self.__workspace_selector = WorkspaceSelector(self._backend)
        _log.debug("GUI init done")
        self.__started = True

        _log.info("Starting GUI")
        while not glfw.window_should_close(self.__window):
            glfw.poll_events()
            window_renderer.process_inputs()

            imgui.new_frame()

            self.__main_menu_bar()
            self.__draw_windows()

            if self.__show_demo:
                imgui.show_test_window()
            if self.__show_style_editor:
                imgui.show_style_editor()
            if self.__show_metrics:
                imgui.show_metrics_window()

            GL.glClearColor(0.11, 0.11, 0.09, 1)
            GL.glClear(GL.GL_COLOR_BUFFER_BIT)

            imgui.render()
            try:
                window_renderer.render(imgui.get_draw_data())
            except GL.error.GLError as e:
                _log.error(e)
            glfw.swap_buffers(self.__window)

        window_renderer.shutdown()
        glfw.terminate()

    def __main_menu_bar(self):
        if imgui.begin_main_menu_bar():
            if imgui.begin_menu("File", True):
                clicked_quit, _selected_quit = imgui.menu_item("Quit")

                if clicked_quit:
                    glfw.set_window_should_close(self.__window, True)

                imgui.end_menu()

            if imgui.begin_menu("Help", True):
                clicked_demo, _ = imgui.menu_item("imgui demo", None, self.__show_demo)
                clicked_style_editor, _ = imgui.menu_item("style editor", None, self.__show_style_editor)
                clicked_metrics, _ = imgui.menu_item("imgui metrics", None, self.__show_metrics)

                if clicked_demo:
                    self.__show_demo = not self.__show_demo

                if clicked_style_editor:
                    self.__show_style_editor = not self.__show_style_editor

                if clicked_metrics:
                    self.__show_metrics = not self.__show_metrics

                imgui.end_menu()

            imgui.end_main_menu_bar()

    def __draw_windows(self):
        if self._backend.get_workspace_dir() is None:
            self.__workspace_selector.render()
            ws_path = self._backend.get_workspace_dir()
            if ws_path is not None:
                window_postfix = f" :: {ws_path}" if ws_path is not None else ""
                if window_postfix != self.__window_title_postfix:
                    self.update_title(postfix=window_postfix)
        else:
            imgui.set_next_window_size(0, 0)
            with imgui.begin(
                "Fullscreen Wnd",
                False,
                imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE,
            ):
                imgui.text(str(self._backend.get_workspace_dir()))

    @staticmethod
    def __glfw_init_window(window_title: str):
        width, height = 1920, 1080  # 3840, 2160

        if not glfw.init():
            _log.fatal("Could not initialize OpenGL context")
            sys.exit(1)

        monitor = glfw.get_primary_monitor()
        video_mode = glfw.get_video_mode(monitor)
        monitor_width_mm, monitor_height_mm = glfw.get_monitor_physical_size(monitor)
        mm_per_inch = 25.4
        dpi = video_mode.size.width / (monitor_width_mm / mm_per_inch)
        _log.debug(f"video_mode: {video_mode}, dpi: {dpi}")

        # OS X supports only forward-compatible core profiles from 3.2
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.window_hint(glfw.MAXIMIZED, GL.GL_TRUE)

        # Create a windowed mode window and its OpenGL context
        window = glfw.create_window(int(width), int(height), window_title, None, None)
        glfw.make_context_current(window)

        if not window:
            glfw.terminate()
            _log.fatal("Could not initialize Window")
            sys.exit(2)

        return window
