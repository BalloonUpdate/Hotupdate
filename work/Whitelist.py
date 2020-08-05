from File import File
from work.B import B


class Whitelist(B):

    @staticmethod
    def getNameInTree(_name: str, _tree: list):
        for n in _tree:
            if n['name'] == _name:
                return n
        return None

    def PScan(self, dir: File, tree: list):
        """扫描新文件或者修改过的文件(不包括被删除的)"""

        for t in tree:
            d = dir.child(t['name'])

            if not d.exists:  # 文件已经被删除了
                self.download(t, d)
            else:  # 文件没有被删除
                if 'tree' in t:  # 理应是一个文件夹
                    if d.isFile:  # 实际却是一个文件
                        self.delete(d)
                        self.download(t, d)
                    else:  # 实际也是一个文件夹
                        self.PScan(d, t['tree'])
                else:  # 理应是一个文件
                    if d.isFile:  # 实际也是一个文件
                        if d.sha1 != t['hash']:
                            self.delete(d)
                            self.download(t, d)
                    else:  # 实际却是一个文件夹
                        self.delete(d)
                        self.download(t, d)

    def NScan(self, dir: File, tree: list):
        """扫描被删除的文件，不包括新文件或者修改过的文件，这类情况均由PScan()处理"""

        for d in dir:
            t = Whitelist.getNameInTree(d.name, tree)  # 尝试反向获取对应的文件信息

            if t is not None:  # 能获取到信息
                if d.isDirectory:
                    if 'tree' in t:
                        self.NScan(d, t['tree'])
            else:  # 获取不到
                self.delete(d)

    def scan(self, dir: File, tree: list):
        self.PScan(dir, tree)
        self.NScan(dir, tree)

