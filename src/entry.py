import base64
import json
import platform
import sys
import threading
import traceback
from binascii import Error
from json import JSONDecodeError
from urllib.parse import unquote

import psutil
import requests

from ci.version import productVersion
from src.common import inDev, devDirectory
from src.exception.BasicWrappedError import BasicWrappedError
from src.exception.FailedToConnectError import FailedToConnectError
from src.exception.NoSettingsFileError import NoSettingsFileError
from src.exception.NotInRightPathError import NotInRightPathError
from src.exception.UnableToDecodeError import UnableToDecodeError
from src.logging.LoggingSystem import LogSys
from src.pywebview.updater_web_view import UpdaterWebView
from src.update import Update
from src.upgrade import Upgrade
from src.utils.file import File


class Entry:
    def __init__(self):
        self.workDir = None
        self.exe = File(sys.executable)
        self.baseUrl = ''
        self.upgradeUrl = ''
        self.updateUrl = ''
        self.upgradeSource = ''
        self.updateSource = ''
        self.exitcode = 0

        self.updateLock = threading.Lock()

        self.webview: UpdaterWebView = None

        self.initializeWorkDirectory()
        self.clearSignalFile()

    def workThread(self):
        """工作线程"""
        try:
            self.webview.invokeCallback('init', {**self.settingsJson, 'indev': inDev})

            # 等待开始更新的信号
            self.updateLock.acquire()
            self.updateLock.acquire()

            serverInfo = self.fetchInfo()

            # 检查是否有新版本需要升级
            remoteFilesStructure = self.httpGet(self.upgradeUrl)
            upgrade = Upgrade(self)
            compare = upgrade.compare(remoteFilesStructure)

            # 如果有需要删除/下载的文件，代表程序需要更新
            if compare.hasDifferent:
                LogSys.info('Compare', 'Old Files: ' + str(compare.deleteFiles))
                LogSys.info('Compare', 'Old Folders: ' + str(compare.deleteFolders))
                LogSys.info('Compare', 'New Files: ' + str(compare.downloadFiles))
                LogSys.info('Compare', 'New Folders: ' + str(compare.downloadFolders))

                # 触发回调函数
                # filename, length, hash
                newFiles = [[filename, length[0], length[1]] for filename, length in compare.downloadFiles.items()]
                newFiles += [[file, -1] for file in compare.downloadFolders]
                self.webview.invokeCallback('whether_upgrade', True)
                self.webview.invokeCallback('upgrading_new_files', newFiles)

                # 进入升级阶段
                upgrade.main(compare)
            else:
                self.webview.invokeCallback('whether_upgrade', False)
                LogSys.info('Compare', 'There are nothing need update')

                # 进入更新阶段
                Update(self).main(serverInfo)

                self.webview.exitLock.acquire()

            LogSys.info('Webview', 'Webview Cleanup')

        except BasicWrappedError as e:
            LogSys.error('Exception', 'BasicWrappedError Exception: ' + traceback.format_exc())

            typeName = str(e.__class__.__name__)
            detail = e.content

            self.webview.invokeCallback('on_error', typeName, detail, False, traceback.format_exc())
            self.exitcode = 1
        except BaseException as e:
            LogSys.error('Exception', 'Python exception raised: ' + traceback.format_exc())

            className = str(e.__class__)
            className = className[className.find('\'') + 1:className.rfind('\'')]
            detail = '----------Python exception raised----------\n' + str(type(e)) + '\n' + str(e)

            self.webview.invokeCallback('on_error', className, detail, True, traceback.format_exc())
            self.exitcode = 1
        # finally:
        #     if not self.webview.windowClosed:
        #         self.webview.close()

    def mainThread(self):
        """主线程/UI线程"""
        cfg = self.settingsJson
        width = cfg['width'] if 'width' in cfg else 380
        height = cfg['height'] if 'height' in cfg else 130

        self.printEnvInfo()

        workThread = threading.Thread(target=self.workThread, daemon=True)

        # 启动CEF窗口
        self.webview = UpdaterWebView(self, onStart=lambda window: workThread.start(), width=width, height=height)
        self.webview.start()

        LogSys.info('Webview', 'Webview Exited with exit code ' + str(self.exitcode))

        self.writeSignalFile()
        sys.exit(self.exitcode)

    def initializeWorkDirectory(self):
        if not inDev:
            self.workDir = File(sys.argv[1]) if len(sys.argv) > 1 else self.exe.parent.parent.parent
            if '.minecraft' not in self.workDir:
                raise NotInRightPathError(self.workDir.path)
        else:
            self.workDir = File(devDirectory)
            self.workDir.mkdirs()

    @staticmethod
    def printEnvInfo():
        LogSys.info('Environment', 'S:Architecture: ' + platform.machine())
        LogSys.info('Environment', 'S:Processors: ' + str(psutil.cpu_count()))
        LogSys.info('Environment', 'S:Operating System: ' + platform.platform())
        LogSys.info('Environment', 'S:Memory: ' + str(psutil.virtual_memory()))

    def fetchInfo(self):
        """从服务端获取'更新信息'"""
        cfg = self.settingsJson

        self.baseUrl = self.tryToDecodeUrl(cfg['url'])
        index = ('/' + cfg['index']) if 'index' in cfg else ''

        self.webview.invokeCallback('check_for_upgrade', self.baseUrl + index)

        resp = self.httpGet(self.baseUrl + index)

        upgrade = resp['upgrade'] if 'upgrade' in resp else 'self'
        update = resp['update'] if 'upgrade' in resp else 'res'

        def findSource(text, default):
            if '?' in text:
                paramStr = text.split('?')
                if paramStr[1] != '':
                    for paramPair in paramStr[1].split('&'):
                        pp = paramPair.split('=')
                        if len(pp) == 2 and pp[0] == 'source' and pp[1] != '':
                            return pp[1]
                return paramStr[0]
            return default

        self.upgradeUrl = self.baseUrl + '/' + (upgrade + '.json' if '?' not in upgrade else upgrade)
        self.updateUrl = self.baseUrl + '/' + (update + '.json' if '?' not in update else update)
        self.upgradeSource = self.baseUrl + '/' + findSource(upgrade, upgrade)
        self.updateSource = self.baseUrl + '/' + findSource(update, update)

        LogSys.info('ServerAPI', 'response: ' + str(resp))
        LogSys.info('ServerAPI', 'upgradeUrl: '+self.upgradeUrl)
        LogSys.info('ServerAPI', 'updateUrl: ' + self.updateUrl)
        LogSys.info('ServerAPI', 'upgradeSource: ' + self.upgradeSource)
        LogSys.info('ServerAPI', 'updateSource: ' + self.updateSource)

        LogSys.info('Environment', 'ServerVersion: ' + resp['version'])
        LogSys.info('Environment', 'HoutupdateVersion: ' + productVersion)

        return resp

    def writeSignalFile(self):
        """往exe所在目录写入信号文件，UpdaterClient程序会根据不同的信号执行不同的操作"""

        hotupdateSignal = self.exe.parent('updater.hotupdate.signal')
        errorSignal = self.exe.parent('updater.error.signal')

        hotupdateSignal.delete()
        errorSignal.delete()

        if self.exitcode == 2:
            hotupdateSignal.create()

        if self.exitcode == 1:
            errorSignal.create()

    def clearSignalFile(self):
        """清理信号文件"""

        self.exe.parent('updater.hotupdate.signal').delete()
        self.exe.parent('updater.error.signal').delete()

    @property
    def settingsJson(self):
        file = self.workDir('.minecraft/updater.settings.json')
        try:
            return json.loads(file.content)
        except FileNotFoundError:
            raise NoSettingsFileError(file)

    @staticmethod
    def tryToDecodeUrl(url: str):
        try:
            serverUrl = unquote(base64.b64decode(url, validate=True).decode('utf-8'), 'utf-8')
        except Error:
            serverUrl = url
        return serverUrl

    @staticmethod
    def httpGet(url):
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
