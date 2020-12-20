import random
import subprocess
import sys
import time

import requests
from tqdm import tqdm

from src.newupdater.common import inDevelopment
from src.newupdater.exception.displayable_error import UnexpectedHttpCodeError, FailedToConnectError, UnexpectedTransmissionError
from src.newupdater.utils.logger import info, debug
from src.newupdater.work_mode.mode_a import AMode
from src.newupdater.work_mode.mode_b import BMode


class NewUpdater:
    def __init__(self, entry):
        self.e = entry

    def main(self, response1, clientSettings):
        workDir = self.e.workDir

        visibleTime = clientSettings['visible_time']

        updatingInfo = response1['server']
        mode = updatingInfo['mode_a']
        regexes = updatingInfo['regexes']
        regexesMode = updatingInfo['match_all_regexes']
        command = updatingInfo['command_before_exit']

        debug(f'ModeA: {mode}')
        debug(f'Regexes: {regexes}')
        debug(f'RegexesMode: {regexesMode}')
        debug(f'Command: {command}')

        # 检查最新版本
        response3 = self.e.httpGetRequest(self.e.updateApi)
        remoteFilesStructure = response3

        rootDir = workDir if not inDevelopment else workDir('debugging-dir')
        rootDir.mkdirs()

        if inDevelopment:
            info('文件夹已被重定向到: ' + rootDir.path)

        # 计算要修改的文件
        work = self.calculateChanges(mode, rootDir, regexes, regexesMode, remoteFilesStructure)

        # 删除旧文件
        totalToDelete = len(work.deleteList)  # 计算出总共要删除的文件数
        deletedCount = 0
        for df in work.deleteList:
            deletedCount += 1
            info('已删除: ' + df)
            rootDir(df).delete()
            time.sleep(0.02 + random.random() * 0.03)

        # 计算出总下载量(字节)
        totalKBytes = 0
        downloadedBytes = 0
        for length in work.downloadMap.values():
            totalKBytes += length

        # 下载新文件
        if len(work.downloadList) > 0:
            with tqdm(total=totalKBytes/1024, dynamic_ncols=True, unit='kb',  # desc=file.name,
                      bar_format="{percentage:3.0f}% {bar} {n_fmt}/{total_fmt}Kb {rate_fmt}{postfix}") as pbar:

                downloadedBytes = 0
                for df in work.downloadList:
                    file = rootDir(df)
                    url = self.e.updateSource+'/'+df

                    info(f'正在下载: {df}')
                    debug(f'正在下载: {df} on {url}')

                    try:
                        r = requests.get(url, stream=True, timeout=5)

                        if r.status_code != 200:
                            raise UnexpectedHttpCodeError(url, r.status_code, r.text)

                        file.makeParentDirs()
                        file.delete()
                        with open(file.path, 'wb+') as f:
                            for chunk in r.iter_content(chunk_size=1024 * 64):
                                f.write(chunk)
                                downloadedBytes += len(chunk)
                                pbar.update(len(chunk)/1024)

                    except requests.exceptions.ConnectionError as e:
                        raise FailedToConnectError(e, url)
                    except requests.exceptions.ChunkedEncodingError as e:
                        raise UnexpectedTransmissionError(e, url)

        info('所有文件已是最新')

        # 如果被打包就执行一下命令
        if getattr(sys, 'frozen', False) and command != '':
            subprocess.call(f'cd /D "{self.e.exe.parent.parent.parent.windowsPath}" && {command}', shell=True)

        if visibleTime >= 0:
            time.sleep(visibleTime / 1000)

    def calculateChanges(self, mode, rootDir, regexes, regexesMode, structure):
        """计算要修改的文件"""

        info('正在检查更新..')

        if mode:
            workMode = AMode(rootDir, regexes, regexesMode)
        else:
            workMode = BMode(rootDir, regexes, regexesMode)

        workMode.scan(rootDir, structure)
        return workMode
