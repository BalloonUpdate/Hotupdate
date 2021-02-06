import json
import logging
import sys
import time
import traceback
import webview

from webview import Window

from src.common import inDevelopment
from src.utils.logger import info, logger
from webview.platforms.cef import settings

settings.update({
    'persist_session_cookies': True
})


class UpdaterWebView:
    def __init__(self, entry, onStart=None, width=800, height=600):
        self.entry = entry

        externalAssets = entry.exe.parent('assets/index.html')
        usingInternalAssets = inDevelopment or not externalAssets.exists
        url = 'assets/index.html' if usingInternalAssets else externalAssets.path
        info('Using '+('internal' if usingInternalAssets else 'external')+' Assets')
        info('Load Assets: '+url)

        self.window: Window = webview.create_window('', url=url, js_api=self, width=width, height=height, text_select=True)
        self.onStart = onStart

        self.expose()

        class Monitor(logging.StreamHandler):
            def emit(self, record: logging.LogRecord) -> None:
                info('WebView: ' + record.message)
                if record.exc_info is not None:
                    logger.error('WebView: ' + record.exc_text)

        logging.getLogger('pywebview').addHandler(Monitor())

    def expose(self):
        self.window.expose(self.setTitle)

    def onInit(self, window):
        if self.onStart is not None:
            self.onStart(window)

    def start(self):
        webview.start(func=self.onInit, args=self.window, gui='cef', http_server=True)
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
        try:
            self.window.destroy()
        except KeyError:
            logger.warn('KeyError')
            pass

    def alert(self, message):
        self.invokeCallback('alert', message)

    def dialog(self, title, content):
        self.alert(title + ': ' + content)

    def invokeCallback(self, name, *args):

        def convert(arg):
            # if isinstance(arg, list):
            #     text = ''
            # if isinstance(arg, tuple):
            #     pass
            if isinstance(arg, bool):
                return 'true' if arg else 'false'
            else:
                return str(arg)

        statement = rf'callback.{name}{str(convert(args))}'
        statement = statement.replace('True', 'true')
        statement = statement.replace('False', 'false')
        logger.debug('Statement: ' + statement)
        try:
            self.window.evaluate_js(statement)
        except:
            logger.error('+-+-+-+-+-+-+-+--+-+-+-+-+-+-+-+-+-+-+-+-+-')
            logger.error(traceback.format_exc())

    # def setSize(self, width, height):
    #     self.window.resize(width, height)
