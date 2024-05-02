import contextlib
import logging
import os
import sys


_fmt = ('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_datefmt = '%Y%m%d_%H%M%S'


class _ColorFormatter(logging.Formatter):

    GREY = '\x1b[38;21m'
    BLUE = '\x1b[34;21m'
    GREEN = '\x1b[32;21m'
    YELLOW = '\x1b[33;21m'
    RED = '\x1b[31;21m'
    BOLD_RED = '\x1b[31;1m'
    RESET = '\x1b[0m'

    LEVEL_TO_COLOR = {
        logging.DEBUG: GREY,
        logging.INFO: BLUE,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED,
    }

    def __init__(self, fmt, datefmt=None):
      self._formatters = {
          level: logging.Formatter(color + fmt + self.RESET, datefmt=datefmt)
          for level, color in self.LEVEL_TO_COLOR.items()
      }

    def format(self, record):
      self._formatters[record.levelno].format(record)


def setup_logging(colorize=False):
  logger = logging.getLogger()
  logger.setLevel(logging.DEBUG)
  sh = logging.StreamHandler(sys.stdout)
  sh.setLevel(logging.DEBUG)
  if colorize:
    sh.setFormatter(_ColorFormatter(_fmt, datefmt=_datefmt))
  else:
    sh.setFormatter(logging.Formatter(_fmt, datefmt=_datefmt))
  logger.addHandler(sh)


@contextlib.contextmanager
def log_to(log_path):
  logger = logging.getLogger()
  fh = logging.FileHandler(log_path)
  fh.setLevel(logging.DEBUG)
  fh.setFormatter(logging.Formatter(_fmt, datefmt=_datefmt))
  logger.addHandler(fh)
  try:
    yield
  finally:
    logger.removeHandler(fh)
