import logging
import sys

from src.logging.FilelogFormatter import FilelogFormatter
from src.utils.file import File


class FilelogLogger(logging.Logger):
    def __init__(self, file: File):
        super().__init__(__name__)

        formatter = self.getFormatter()

        self.fileHandler = logging.FileHandler(file.path, encoding="utf-8")
        self.fileHandler.setLevel(logging.DEBUG)
        self.fileHandler.setFormatter(formatter)

        self.addHandler(self.fileHandler)

    @staticmethod
    def getFormatter():
        lineFormat = '[ %(asctime)s {levelname:5s} ] [ {tag:s} ]: %(message)s'
        dateFormat = '%Y-%m-%d %H:%M:%S.$s'
        return FilelogFormatter(fmt=lineFormat, datefmt=dateFormat)
