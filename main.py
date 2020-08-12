import json
import platform
import sys
import threading
import time

import requests
from tqdm import tqdm

from CursesLib.Terminal import Terminal
from CursesLib.utils.ChineseSpace import smartStretch
from CursesLib.window.ProcessListWindow import ProcessListWindow
from CursesLib.window.component.CloseButton import CloseButton
from CursesLib.window.component.WindowTitle import WindowTitle
from File import File
from terminal import setFont, setBuffer
from work.Blacklist import Blacklist
from work.Whitelist import Whitelist


def downloadFile(url: str, file: File):
    r = requests.get(url, stream=True)
    assert r.status_code == 200, "HTTP ERR CODE: " + str(r.status_code)

    totalSize = int(r.headers.get("Content-Length"))
    chunkSize = 1024

    file.makeParentDirs()
    f = open(file.absPath, 'xb+')

    with tqdm(total=int(totalSize / 1024), dynamic_ncols=True, unit='kb', desc=file.name) as pbar:
        for chunk in r.iter_content(chunk_size=chunkSize):
            f.write(chunk)
            recv = int(len(chunk) / 1024)
            pbar.update(recv)

    f.close()


def checkURL(url: str):
    return url if url.endswith('/') else url + '/'


class AList(ProcessListWindow):
    def __init__(self):
        super().__init__()

        if not platform.platform().startswith('Windows-10'):
            border = self.getComponent('border')
            border.enable = False
            # border.bgChar = curses.ACS_VLINE
            border.markChar = '|'

        self.addComponent("title", WindowTitle(smartStretch('更新列表')))
        self.addComponent("close", CloseButton())


def work2():
    try:
        work()
    except Exception as e:
        ts.quit()
        raise e


def work():
    settingsFile = File('settings.json')

    if not settingsFile.exists:
        print('settings.json不存在')
        default = {"metadataUrl": "http://127.0.0.1", "resourcesUrl": "http://127.0.0.1/resources"}
        settingsFile.put(json.dumps(default))
        exit()

    settings = json.loads(settingsFile.content)

    settings['metadataUrl'] = checkURL(settings['metadataUrl'])
    settings['resourcesUrl'] = checkURL(settings['resourcesUrl'])

    metadataResponse = requests.get(settings['metadataUrl'])
    assert metadataResponse.status_code == 200, f"HTTP ERR CODE: " + str(metadataResponse.status_code)
    infojson = metadataResponse.json()

    td = File('target')
    td.mkdirs()

    if infojson['mode'] == 'whitelist':
        hl = Whitelist(td.absPath)
    else:
        hl = Blacklist(td.absPath)

    hl.scan(td, infojson['structure'])

    # print('\n'.join(hl.deleteList))
    # print('----------')
    # print('\n'.join(hl.downloadList))

    for p in hl.deleteList:
        al.addItem(p, '删除文件 ' + p, 0.0, None)

    for p in hl.downloadList:
        al.addItem(p, '等待下载 '+p, 0.0, None)

    for p in hl.deleteList:
        # td.append(p).delete()
        # al.removeItem(p)
        al.getItem(p)[2] = -1

        if al.viewFollow:
            al.lookAtItem(p)
        else:
            al.drawAFrame()

        time.sleep(0.01)

    def downloadFile2(url: str, file: File, relPath: str):
        r = requests.get(url, stream=True)
        assert r.status_code == 200, "HTTP ERR CODE: " + str(r.status_code)

        totalSize = int(r.headers.get("Content-Length"))
        chunkSize = 1024
        received = 0

        file.makeParentDirs()

        File(file.absPath + '.ts').delete()
        f = open(file.absPath + '.ts', 'xb+')

        for chunk in r.iter_content(chunk_size=chunkSize):
            f.write(chunk)
            received += len(chunk)
            al.getItem(p)[1] = format(received / totalSize * 100, '.2f')+'% '+p
            al.getItem(p)[2] = received / totalSize

            if al.viewFollow:
                al.lookAtItem(p)
            else:
                al.drawAFrame()

        if totalSize == 0:
            al.getItem(p)[2] = 1
            al.drawAFrame()

        f.close()
        al.getItem(p)[1] = '下载完成 ' + p
        al.lookAtItem(p)

    for p in hl.downloadList:
        file = td.append(p)
        downloadFile2(settings['resourcesUrl'] + p, file, p)

    print(infojson['announcement'])

    # time.sleep(3)
    # ts.quit()


if __name__ == "__main__":

    if sys.prefix == sys.base_prefix:
        setFont()
        setBuffer()

    ts = Terminal()
    al = AList()

    ts.addWindow(al)

    threading.Thread(target=work2, daemon=True).start()

    ts.mainLoop()


