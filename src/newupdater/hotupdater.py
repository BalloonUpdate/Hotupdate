import subprocess
import sys
import tempfile

import requests
from tqdm import tqdm

from src.newupdater.common import inDevelopment
from src.newupdater.exception.displayable_error import FailedToConnectError, UnexpectedTransmissionError, UnexpectedHttpCodeError
from src.newupdater.hotupdate.file_comparer import FileComparer
from src.newupdater.utils.logger import info


class HotUpdateHelper:
    def __init__(self, entry):
        self.workDir = workDir = entry.workDir
        self.e = entry

        self.temporalDir = workDir(tempfile.mkdtemp()) if not inDevelopment else workDir('debug_temp_dir')
        self.temporalDir.mkdirs()
        self.temporalDir.clear()

        self.temporalScript = workDir(tempfile.mkstemp(suffix='.bat')[1]) if not inDevelopment else workDir('debug_temp_script.bat')

        self.hotupdate = workDir(sys.executable).parent if not inDevelopment else workDir('debug_prog_dir')
        self.hotupdate.mkdirs()

    def compare(self, remoteFileStructure: list):
        comparer = FileComparer(self.hotupdate)
        comparer.compareWith(self.hotupdate, remoteFileStructure)
        return comparer

    def generateBatchStatements(self, comparer: FileComparer):
        # 准备生成用于热替换的batch脚本
        batchText = '@echo off \n'
        batchText += 'echo 准备中.. \n'
        batchText += 'ping -n 3 127.0.0.1 > nul \n'

        # 删除旧文件
        batchText += f'echo 删除旧文件({len(comparer.uselessFiles) + len(comparer.uselessFolders)})\n'
        for d in comparer.uselessFiles:
            file = self.hotupdate[d]
            delCmd = 'del /F /S /Q ' if file.isFile else 'rmdir /S /Q '
            batchText += delCmd + '"' + file.windowsPath + '"\n'
        for d in comparer.uselessFolders:
            file = self.hotupdate[d]
            batchText += f'rmdir /S /Q "{file.windowsPath}"\n'

        # 复制新文件
        source = self.temporalDir.windowsPath + '\\*'
        destination = self.hotupdate.windowsPath + '\\'

        batchText += f'echo 复制新文件({len(comparer.missingFiles)})\n'
        batchText += f'xcopy /E /R /Y "{source}" "{destination}" \n'
        batchText += 'echo 清理临时目录\n'
        batchText += 'ping -n 1 127.0.0.1 > nul \n'
        batchText += 'rmdir /S /Q "' + self.temporalDir.windowsPath + '"\n'
        batchText += 'echo done!!\n'
        batchText += 'ping -n 2 127.0.0.1 > nul \n'
        batchText += f'cd /D "{self.e.exe.parent.windowsPath}" && start {self.e.exe.name} \n' if not inDevelopment else 'echo 运行在开发模式\n'
        batchText += 'exit\n'
        batchText += 'del /F /S /Q "' + self.temporalScript.windowsPath + '"'

        return batchText

    def generateStartupCommand(self):
        return f'cd /D "{self.temporalScript.parent.windowsPath}" && start {self.temporalScript.name}'

    def main(self, comparer: FileComparer, clientSettings):
        # 生成热更新替换脚本
        batchText = self.generateBatchStatements(comparer)
        info('正在更新文件..')

        # 创建缺失的目录
        for mf in comparer.missingFolders:
            self.workDir(mf).mkdirs()

        # 计算总下载量
        totalKBytes = 0
        downloadedBytes = 0
        for df in comparer.missingFiles.values():
            totalKBytes += df[0]

        with tqdm(total=int(totalKBytes/1024), dynamic_ncols=True, unit='kb',  # desc=file.name,
                  bar_format="{percentage:3.0f}% {bar} {n_fmt}/{total_fmt}Kb {rate_fmt}{postfix}") as pbar:

            # 下载新文件
            for k, v in comparer.missingFiles.items():
                url = self.e.upgradeSource + '/' + k
                file = self.temporalDir(k)
                expectantLength = v[0]

                info('下载: ' + file.name)

                try:
                    r = requests.get(url, stream=True, timeout=5)

                    if r.status_code != 200:
                        raise UnexpectedHttpCodeError(url, r.status_code, r.text)

                    file.makeParentDirs()
                    with open(file.path, 'xb+') as f:
                        for chunk in r.iter_content(chunk_size=1024 * 64):
                            f.write(chunk)
                            downloadedBytes += len(chunk)
                            pbar.update(int(len(chunk)/1024))

                except requests.exceptions.ConnectionError as e:
                    raise FailedToConnectError(e, url)
                except requests.exceptions.ChunkedEncodingError as e:
                    raise UnexpectedTransmissionError(e, url)

        # 将脚本代码写入文件
        with open(self.temporalScript.path, "w+", encoding='gbk') as f:
            f.write(batchText)

        # 开始执行替换
        subprocess.call(self.generateStartupCommand(), shell=True)

        # temporalDir.delete() # 由批处理文件删除
        # temporalScript.delete() # 由批处理文件删除
