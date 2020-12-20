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

from src.newupdater.common import inDevelopment
from src.newupdater.exception.displayable_error import BasicDisplayableError, FailedToConnectError, UnableToDecodeError, \
    NotInRightPathError, NoSettingsFileError
from src.newupdater.hotupdater import HotUpdateHelper
from src.newupdater.newupdater import NewUpdater
from src.newupdater.ui.updating_window import UpdatingWindow
from src.newupdater.ui.upgrading_window import UpgradingWindow
from src.newupdater.utils.file import File
from src.newupdater.utils.logger import info


class Entry:
    def __init__(self):
        self.workDir = None
        self.exe = File(sys.executable)
        self.serverUrl = ''
        self.upgradeApi = ''  # 软件自升级的API
        self.upgradeSource = ''
        self.updateApi = ''  # 文件更新的API
        self.updateSource = ''

        # 初始化UI界面
        self.qt = QApplication(sys.argv)
        self.updatingWindow = UpdatingWindow()
        self.upgradingWindow = UpgradingWindow()

        self.uiThreadHandle = threading.Thread(target=self.work, daemon=True)

    def work(self):
        try:
            try:
                self.initializeWorkDirectory()

                # 从文件读取服务端url并解码
                self.serverUrl = self.decodeUrl(self.getSettingsJson()['url'])

                # 发起请求并处理返回的数据
                response1 = self.httpGetRequest(self.serverUrl)
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

                # 如果有需要删除/下载的文件，代表程序需要更新
                if len(comparer.uselessFiles) > 0 or len(comparer.uselessFolders) > 0 or len(comparer.missingFiles) > 0:
                    info('需要更新')
                    info('uselessFiles: ' + str(comparer.uselessFiles))
                    info('uselessFolders: ' + str(comparer.uselessFolders))
                    info('missingFiles: ' + str(comparer.missingFiles))

                    hotupdate.main(comparer, response1['client'])
                else:
                    info('不需要更新')
                    np = NewUpdater(self)
                    np.main(response1, response1['client'])
            except requests.exceptions.ConnectionError as e:
                info('请求失败,连接错误: \n' + str(e))
                input('任意键退出..')
            except KeyboardInterrupt:
                info('收到键盘中断信号')
                exit(1)
        except BasicDisplayableError as e:
            info('异常: '+str(e))
            self.upgradingWindow.es_showMessageBox.emit(e.content, e.title)
            sys.exit(1)
        except SystemExit:
            pass
        except BaseException as e:
            info('出现了未知错误: '+traceback.format_exc())
            self.upgradingWindow.es_showMessageBox.emit(traceback.format_exc(), '出现了未知错误')
            sys.exit(1)

    def main(self):
        self.uiThreadHandle.start()

        info('ui工作')
        r = self.qt.exec_()
        info('ui退出'+str(r))

    def initializeWorkDirectory(self):
        if not inDevelopment:
            cwd = File(sys.argv[1]) if len(sys.argv) > 1 else self.exe.parent.parent.parent
            if '.minecraft' in cwd:
                self.workDir = cwd
            else:
                raise NotInRightPathError(cwd.path)
        else:
            self.workDir = File('debug-dir')
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

    def httpGetRequest(self, url):
        response = None
        try:
            response = requests.get(url, timeout=6)
            return response.json()
        except requests.exceptions.ConnectionError as e:
            raise FailedToConnectError(e, url)
        except JSONDecodeError as e:
            raise UnableToDecodeError(e, url, response.status_code, response.text)
