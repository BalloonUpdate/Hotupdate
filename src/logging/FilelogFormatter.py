import logging
import time


class FilelogFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, style='%'):
        super(FilelogFormatter, self).__init__(fmt, datefmt, style)

    def formatTime(self, record, datefmt=None):
        converter = time.localtime(record.created)
        if datefmt:
            s = time.strftime(datefmt, converter).replace('$s', '{:03d}'.format(int(record.msecs)))
        else:
            t = time.strftime(self.default_time_format, converter)
            s = self.default_msec_format % (t, record.msecs)
        return s

    def formatMessage(self, record):
        trans = {'CRITICAL': 'CRIT', 'WARNING': 'WARN', }
        if record.levelname in trans:
            record.levelname = trans[record.levelname]

        msg = self._style._fmt.format(**record.__dict__)
        msg = msg % record.__dict__
        return msg
