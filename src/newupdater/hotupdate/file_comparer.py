from src.newupdater.utils.file import File


class FileComparer:
    def __init__(self, basePath):
        super().__init__()
        self.basePath: File = basePath
        self.deleteList: list = []
        self.downloadList: list = []
        self.downloadMap: dict = {}

    def scanDownloadableFiles(self, dir: File, tree: list, base: File):
        """只扫描需要下载的文件(不包括被删除的)
        :param dir: 对应的本地目录对象
        :param tree: 与本地目录对应的远程目录
        :param base: 工作目录(更新根目录)，用于计算相对路径
        """

        for file in tree:
            corresponding = dir.append(file['name'])

            if not corresponding.exists:  # 文件不存在的话就不用校验直接进行下载
                self.download(file, corresponding)
            else:  # 文件存在的话要进行进一步判断
                if 'tree' in file:  # 远程对象是一个目录
                    if corresponding.isFile:  # 本地对象是一个文件
                        # 先删除本地的 文件 再下载远程端的 目录
                        self.delete(corresponding)
                        self.download(file, corresponding)
                    else:  # 远程对象 和 本地对象 都是目录
                        # 递归调用，进行进一步判断
                        self.scanDownloadableFiles(corresponding, file['tree'], base)
                else:  # 远程对象是一个文件
                    if corresponding.isFile:  # 远程对象 和 本地对象 都是文件
                        # 校验hash
                        if corresponding.sha1 != file['hash']:
                            # 如果hash对不上，删除后进行下载
                            self.delete(corresponding)
                            self.download(file, corresponding)
                    else:  # 本地对象是一个目录
                        # 先删除本地的 目录 再下载远程端的 文件
                        self.delete(corresponding)
                        self.download(file, corresponding)

    def scanDeletableFiles(self, dir: File, tree: list, base: File):
        """只扫描需要删除的文件
        :param dir: 对应的本地目录对象
        :param tree: 与本地目录对应的远程目录
        :param base: 工作目录(更新根目录)，用于计算相对路径
        """

        for file in dir:
            corresponding = FileComparer.getNameInTree(file.name, tree)  # 参数获取远程端的对应对象，可能会返回None

            if corresponding is not None:  # 如果远程端也有这个文件
                if file.isDirectory:
                    if 'tree' in corresponding:
                        # 如果 本地对象 和 远程对象 都是目录，递归调用进行进一步判断
                        self.scanDeletableFiles(file, corresponding['tree'], base)
                # 其它情况均由scanDownloadableFiles进行处理了，这里不需要重复判断
            else:  # 远程端没有有这个文件，就直接删掉好了
                self.delete(file)

    @staticmethod
    def getNameInTree(_name: str, _tree: list):
        """在一个远程目录对象里获取一个文件对象"""
        for n in _tree:
            if n['name'] == _name:
                return n
        return None

    def delete(self, file: File):
        if file.isDirectory:
            for f in file:
                if 'tree' in f:
                    self.delete(f)
                else:
                    self.deleteList.append(f.relPath(self.basePath))
        self.deleteList.append(file.relPath(self.basePath))

    def download(self, node: dict, dir: File):
        if 'tree' in node:
            # 提前创建文件夹（即使是空文件夹）
            dir.append(node['name']).makeParentDirs()

            for n in node['tree']:
                dd = dir.append(n['name'])

                if 'tree' in n:
                    self.download(n, dd)
                else:
                    relPath = dd.relPath(self.basePath)
                    self.downloadList.append(relPath)
                    self.downloadMap[relPath] = n['length']
        else:
            relPath = dir.relPath(self.basePath)
            self.downloadList.append(relPath)
            self.downloadMap[relPath] = node['length']

    def compare(self, dir: File, tree: list):
        self.scanDownloadableFiles(dir, tree, dir)
        self.scanDeletableFiles(dir, tree, dir)