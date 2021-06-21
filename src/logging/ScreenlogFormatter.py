import logging
import time


class ScreenlogFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super(ScreenlogFormatter, self).__init__(fmt, datefmt, style)

    def formatTime(self, record, datefmt=None):
        converter = time.localtime(record.created)
        if datefmt:
            s = time.strftime(datefmt, converter).replace('$s', '{:03d}'.format(int(record.msecs)))
        else:
            t = time.strftime(self.default_time_format, converter)
            s = self.default_msec_format % (t, record.msecs)
        return s

    def formatMessage(self, record):
        trans = {
            'CRITICAL': '严重',
            'WARNING': '警告',
            'DEBUG': '调试',
            'INFO': '信息',
            'ERROR': '错误'
        }
        if record.levelname in trans:
            record.levelname = trans[record.levelname]

        msg = self._style._fmt.format(**record.__dict__)
        msg = msg % record.__dict__
        return msg
