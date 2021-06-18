import json
import logging
import subprocess
import threading
import time
import traceback

import webview
from cefpython3.cefpython_py37 import LOGSEVERITY_DISABLE
from webview import Window
from webview.platforms.cef import settings

from src.utils.file import File
from src.common import inDev
from src.logging.LoggingSystem import LogSys


class UpdaterWebView:
    def __init__(self, entry, onStart=None, width=800, height=600, icon=None):
        self.entry = entry
        self.javascriptLock = threading.Lock()
        self.loggingLock = threading.Lock()
        self.exitLock = threading.Lock()
        self.configCef()

        cfg = entry.settingsJson

        self.externalAssets = entry.exe.parent('assets/index.html')
        self.usingRemoteAssets = 'interface' in cfg
        self.usingInternalAssets = inDev or not self.externalAssets.exists

        if self.usingRemoteAssets:
            LogSys.info('Webview', 'Using Remote Assets')
            url = cfg['interface']
        elif self.usingInternalAssets:
            LogSys.info('Webview', 'Using Internal Assets')
            url = 'assets/index.html'
        else:
            LogSys.info('Webview', 'Using External Assets')
            url = self.externalAssets.path

        LogSys.info('Webview', 'Load Assets: ' + url)

        self.windowClosed = False
        self.window: Window = webview.create_window('', url=url, js_api=self, width=width, height=height,
                                                    text_select=True)

        self.onStart = onStart

        class Monitor(logging.StreamHandler):
            def emit(self, record: logging.LogRecord) -> None:
                LogSys.info('Webview', 'WebView: ' + record.message)
                if record.exc_info is not None:
                    LogSys.error('Webview', 'WebView: ' + record.exc_text)

        logging.getLogger('pywebview').addHandler(Monitor())

    def configCef(self):
        settings.update({
            'context_menu': {
                'view_source': True,
                'devtools': True
            },
            'debug': False,
            'log_file': self.entry.workDir('.minecraft/logs/updater-cef.log').path,
            'log_severity': LOGSEVERITY_DISABLE
        })

    def onInit(self, window):
        self.exitLock.acquire()

        if self.onStart is not None:
            self.onStart(window)

        self.setIcon()

    def start(self):
        cfg = self.entry.settingsJson
        cef_with_httpserver = cfg['cef_with_httpserver'] if 'cef_with_httpserver' in cfg else True

        try:
            webview.start(func=self.onInit, args=self.window, gui='cef', http_server=cef_with_httpserver, debug=True)
        except UnicodeDecodeError as e:
            if 'cef_with_httpserver' not in cfg:
                webview.start(func=self.onInit, args=self.window, gui='cef', http_server=False, debug=True)
            else:
                raise e

    def startUpdate(self):
        def s():
            LogSys.info('WebView', 'startUpdate')
            while not self.entry.updateLock.locked():
                time.sleep(0.1)
            self.entry.updateLock.release()

        threading.Thread(target=s, daemon=True).start()

    def getUrl(self):
        return self.window.get_current_url()

    def loadUrl(self, url):
        LogSys.info('WebView', 'LoadUrl: '+url)
        self.window.load_url(url)

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

    def getWorkDirectory(self):
        return self.entry.exe.parent.parent.parent.windowsPath

    def execute(self, command):
        try:
            subprocess.call(command, shell=True)
        except Exception as e:
            LogSys.error('Webview', e)
            LogSys.error('Webview', traceback.format_exc())

    def info(self, message):
        self.evaluateJs('console.log("'+message+'")')

    def evaluateJs(self, statement):
        try:
            with self.javascriptLock:
                self.window.evaluate_js(statement)
        except BaseException:
            LogSys.error('Webview', '+-+-+-+-+-+-+-+--+-+-+-+-+-+-+-+-+-+-+-+-+-')
            LogSys.error('Webview', traceback.format_exc())

    def invokeCallback(self, name, *args):
        argText = ''
        for aa in args:
            argText += json.dumps(aa) + ','
        if argText.endswith(','):
            argText = argText[:-1]

        statement = rf'updaterApi.dispatchEvent("{name}", {argText})'
        with self.loggingLock:
            LogSys.debug('Webview', 'Statement: ' + statement)
        self.evaluateJs(statement)

    def setIcon(self):
        if self.usingInternalAssets:
            LogSys.info('Webview', 'Using Internal Icon')
            ico = 'assets/icon.ico'
            if not inDev:
                temp = File(getattr(sys, '_MEIPASS', ''))
                ico = temp(ico).path
        else:
            LogSys.info('Webview', 'Using External Icon')
            ico = self.entry.exe.parent('assets/icon.ico')

        if not File(ico).exists:
            LogSys.warning('Webview', 'Icon not found: '+ico)
            return

        import clr
        from System.Drawing import Icon

        instances = self.window.gui.BrowserView.instances

        def work():
            while 'master' not in instances:
                time.sleep(0.1)
            winform = instances['master']
            winform.Icon = Icon(ico)
            print(winform.Icon)

        threading.Thread(target=work, daemon=True).start()

    # def setSize(self, width, height):
    #     self.window.resize(width, height)
