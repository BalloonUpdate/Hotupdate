from src.newupdater.utils.file import File
from src.newupdater.utils.logger import info
from src.newupdater.work_mode.base_work_mode import BaseWorkMode


class AMode(BaseWorkMode):
    """
    默认同步指定文件夹内的所有文件，
    如果指定了正则表达式，则会使用正则表达式进行进一步筛选
    不匹配的文件会被忽略掉(不做任何变动)
    匹配的文件会与服务器进行同步
    """

    @staticmethod
    def getNameInTree(_name: str, _tree: list):
        """在一个远程目录对象里获取一个文件对象"""
        for n in _tree:
            if n['name'] == _name:
                return n
        return None

    def checkSubFolder(self, t: dict, parent: str, debug=''):
        """检查指定路径是否有 路径可匹配的 子目录"""
        if parent == '.' or parent == './':
            parent = ''
        thisPath = parent + ('/' if parent != '' else '') + t['name']

        if parent == '':
            info('进入特殊检测流程: parent:' + parent + '\n' + debug + '=> ')
        else:
            info(debug + '- ')

        if 'tree' in t:
            info('多文件: ' + thisPath)
            ret = False
            for tt in t['tree']:
                ret |= self.checkSubFolder(tt, thisPath, debug + '    ')
            return ret
        else:
            ret = self.test(thisPath)
            info('单文件: ' + thisPath + '       - ' + str(ret))
            return ret

    def checkSubFolder2(self, d: File, parent: str):
        """检查指定路径是否有 路径可匹配的 子目录"""

        if parent == '.' or parent == './':
            parent = ''

        thisPath = parent + ('/' if parent != '' else '') + d.name

        if d.isDirectory:
            ret = False
            for dd in d:
                ret |= self.checkSubFolder2(dd, thisPath)
            return ret
        else:
            ret = self.test(thisPath)
            return ret

    def scanDownloadableFiles(self, dir: File, tree: list, base: File):
        """只扫描需要下载的文件(不包括被删除的)
        :param dir: 对应的本地目录对象
        :param tree: 与本地目录对应的远程目录
        :param base: 工作目录(更新根目录)，用于计算相对路径
        """

        for t in tree:
            dd = dir[t['name']]
            dPath = dd.relPath(base)

            judgementA = self.test(dPath)
            judgementB = self.checkSubFolder(t, dir.relPath(base))

            info('文件检测结果: ' + dPath + "  A: " + str(judgementA) + "   b: " + str(judgementB) + '  |  ' + dir.relPath(base))

            # 文件自身无法匹配 且 没有子目录/子文件被匹配 时，对其进行忽略
            if not judgementA and not judgementB:
                info('无法匹配: ' + str(t))
                continue

            if not dd.exists:  # 文件不存在的话就不用校验直接进行下载
                self.download(t, dd)
            else:  # 文件存在的话要进行进一步判断
                if 'tree' in t:  # 远程对象是一个目录
                    if dd.isFile:  # 本地对象是一个文件
                        # 先删除本地的 文件 再下载远程端的 目录
                        self.delete(dd)
                        self.download(t, dd)
                    else:  # 远程对象 和 本地对象 都是目录
                        # 递归调用，进行进一步判断
                        self.scanDownloadableFiles(dd, t['tree'], base)
                else:  # 远程对象是一个文件
                    if dd.isFile:  # 远程对象 和 本地对象 都是文件
                        # 校验hash
                        if dd.sha1 != t['hash']:
                            # 如果hash对不上，删除后进行下载
                            self.delete(dd)
                            self.download(t, dd)
                    else:  # 本地对象是一个目录
                        # 先删除本地的 目录 再下载远程端的 文件
                        self.delete(dd)
                        self.download(t, dd)

    def scanDeletableFiles(self, dir: File, tree: list, base: File):
        """只扫描需要删除的文件
        :param dir: 对应的本地目录对象
        :param tree: 与本地目录对应的远程目录
        :param base: 工作目录(更新根目录)，用于计算相对路径
        """

        for d in dir:
            t = AMode.getNameInTree(d.name, tree)  # 参数获取远程端的对应对象，可能会返回None
            dPath = d.relPath(base)

            judgementA = self.test(dPath)
            judgementB = self.checkSubFolder2(d, dir.relPath(base))

            # 文件自身无法匹配 且 没有子目录/子文件被匹配 时，对其进行忽略
            if not judgementA and not judgementB:
                continue

            if t is not None:  # 如果远程端也有这个文件
                if d.isDirectory:
                    if 'tree' in t:
                        # 如果 本地对象 和 远程对象 都是目录，递归调用进行进一步判断
                        self.scanDeletableFiles(d, t['tree'], base)
                # 其它情况均由scanDownloadableFiles进行处理了，这里不需要重复判断
            else:  # 远程端没有有这个文件，就直接删掉好了
                self.delete(d)

    def scan(self, dir: File, tree: list):
        self.scanDownloadableFiles(dir, tree, dir)
        self.scanDeletableFiles(dir, tree, dir)
        self.excludeSelf()
