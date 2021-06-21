import logging
import sys

from src.logging.ScreenlogFormatter import ScreenlogFormatter
from src.utils.file import File


class ScreenlogLogger(logging.Logger):
    def __init__(self):
        super().__init__(__name__)

        formatter = self.getFormatter()

        self.streamHandler = logging.StreamHandler(sys.stdout)
        self.streamHandler.setLevel(logging.DEBUG)
        self.streamHandler.setFormatter(formatter)

        self.addHandler(self.streamHandler)

    @staticmethod
    def getFormatter():
        # lineFormat = '[{levelname:5s}] [{tag:s}] : %(message)s'
        lineFormat = '[{levelname:2s}]: %(message)s'
        dateFormat = '%Y-%m-%d %H:%M:%S.$s'
        return ScreenlogFormatter(fmt=lineFormat, datefmt=dateFormat)
