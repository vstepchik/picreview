#!python3

import logging.config

import yaml

from app.pic_review import PicReview

if __name__ == "__main__":
    with open('logging_cfg.yaml', 'r') as f:
        logging.config.dictConfig(yaml.safe_load(f))
    log = logging.getLogger(__name__)
    log.info("Starting application...")
    pr = PicReview()
    pr.run()
    log.info("Done.")
