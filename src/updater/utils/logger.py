import logging
import sys

from src.updater.common import inDevelopment
from src.updater.utils.file import File


class DebugLogger(logging.Logger):
    def __init__(self, file: File):
        super().__init__(__name__)

        formatter = self.getFormatter()

        self.fileHandler = logging.FileHandler(file.path, encoding="utf-8")
        self.fileHandler.setLevel(logging.INFO)
        self.fileHandler.setFormatter(formatter)

        self.streamHandler = logging.StreamHandler(sys.stdout)
        self.streamHandler.setLevel(logging.INFO)
        self.streamHandler.setFormatter(formatter)

        self.addHandler(self.fileHandler)
        self.addHandler(self.streamHandler)

    @staticmethod
    def getFormatter():
        lineFormat = '[%(asctime)s %(levelname)s]: %(message)s'
        dateFormat = '%m-%d %H:%M:%S'
        return logging.Formatter(fmt=lineFormat, datefmt=dateFormat)


logFile = File(sys.executable).parent.parent('logs/updater.log') if not inDevelopment else File('updater.log')
logFile.clear()
logger = DebugLogger(logFile)
logger.info('log file location: '+logFile.path)


def info(text):
    logger.info(str(text))