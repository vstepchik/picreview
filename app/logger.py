from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


class MkdirTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    Handler for logging to a file, rotating the log file at certain timed
    intervals.

    If backupCount is > 0, when rollover is done, no more than backupCount
    files are kept - the oldest ones are deleted.
    """
    def __init__(self, filename, *args, **kwargs):
        Path(filename).parent.mkdir(exist_ok=True, parents=True)
        TimedRotatingFileHandler.__init__(self, filename, *args, **kwargs)
