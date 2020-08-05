import json

import requests
from tqdm import tqdm

from File import File
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


if __name__ == "__main__":

    settingsFile = File('settings.json')

    if not settingsFile.exists:
        print('settings.json不存在')
        default = {"metadataUrl": "http://127.0.0.1", "resourcesUrl": "http://127.0.0.1/resources"}
        settingsFile.put(json.dumps(default))
        exit(0)

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
        td.append(p).delete()

    for p in hl.downloadList:
        file = td.append(p)
        downloadFile(settings['resourcesUrl'] + p, file)

    print(infojson['announcement'])
