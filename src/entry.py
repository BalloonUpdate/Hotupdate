import base64
import json
import platform
import sys
import threading
import time
import traceback
from binascii import Error
from json import JSONDecodeError
from urllib.parse import unquote

import psutil
import requests

from ci.version import productVersion
from src.common import inDev
from src.exception.BasicWrappedError import BasicWrappedError
from src.exception.FailedToConnectError import FailedToConnectError
from src.exception.NoSettingsFileError import NoSettingsFileError
from src.exception.NotInRightPathError import NotInRightPathError
from src.exception.UnableToDecodeError import UnableToDecodeError
from src.update import Update
from src.pywebview.updater_web_view import UpdaterWebView
from src.upgrade import Upgrade
from src.utils.file import File
from src.utils.logger import info, logger


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

        # PyWebview
        self.webview: UpdaterWebView = None

        self.initializeWorkDirectory()

        # 删除上次遗留的信号文件
        hotupdateSignal = self.exe.parent('updater.hotupdate.signal')
        errorSignal = self.exe.parent('updater.error.signal')

        hotupdateSignal.delete()
        errorSignal.delete()

    def work(self):
        try:
            initConfig = self.getSettingsJson()
            initConfig['indev'] = inDev
            self.webview.invokeCallback('init', initConfig)

            # 读取配置文件
            settingsJson = self.getSettingsJson()

            # 从文件读取服务端url并解码
            self.serverUrl = self.decodeUrl(settingsJson['url'])

            # 发起请求并处理返回的数据
            index = ('/' + settingsJson['index']) if 'index' in settingsJson else ''
            self.webview.invokeCallback('check_for_upgrade', self.serverUrl + index)
            response1 = self.httpGetRequest(self.serverUrl + index)
            upgrade_info = response1['upgrade_info']
            upgrade_dir = response1['upgrade_dir']
            update_info = response1['update_info']
            update_dir = response1['update_dir']
            self.upgradeApi = (self.serverUrl + '/' + upgrade_info) if not upgrade_info.startswith(
                'http') else upgrade_info
            self.upgradeSource = (self.serverUrl + '/' + upgrade_dir) if not upgrade_dir.startswith(
                'http') else upgrade_dir
            self.updateApi = (self.serverUrl + '/' + update_info) if not update_info.startswith('http') else update_info
            self.updateSource = (self.serverUrl + '/' + update_dir) if not update_dir.startswith('http') else update_dir

            info('ServerVersion: '+response1['version'])
            info('HoutupdateVersion: '+productVersion)

            # 检查最新版本
            response2 = self.httpGetRequest(self.upgradeApi)
            remoteFilesStructure = response2

            # 与本地进行对比
            upgrade = Upgrade(self)
            self.webview.invokeCallback('calculate_differences_for_upgrade')
            comparer = upgrade.compare(remoteFilesStructure)

            # 如果有需要删除/下载的文件，代表程序需要更新
            if len(comparer.deleteFiles) > 0 or len(comparer.deleteFolders) > 0 or len(comparer.downloadFiles) > 0:
                info('Old Files: ' + str(comparer.deleteFiles))
                info('Old Folders: ' + str(comparer.deleteFolders))
                info('New Files: ' + str(comparer.downloadFiles))

                # filename, length, hash
                newFiles = [[filename, length[0], length[1]] for filename, length in comparer.downloadFiles.items()]
                newFiles += [[file, -1] for file in comparer.downloadFolders]
                self.webview.invokeCallback('whether_upgrade', True)
                self.webview.invokeCallback('upgrading_new_files', newFiles)

                upgrade.main(comparer)
            else:
                self.webview.invokeCallback('whether_upgrade', False)
                info('There are nothing need updating')

                update = Update(self)
                update.main(response1, settingsJson)

                if 'hold_ui' in settingsJson and settingsJson['hold_ui']:
                    self.webview.exitLock.acquire()
                else:
                    if 'visible_time' in settingsJson and settingsJson['visible_time'] >= 0:
                        time.sleep(settingsJson['visible_time'] / 1000)

            info('Webview Cleanup')

        except BasicWrappedError as e:
            logger.error('BasicWrappedError Exception: ' + traceback.format_exc())
            self.webview.invokeCallback('on_error', str(e.__class__.__name__), e.title + ': ' + e.content, False,
                                        traceback.format_exc())
            self.exitcode = 1
        except BaseException as e:
            logger.error('Unknown error occurred: ' + traceback.format_exc())
            className = str(e.__class__)
            className = className[className.find('\'') + 1:className.rfind('\'')]
            self.webview.invokeCallback('on_error', className,
                                        '----------Python exception raised----------\n' + str(type(e)) + '\n' + str(e),
                                        True, traceback.format_exc())
            self.exitcode = 1
        finally:
            if not self.webview.windowClosed:
                self.webview.close()

    def main(self):
        width = 600
        height = 480

        self.printEnvInfo()

        try:
            # 尝试读取窗口宽高
            settingsJson = self.getSettingsJson()
            width = settingsJson['width']
            height = settingsJson['height']
        except BaseException:
            pass

        workThread = threading.Thread(target=self.work, daemon=True)

        self.webview = UpdaterWebView(self, onStart=lambda window: workThread.start(), width=width, height=height)
        self.webview.start()

        info('Webview Exited with exit code ' + str(self.exitcode))

        # ------------

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
        if not inDev:
            self.workDir = File(sys.argv[1]) if len(sys.argv) > 1 else self.exe.parent.parent.parent
            if '.minecraft' not in self.workDir:
                raise NotInRightPathError(self.workDir.path)
        else:
            self.workDir = File('debug-workdir')
            self.workDir.mkdirs()

    def printEnvInfo(self):
        info('S:Architecture: ' + platform.machine())
        info('S:Processors: ' + str(psutil.cpu_count()))
        info('S:Operating System: ' + platform.platform())
        info('S:Memory: ' + str(psutil.virtual_memory()))

    def getSettingsJson(self):
        file = self.workDir('.minecraft/updater.settings.json')
        try:
            return json.loads(file.content)
        except FileNotFoundError:
            raise NoSettingsFileError(file)

    @staticmethod
    def decodeUrl(url: str):
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
