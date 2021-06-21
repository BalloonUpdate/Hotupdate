import ctypes
import threading
from multiprocessing.pool import ThreadPool
from queue import Queue

import requests
from tqdm import tqdm

from src.common import inDev
from src.exception.FailedToConnectError import FailedToConnectError
from src.exception.UnexpectedHttpCodeError import UnexpectedHttpCodeError
from src.exception.UnexpectedTransmissionError import UnexpectedTransmissionError
from src.exception.UnknownWorkModeError import UnknownWorkModeError
from src.logging.LoggingSystem import LogSys
from src.work_mode.mode_a import AMode
from src.work_mode.mode_b import BMode


class Update:
    def __init__(self, entry):
        self.e = entry

    def main(self, serverInfo):
        workDir = self.e.workDir

        # 工作目录
        rootDir = workDir
        rootDir.mkdirs()
        if inDev:
            LogSys.if_('Environment', 'In Dev Mode: ' + rootDir.path)

        LogSys.if_('Update', f'ServerConfig: {serverInfo}')

        mode = serverInfo['mode']
        paths = serverInfo['paths']

        # 检查最新版本
        remoteFilesStructure = self.e.httpGet(self.e.updateUrl)

        downloadList = {}
        deleteList = []

        workModes = {
            'common': AMode,
            'exist': BMode
        }

        if mode not in workModes:
            raise UnknownWorkModeError(mode)

        workmode = workModes[mode](rootDir, paths, False)

        LogSys.if_('Update', 'WorkMode: ' + str(workmode))

        workmode.scan(rootDir, remoteFilesStructure)

        deleteList += workmode.deleteList
        downloadList = {**downloadList, **workmode.downloadList}

        # 删除旧文件
        for path in deleteList:
            LogSys.if_('Update', 'Deleted: ' + path)
            # LogSys.is_('Update', '删除: ' + path)
            rootDir(path).delete()

        # 开始下载过程
        self.download(rootDir, downloadList)

        return workmode

    def download(self, rootDir, downloadList):

        # 读取下载并发数和传输大小
        cfg = self.e.settingsJson
        maxParallel = cfg['parallel'] if 'parallel' in cfg else 1
        chunkSize = cfg['chunk_size'] if 'chunk_size' in cfg else 32
        autoChunkSize = 'chunk_size' in cfg and cfg['chunk_size'] <= 0

        downloadQueue = Queue(1000000)
        threadPool = ThreadPool(maxParallel)

        LogSys.if_('Update', 'Count of downloadTask: ' + str(len(downloadList.items())))

        if len(downloadList.items()) > 0:
            LogSys.is_('Update', '正在下载新的文件，请不要关掉本程序。')

        # 计算总下载量
        totalKBytes = 0
        downloadedBytes = 0
        for d in downloadList.values():
            totalKBytes += d

        # 进度条
        with tqdm(total=int(totalKBytes / 1024), dynamic_ncols=True, unit='kb', desc='',
                  bar_format="{desc}{percentage:3.1f}% {bar} {n_fmt}/{total_fmt}Kb {rate_fmt}") as pbar:
            pbarUpdateLock = threading.Lock()
            downloadedCount = 0

            # 开始下载
            for path, length in downloadList.items():
                _file = rootDir(path)
                _url = self.e.updateSource + '/' + path
                downloadQueue.put([_file, _url, path, length])
                # LogSys.is_('Update', '下载: ' + path)

            def downloadTask():
                while not downloadQueue.empty():
                    task = downloadQueue.get(timeout=10)
                    file = task[0]
                    url = task[1].replace('+', '%2B')
                    path = task[2]
                    length = task[3]
                    nonlocal downloadedCount

                    LogSys.if_('Debug', 'url: ' + url)
                    LogSys.if_('Update', 'Downloading: ' + path + ' from ' + url)

                    pbar.set_description(str(downloadedCount + 1) + '/' + str(len(downloadList)))

                    ctypes.windll.kernel32.SetConsoleTitleW(path)

                    try:
                        r = requests.get(url, stream=True, timeout=5)
                        if r.status_code != 200:
                            raise UnexpectedHttpCodeError(url, r.status_code, r.text)

                        if autoChunkSize:
                            cs = int(length / 1024 / 1)
                            _cs = max(4, min(1024, cs))
                            _chunkSize = 1024 * _cs
                            LogSys.if_('Update',
                                       'AutoChunkSize: File: ' + path + '  len: ' + str(length) + '  chunk: ' + str(_cs) + ' of ' + str(cs))
                        else:
                            _chunkSize = 1024 * chunkSize
                            LogSys.if_('Update', 'ChunkSize: File: ' + path + '  len: ' + str(length) + '  chunk: ' + str(_chunkSize))
                        # received = 0

                        file.makeParentDirs()
                        file.delete()
                        with open(file.path, 'wb+') as f:
                            nonlocal downloadedBytes
                            for chunk in r.iter_content(chunk_size=_chunkSize):
                                f.write(chunk)
                                # received += len(chunk)
                                downloadedBytes += len(chunk)
                                with pbarUpdateLock:
                                    pbar.update(int(len(chunk) / 1024))

                        downloadedCount += 1

                    except requests.exceptions.ConnectionError as e:
                        raise FailedToConnectError(e, url)
                    except requests.exceptions.ChunkedEncodingError as e:
                        raise UnexpectedTransmissionError(e, url)

            ex = None

            for i in range(0, maxParallel):
                def onError(e):
                    threadPool.terminate()
                    nonlocal ex
                    ex = e

                threadPool.apply_async(downloadTask, error_callback=onError)

            threadPool.close()
            threadPool.join()

            if ex is not None:
                raise ex
