import logging
import sys

from src.logging.UpdaterFormatter import UpdaterFormatter
from src.utils.file import File


class UpdaterLogger(logging.Logger):
    def __init__(self, file: File):
        super().__init__(__name__)

        formatter = self.getFormatter()

        self.fileHandler = logging.FileHandler(file.path, encoding="utf-8")
        self.fileHandler.setLevel(logging.DEBUG)
        self.fileHandler.setFormatter(formatter)

        self.streamHandler = logging.StreamHandler(sys.stdout)
        self.streamHandler.setLevel(logging.INFO)
        self.streamHandler.setFormatter(formatter)

        self.addHandler(self.fileHandler)
        self.addHandler(self.streamHandler)

    @staticmethod
    def getFormatter():
        lineFormat = '[ %(asctime)s {levelname:5s} ] [ {tag:s} ]: %(message)s'
        dateFormat = '%Y-%m-%d %H:%M:%S.$s'
        return UpdaterFormatter(fmt=lineFormat, datefmt=dateFormat)
