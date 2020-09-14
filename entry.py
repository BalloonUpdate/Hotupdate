import json
import platform
import subprocess
import sys
from json.decoder import JSONDecodeError

import requests
from tqdm import tqdm

from File import File


def checkURL(Url: str):
    return Url if Url.endswith('/') else Url + '/'


def downloadFileWithTQDM(Url: str, file: File):
    r = requests.get(Url, stream=True)
    assert r.status_code == 200, "HTTP CODE: " + str(r.status_code)

    totalSize = int(r.headers.get("Content-Length"))
    chunkSize = 1024

    file.makeParentDirs()
    f = open(file.absPath, 'xb+')

    with tqdm(total=int(totalSize / 1024),
              dynamic_ncols=True,
              unit='kb',
              desc=file.name,
              bar_format="{l_bar}{bar} {n_fmt}/{total_fmt}Kb {rate_fmt}{postfix}"
              ) as pbar:
        for chunk in r.iter_content(chunk_size=chunkSize):
            f.write(chunk)
            recv = int(len(chunk) / 1024)
            pbar.update(recv)

    f.close()


if __name__ == "__main__":

    settingsFile = File('settings.json')

    if not settingsFile.exists:
        sfInMc = settingsFile.parent['.minecraft']['settings.json']
        if not sfInMc.exists:
            msg = '找不到文件 settings.json,请检查是否存在于本程序旁边或者.minecraft文件夹里'
            print(msg)
            input('任意键退出..')
        else:
            settingsFile = sfInMc

    settings = json.loads(settingsFile.content)
    settings['url'] = checkURL(settings['url'])

    response = None
    url = ''

    try:
        response = requests.get(settings['url'] + 'update.php')
        info = response.json()

        executable = File('.minecraft/updater.exe')

        if not executable.exists or executable.sha1 != info['hash']:
            print('正在更新主程序..')
            executable.makeParentDirs()
            executable.delete()
            url = settings['url'] + info['filename']
            downloadFileWithTQDM(url, executable)

        if platform.platform().startswith('Windows'):
            subprocess.call('start ' + executable.path, shell=True)
        else:
            subprocess.call(executable.path, shell=True)
    except requests.exceptions.ConnectionError as e:
        print('请求失败,连接错误: \n' + str(e))
        input('任意键退出..')
    except JSONDecodeError as e:
        text = '服务器返回了无法解码的信息:\n'
        text += '访问的URL: ' + response.url + '\n'
        text += 'HTTP CODE: ' + str(response.status_code) + '\n\n'
        text += '原始数据:\n' + response.text
        print(text)
        input('任意键退出..')
    except AssertionError as e:
        text2 = '下载主程序时出现了错误,服务器没有按预期返回200:\n'
        text2 += '原始URL: ' + url + '\n'
        text2 += str(e)+''
        print(text2)
        input('任意键退出..')
    except requests.exceptions.ChunkedEncodingError as e:
        text3 = '与服务器的连接意外中断:\n'
        text3 += str(e)
        print(text3)
        input('任意键退出..')
    except BaseException as e:
        print('出现了未知错误:\n' + str(e))
        input('任意键退出..')
