from utils.File import File
from work_mode.BaseWorkMode import BaseWorkMode


class BMode(BaseWorkMode):
    """
    默认只同步存在于服务器的上的文件，服务器没有的文件不做任何变动
    如果指定了正则表达式，则会使用正则表达式进行删除
    匹配的文件会直接被删除，即使是存在于服务器的上的文件也是如此(高优先级)
    不匹配的文件会被忽略掉，并按第一行的规则进行处理
    """

    def walk(self, dir: File, tree: list, base: File):

        # 计算出要删除的文件
        for d in dir:
            if self.test(d.relPath(base)):
                self.delete(d)
                continue

        # 计算出要更新的文件
        for t in tree:
            d = dir.append(t['name'])
            dPath = d.relPath(base)

            # 如果是属于要删除的文件就不进行下载了
            if self.test(dPath):
                continue

            if d.exists:
                if 'tree' not in t:  # 远端是一个文件
                    if d.sha1 != t['hash']:
                        self.delete(d)
                        self.download(t, d)
                else:  # 远端是一个目录
                    self.walk(d, t['tree'], base)
            else:
                self.download(t, d)

    def scan(self, dir: File, tree: list):
        self.walk(dir, tree, dir)
        self.excludeSelf()
