import json
import logging
import subprocess
import sys
import threading
import time
import traceback
import webview
from cefpython3.cefpython_py37 import LOGSEVERITY_INFO, LOGSEVERITY_ERROR

from webview import Window

from src.common import inDev
from src.utils.logger import info, logger
from webview.platforms.cef import settings

settings.update({
    'persist_session_cookies': True,
    'context_menu': {
        'view_source': True,
        'devtools': True
    },
    'debug': True,
    'log_severity': LOGSEVERITY_ERROR if inDev else LOGSEVERITY_INFO,
})

class UpdaterWebView:
    def __init__(self, entry, onStart=None, width=800, height=600):
        self.entry = entry
        self.javascriptLock = threading.Lock()
        self.loggingLock = threading.Lock()
        self.exitLock = threading.Lock()
        self.configCef()

        externalAssets = entry.exe.parent('assets/index.html')
        usingInternalAssets = inDev or not externalAssets.exists
        url = 'assets/index.html' if usingInternalAssets else externalAssets.path
        info('Using '+('internal' if usingInternalAssets else 'external')+' Assets')
        info('Load Assets: '+url)

        self.windowClosed = False
        self.window: Window = webview.create_window('', url=url, js_api=self, width=width, height=height,
                                                    text_select=True)
        self.onStart = onStart

        class Monitor(logging.StreamHandler):
            def emit(self, record: logging.LogRecord) -> None:
                info('WebView: ' + record.message)
                if record.exc_info is not None:
                    logger.error('WebView: ' + record.exc_text)

        logging.getLogger('pywebview').addHandler(Monitor())

    def onInit(self, window):
        self.exitLock.acquire()

        if self.onStart is not None:
            self.onStart(window)

    def start(self):
        webview.start(func=self.onInit, args=self.window, gui='cef', http_server=True, debug=True)
        # webview.start(func=self.onInit, args=self.window, http_server=True)

    def setTitle(self, title):
        self.window.set_title(title)

    def toggleFullscreen(self):
        self.window.toggle_fullscreen()

    def minimize(self):
        self.window.minimize()

    def restore(self):
        self.window.restore()

    def close(self):
        if not self.closed:
            # 如果由JS调用本方法，恰好又是同步调佣destory()的话，会出现依赖锁死导致报错
            threading.Thread(target=lambda: self.window.destroy()).start()

            self.windowClosed = True

        if self.exitLock.locked():
            self.exitLock.release()

    @property
    def closed(self):
        return self.windowClosed

    def execute(self, command):
        try:
            subprocess.call(command, shell=True)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def alert(self, message):
        self.invokeCallback('alert', message)

    def info(self, message):
        self.evaluateJs('console.log("'+message+'")')

    def dialog(self, title, content):
        self.alert(title + ': ' + content)

    def evaluateJs(self, statement):
        try:
            with self.javascriptLock:
                self.window.evaluate_js(statement)
        except BaseException:
            logger.error('+-+-+-+-+-+-+-+--+-+-+-+-+-+-+-+-+-+-+-+-+-')
            logger.error(traceback.format_exc())

    def invokeCallback(self, name, *args):
        argText = ''
        for aa in args:
            argText += json.dumps(aa) + ','
        if argText.endswith(','):
            argText = argText[:-1]

        statement = rf'callback.{name}({argText})'
        with self.loggingLock:
            logger.debug('Statement: ' + statement)
        self.evaluateJs(statement)

    # def setSize(self, width, height):
    #     self.window.resize(width, height)
