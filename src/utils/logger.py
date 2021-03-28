import logging
import sys

from src.common import inDev
from src.utils.file import File


class DebugLogger(logging.Logger):
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
        lineFormat = '[%(asctime)s %(levelname)s]: %(message)s'
        dateFormat = '%m-%d %H:%M:%S'
        return logging.Formatter(fmt=lineFormat, datefmt=dateFormat)


pathInDev = File('debug-workdir/.minecraft/logs/updater.log')
pathInProd = File(sys.executable).parent.parent('logs/updater.log')
logFile = pathInDev if inDev else pathInProd
logFile.makeParentDirs()
logFile.clear()
logger = DebugLogger(logFile)
logger.info('Log file location: ' + logFile.path)


def info(text):
    logger.info(str(text))
    pass
