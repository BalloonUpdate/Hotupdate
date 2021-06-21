import base64
import ctypes
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

from src.common import inDev, devDirectory
from src.exception.BasicWrappedError import BasicWrappedError
from src.exception.FailedToConnectError import FailedToConnectError
from src.exception.NoSettingsFileError import NoSettingsFileError
from src.exception.NotInRightPathError import NotInRightPathError
from src.exception.UnableToDecodeError import UnableToDecodeError
from src.logging.LoggingSystem import LogSys
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

        # 初始化工作目录
        if not inDev:
            self.workDir = self.exe.parent.parent.parent
            if '.minecraft' not in self.workDir:
                raise NotInRightPathError(self.workDir.path)
        else:
            self.workDir = File(devDirectory)
            self.workDir.mkdirs()

        # 清理信号文件
        self.exe.parent('updater.hotupdate.signal').delete()
        self.exe.parent('updater.error.signal').delete()

    def mainThread(self):
        """主线程/UI线程"""
        self.printEnvInfo()

        try:
            serverInfo = self.fetchInfo()

            try:
                ctypes.windll.kernel32.SetConsoleTitleW("Minecraft文件更新")
            except:
                pass

            # 检查是否有新版本需要升级
            LogSys.is_('正在检查文件更新...')
            remoteFilesStructure = self.httpGet(self.upgradeUrl)
            # upgrade = Upgrade(self)
            # compare = upgrade.compare(remoteFilesStructure)

            # 如果有需要删除/下载的文件，代表程序需要更新
            # if compare.hasDifferent:
            if False:
                pass
                # LogSys.if_('Compare', 'Old Files: ' + str(compare.deleteFiles))
                # LogSys.if_('Compare', 'Old Folders: ' + str(compare.deleteFolders))
                # LogSys.if_('Compare', 'New Files: ' + str(compare.downloadFiles))
                # LogSys.if_('Compare', 'New Folders: ' + str(compare.downloadFolders))

                # 进入升级阶段
                # upgrade.main(compare)
            else:
                LogSys.if_('Compare', 'No upgrade forever')

                # 进入更新阶段
                LogSys.is_('正在检查文件更新...')
                wkmd = Update(self).main(serverInfo)
                if len(wkmd.downloadList) > 0:
                    print('\n')
                    LogSys.is_('MainThread', '所有文件已更新完毕！请按任意键或者关闭本程序。')
                    input()
                else:
                    LogSys.is_('MainThread', '没有文件需要更新。')
                    time.sleep(2)

        except BasicWrappedError as e:
            url = self.settingsJson['url']

            LogSys.ef('Exception', 'BasicWrappedError Exception: ' + traceback.format_exc())
            LogSys.es('\n'+e.content.replace(url, 'https://***')+'\n')
            LogSys.es(e.trans)

            self.exitcode = 1
        except BaseException as e:
            LogSys.error('Exception', 'Python exception raised: ' + traceback.format_exc())

            # className = str(e.__class__)
            # className = className[className.find('\'') + 1:className.rfind('\'')]
            # detail = '----------Python exception raised----------\n' + str(type(e)) + '\n' + str(e)

            self.exitcode = 1

        if self.exitcode == 1:
            input("任意键继续...")

        LogSys.info('MainThread', '退出 ' + str(self.exitcode))

        self.writeSignalFile()
        sys.exit(self.exitcode)

    @staticmethod
    def printEnvInfo():
        LogSys.if_('Environment', 'S:Architecture: ' + platform.machine())
        LogSys.if_('Environment', 'S:Processors: ' + str(psutil.cpu_count()))
        LogSys.if_('Environment', 'S:Operating System: ' + platform.platform())
        LogSys.if_('Environment', 'S:Memory: ' + str(psutil.virtual_memory()))

        if not inDev:
            temp = File(getattr(sys, '_MEIPASS', ''))
            buildInfo = json.loads(temp('build-info.json').content)

            LogSys.if_('Environment', 'HoutupdateVersion: ' + buildInfo['version'])
            LogSys.is_('Environment', 'Minecraft更新小助手，程序版本: ' + buildInfo['version'])

    def fetchInfo(self):
        """从服务端获取'更新信息'"""
        cfg = self.settingsJson

        self.baseUrl = self.tryToDecodeUrl(cfg['url'])
        index = ('/' + cfg['index']) if 'index' in cfg else ''

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

        LogSys.if_('ServerAPI', 'response: ' + str(resp))
        LogSys.if_('ServerAPI', 'upgradeUrl: '+self.upgradeUrl)
        LogSys.if_('ServerAPI', 'updateUrl: ' + self.updateUrl)
        LogSys.if_('ServerAPI', 'upgradeSource: ' + self.upgradeSource)
        LogSys.if_('ServerAPI', 'updateSource: ' + self.updateSource)

        LogSys.if_('Environment', 'ServerVersion: ' + resp['version'])

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
