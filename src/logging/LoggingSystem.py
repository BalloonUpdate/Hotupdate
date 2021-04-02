import sys

from src.common import devDirectory, inDev
from src.logging.UpdaterLogger import UpdaterLogger
from src.utils.file import File


class LoggingSystem:
    pathInDev = File(devDirectory + '/.minecraft/logs/updater.log')
    pathInProd = File(sys.executable).parent.parent('logs/updater.log')

    logger: UpdaterLogger = None

    @classmethod
    def init(cls):
        logFile = cls.pathInDev if inDev else cls.pathInProd
        logFile.makeParentDirs()
        logFile.clear()

        cls.logger = UpdaterLogger(logFile)
        cls.info('LogSys', 'Logging System Initialized, File Location: ' + logFile.path)

    @classmethod
    def debug(cls, tag, msg, *args, **kwargs):
        kwargs['extra'] = {'tag': tag}
        cls.logger.debug(msg, *args, **kwargs)

    @classmethod
    def info(cls, tag, msg, *args, **kwargs):
        kwargs['extra'] = {'tag': tag}
        cls.logger.info(msg, *args, **kwargs)

    @classmethod
    def warning(cls, tag, msg, *args, **kwargs):
        kwargs['extra'] = {'tag': tag}
        cls.logger.warning(msg, *args, **kwargs)

    @classmethod
    def error(cls, tag, msg, *args, **kwargs):
        kwargs['extra'] = {'tag': tag}
        cls.logger.error(msg, *args, **kwargs)

    @classmethod
    def critical(cls, tag, msg, *args, **kwargs):
        kwargs['extra'] = {'tag': tag}
        cls.logger.critical(msg, *args, **kwargs)

    @classmethod
    def exception(cls, tag, msg, *args, **kwargs):
        kwargs['extra'] = {'tag': tag}
        cls.logger.exception(msg, *args, **kwargs)


LogSys = LoggingSystem
