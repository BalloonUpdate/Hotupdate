from src.exception.BasicWrappedError import BasicWrappedError


class NotInRightPathError(BasicWrappedError):
    def __init__(self, currentPath):
        super(NotInRightPathError, self).__init__()

        self.content = f'找不到../../.minecraft目录'
        self.trans = '找不到../../.minecraft目录'
