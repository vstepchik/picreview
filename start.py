#!python3

import logging.config
from pathlib import Path

import yaml

import app
from app.gui.main_window import MainWindow
from app.pic_review import PicReview

USERDATA_PATH = Path("./userdata")

if __name__ == "__main__":
    with open('logging_cfg.yaml', 'r') as f:
        logging.config.dictConfig(yaml.safe_load(f))
    log = logging.getLogger(__name__)
    log.info("Starting application...")
    backend = PicReview(USERDATA_PATH.joinpath("database.sqlite3"))
    main_window = MainWindow(
        window_title=f"PicReview v{app.__version__}",
        backend=backend,
        imgui_ini_file_location=USERDATA_PATH.joinpath("imgui.ini"),
    )
    main_window.show()
    log.info("Done.\n")
