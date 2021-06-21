import sys

from src.common import devDirectory, inDev
from src.logging.FilelogLogger import FilelogLogger
from src.logging.ScreenlogLogger import ScreenlogLogger
from src.utils.file import File


class LoggingSystem:
    pathInDev = File(devDirectory + '/.minecraft/logs/updater.log')
    pathInProd = File(sys.executable).parent.parent('logs/updater.log')

    filelogger: FilelogLogger = None
    screenlogger: ScreenlogLogger = None

    @classmethod
    def init(cls):
        logFile = cls.pathInDev if inDev else cls.pathInProd
        logFile.makeParentDirs()
        logFile.clear()

        cls.filelogger = FilelogLogger(logFile)
        cls.screenlogger = ScreenlogLogger()

        cls.if_('LogSys', 'Logging System Initialized, File Location: ' + logFile.path)

    @classmethod
    def getLoggers2(cls, kwargs: dict):
        if 'on_screen' in kwargs:
            return [cls.screenlogger] if kwargs['on_screen'] else [cls.filelogger]
        return [cls.screenlogger, cls.filelogger]

    @classmethod
    def remove_onscreen(cls, kwargs):
        if 'on_screen' in kwargs:
            del kwargs['on_screen']
        return kwargs

    @classmethod
    def debug(cls, tag, msg, *args, **kwargs):
        kwargs['extra'] = {'tag': tag}
        for lgr in cls.getLoggers2(kwargs):
            lgr.debug(msg, *args, **cls.remove_onscreen(kwargs))

    @classmethod
    def info(cls, tag, msg, *args, **kwargs):
        kwargs['extra'] = {'tag': tag}
        for lgr in cls.getLoggers2(kwargs):
            lgr.info(msg, *args, **cls.remove_onscreen(kwargs))

    @classmethod
    def warning(cls, tag, msg, *args, **kwargs):
        kwargs['extra'] = {'tag': tag}
        for lgr in cls.getLoggers2(kwargs):
            lgr.warning(msg, *args, **cls.remove_onscreen(kwargs))

    @classmethod
    def error(cls, tag, msg, *args, **kwargs):
        kwargs['extra'] = {'tag': tag}
        for lgr in cls.getLoggers2(kwargs):
            lgr.error(msg, *args, **cls.remove_onscreen(kwargs))

    @classmethod
    def critical(cls, tag, msg, *args, **kwargs):
        kwargs['extra'] = {'tag': tag}
        for lgr in cls.getLoggers2(kwargs):
            lgr.critical(msg, *args, **cls.remove_onscreen(kwargs))

    @classmethod
    def df(cls, tag, msg):
        cls.debug(tag, msg, on_screen=False)

    @classmethod
    def ds(cls, tag, msg=None):
        if msg is None:
            msg = tag
            tag = ''
        cls.debug(tag, msg, on_screen=True)

    @classmethod
    def if_(cls, tag, msg):
        cls.info(tag, msg, on_screen=False)

    @classmethod
    def is_(cls, tag, msg=None):
        if msg is None:
            msg = tag
            tag = ''
        cls.info(tag, msg, on_screen=True)

    @classmethod
    def wf(cls, tag, msg):
        cls.warning(tag, msg, on_screen=False)

    @classmethod
    def ws(cls, tag, msg=None):
        if msg is None:
            msg = tag
            tag = ''
        cls.warning(tag, msg, on_screen=True)

    @classmethod
    def ef(cls, tag, msg):
        cls.error(tag, msg, on_screen=False)

    @classmethod
    def es(cls, tag, msg=None):
        if msg is None:
            msg = tag
            tag = ''
        cls.error(tag, msg, on_screen=True)

    @classmethod
    def cf(cls, tag, msg):
        cls.critical(tag, msg, on_screen=False)

    @classmethod
    def cs(cls, tag, msg=None):
        if msg is None:
            msg = tag
            tag = ''
        cls.critical(tag, msg, on_screen=True)

LogSys = LoggingSystem
