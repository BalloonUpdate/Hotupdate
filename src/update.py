from multiprocessing.pool import ThreadPool
from queue import Queue

import requests

from src.common import inDev
from src.exception.FailedToConnectError import FailedToConnectError
from src.exception.UnexpectedHttpCodeError import UnexpectedHttpCodeError
from src.exception.UnexpectedTransmissionError import UnexpectedTransmissionError
from src.logging.LoggingSystem import LogSys
from src.pywebview.updater_web_view import UpdaterWebView
from src.work_mode.mode_a import AMode
from src.work_mode.mode_b import BMode


class Update:
    def __init__(self, entry):
        self.e = entry

    def main(self, serverInfo):
        workDir = self.e.workDir
        webview: UpdaterWebView = self.e.webview

        # 工作目录
        rootDir = workDir
        rootDir.mkdirs()
        if inDev:
            LogSys.info('Environment', 'In Dev Mode: ' + rootDir.path)

        rules = serverInfo['rules']
        LogSys.info('Config', f'Rules: {rules}')

        # 检查最新版本
        webview.invokeCallback('check_for_update', self.e.updateUrl)
        remoteFilesStructure = self.e.httpGet(self.e.updateUrl)

        downloadList = {}
        deleteList = []

        for rule in rules:
            modeA = True
            if rule.startswith('#'):
                rule = rule[1:]
                modeA = False

            mode = (AMode if modeA else BMode)(rootDir, [rule], False)
            mode.scan(rootDir, remoteFilesStructure)

            deleteList += mode.deleteList
            downloadList = {**downloadList, **mode.downloadList}

        # 显示需要下载的新文件
        newFiles = [[filename, length] for filename, length in downloadList.items()]
        webview.invokeCallback('updating_new_files', newFiles)

        # 删除旧文件
        for path in deleteList:
            LogSys.info('Update', 'Deleted: ' + path)
            rootDir(path).delete()

        # 开始下载过程
        self.download(rootDir, downloadList)

        webview.invokeCallback('cleanup')

    def download(self, rootDir, downloadList):
        webview: UpdaterWebView = self.e.webview

        # 读取下载并发数和传输大小
        cfg = self.e.settingsJson
        maxParallel = cfg['parallel'] if 'parallel' in cfg else 1
        chunkSize = cfg['chunk_size'] if 'chunk_size' in cfg else 32
        autoChunkSize = 'chunk_size' in cfg and cfg['chunk_size'] <= 0

        downloadQueue = Queue(1000000)
        threadPool = ThreadPool(maxParallel)

        LogSys.info('Update', 'Count of downloadTask: ' + str(len(downloadList.items())))

        # 开始下载
        for path, length in downloadList.items():
            _file = rootDir(path)
            _url = self.e.updateSource + '/' + path
            downloadQueue.put([_file, _url, path, length])

        def downloadTask():
            while not downloadQueue.empty():
                task = downloadQueue.get(timeout=10)
                file = task[0]
                url = task[1]
                path = task[2]
                length = task[3]

                LogSys.info('Update', 'Downloading: ' + path + ' from ' + url)
                webview.invokeCallback('updating_downloading', path, 0, 0, length)

                try:
                    r = requests.get(url, stream=True, timeout=5)
                    if r.status_code != 200:
                        raise UnexpectedHttpCodeError(url, r.status_code, r.text)

                    if autoChunkSize:
                        cs = int(length / 1024 / 1)
                        _cs = max(4, min(1024, cs))
                        _chunkSize = 1024 * _cs
                        LogSys.info('Update', 'AutoChunkSize: File: '+path+'  len: '+str(length) + '  chunk: '+str(_cs)+' of '+str(cs))
                    else:
                        _chunkSize = 1024 * chunkSize
                        LogSys.info('Update', 'ChunkSize: File: ' + path + '  len: ' + str(length) + '  chunk: ' + str(_chunkSize))
                    received = 0

                    file.makeParentDirs()
                    file.delete()
                    with open(file.path, 'wb+') as f:
                        for chunk in r.iter_content(chunk_size=_chunkSize):
                            f.write(chunk)
                            received += len(chunk)
                            webview.invokeCallback('updating_downloading', path, len(chunk), received, length)

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