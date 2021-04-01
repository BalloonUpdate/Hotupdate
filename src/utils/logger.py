import logging
import sys
import time

from src.common import inDev
from src.utils.file import File


class DebugFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super(DebugFormatter, self).__init__(fmt, datefmt, style)

    def formatTime(self, record, datefmt=None):
        converter = time.localtime(record.created)
        if datefmt:
            s = time.strftime(datefmt, converter).replace('$s', '{:03d}'.format(int(record.msecs)))
        else:
            t = time.strftime(self.default_time_format, converter)
            s = self.default_msec_format % (t, record.msecs)
        return s

    def formatMessage(self, record):
        trans = {'CRITICAL': 'CRIT','WARNING': 'WARN',}
        if record.levelname in trans:
            record.levelname = trans[record.levelname]

        msg = self._style._fmt.format(**record.__dict__)
        msg = msg % record.__dict__
        return msg

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
        lineFormat = '[%(asctime)s {levelname:5s}]: %(message)s'
        dateFormat = '%Y-%m-%d %H:%M:%S:$s'
        return DebugFormatter(fmt=lineFormat, datefmt=dateFormat)


pathInDev = File('debug-workdir/.minecraft/logs/updater.log')
pathInProd = File(sys.executable).parent.parent('logs/updater.log')
logFile = pathInDev if inDev else pathInProd
logFile.makeParentDirs()
logFile.clear()
logger = DebugLogger(logFile)
logger.info('Log file location: ' + logFile.path)


def info(text):
    logger.info(str(text))
