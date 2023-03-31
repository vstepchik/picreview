import logging

_log = logging.getLogger(__name__)


class PicReview:
    def __init__(self):
        _log.info("PicReview initialized")

    def run(self):
        _log.debug(f"Running {self}")
