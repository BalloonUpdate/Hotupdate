import base64
import json
import sys
import threading
import traceback
from binascii import Error
from json import JSONDecodeError
from urllib.parse import unquote

import requests
from PyQt5.QtWidgets import QApplication

from src.common import inDevelopment
from src.exception.displayable_error import BasicDisplayableError, FailedToConnectError, UnableToDecodeError, \
    NotInRightPathError, NoSettingsFileError
from src.hotupdate import HotUpdateHelper
from src.newupdater import NewUpdater
from src.ui.splash_window import SplashWindow
from src.ui.updating_window import UpdatingWindow
from src.ui.upgrading_window import UpgradingWindow
from src.utils.file import File
from src.utils.logger import info


class Entry:
    def __init__(self):
        self.workDir = None
        self.exe = File(sys.executable)
        self.serverUrl = ''
        self.upgradeApi = ''  # 软件自升级的API
        self.upgradeSource = ''
        self.updateApi = ''  # 文件更新的API
        self.updateSource = ''
        self.exitcode = 0

        # 初始化UI界面
        self.qt = QApplication(sys.argv)
        self.updatingWindow = UpdatingWindow()
        self.upgradingWindow = UpgradingWindow()
        self.splashWindow = SplashWindow()

        self.upgradingWindow.e = self

        self.uiThreadHandle = threading.Thread(target=self.work, daemon=True)

    def work(self):
        try:
            try:
                self.initializeWorkDirectory()

                self.splashWindow.es_setShow.emit(True)
                self.splashWindow.es_setWindowTitle.emit('UpdaterHotupdatePackage')
                self.splashWindow.es_setText.emit('正在连接服务器')

                # 读取配置文件
                settingsJson = self.getSettingsJson()

                # 从文件读取服务端url并解码
                self.serverUrl = self.decodeUrl(settingsJson['url'])

                # 发起请求并处理返回的数据
                index = ('/' + settingsJson['index']) if 'index' in settingsJson else ''
                response1 = self.httpGetRequest(self.serverUrl + index)
                upgrade_info = response1['upgrade_info']
                upgrade_dir = response1['upgrade_dir']
                update_info = response1['update_info']
                update_dir = response1['update_dir']
                self.upgradeApi = (self.serverUrl + '/' + upgrade_info) if not upgrade_info.startswith('http') else upgrade_info
                self.upgradeSource = (self.serverUrl + '/' + upgrade_dir) if not upgrade_dir.startswith('http') else upgrade_dir
                self.updateApi = (self.serverUrl + '/' + update_info) if not update_info.startswith('http') else update_info
                self.updateSource = (self.serverUrl + '/' + update_dir) if not update_dir.startswith('http') else update_dir

                # 检查最新版本
                response2 = self.httpGetRequest(self.upgradeApi)
                remoteFilesStructure = response2

                # 与本地进行对比
                hotupdate = HotUpdateHelper(self)
                comparer = hotupdate.compare(remoteFilesStructure)
                self.splashWindow.es_setText.emit('正在加载..')

                # 关闭窗口
                self.splashWindow.es_setShow.emit(False)

                # 如果有需要删除/下载的文件，代表程序需要更新
                if len(comparer.uselessFiles) > 0 or len(comparer.uselessFolders) > 0 or len(comparer.missingFiles) > 0:
                    info('the followings need updating: ')
                    info('uselessFiles: ' + str(comparer.uselessFiles))
                    info('uselessFolders: ' + str(comparer.uselessFolders))
                    info('missingFiles: ' + str(comparer.missingFiles))

                    hotupdate.main(comparer, response1['client'])
                else:
                    info('there are nothing need updating')
                    np = NewUpdater(self)
                    np.main(response1, response1['client'])
            finally:
                # 关闭窗口
                try:
                    self.splashWindow.es_setShow.emit(False)
                except RuntimeError:
                    pass
        except BasicDisplayableError as e:
            info('displayable Exception: ' + str(e))
            self.upgradingWindow.es_showMessageBox.emit(e.content, e.title)
            self.exitcode = 1
        except BaseException as e:
            info('unknown error occurred: ' + traceback.format_exc())
            self.upgradingWindow.es_showMessageBox.emit(traceback.format_exc(), '出现了未知错误')
            self.exitcode = 1

    def main(self):
        self.uiThreadHandle.start()

        info('qt looping..')
        r = self.qt.exec_()
        info('qt loop ended with exit code: ' + str(r))

        hotupdateSignal = self.exe.parent('updater.hotupdate.signal')
        errorSignal = self.exe.parent('updater.error.signal')

        hotupdateSignal.delete()
        errorSignal.delete()

        if self.exitcode == 2:
            hotupdateSignal.create()

        if self.exitcode == 1:
            errorSignal.create()

        sys.exit(self.exitcode)

    def initializeWorkDirectory(self):
        if not inDevelopment:
            self.workDir = File(sys.argv[1]) if len(sys.argv) > 1 else self.exe.parent.parent.parent
            if '.minecraft' not in self.workDir:
                raise NotInRightPathError(self.workDir.path)
        else:
            self.workDir = File('debug-workdir')
            self.workDir.mkdirs()

    def getSettingsJson(self):
        try:
            file = self.workDir('.minecraft/updater.settings.json')
            return json.loads(file.content)
        except FileNotFoundError:
            raise NoSettingsFileError(file)

    def decodeUrl(self, url: str):
        try:
            serverUrl = unquote(base64.b64decode(url, validate=True).decode('utf-8'), 'utf-8')
        except Error:
            serverUrl = url
        return serverUrl

    @staticmethod
    def httpGetRequest(url):
        response = None
        try:
            response = requests.get(url, timeout=6)
            return response.json()
        except requests.exceptions.ConnectionError as e:
            raise FailedToConnectError(e, url)
        except JSONDecodeError as e:
            raise UnableToDecodeError(e, url, response.status_code, response.text)
        except requests.exceptions.ReadTimeout as e:
            raise FailedToConnectError(e, url)
