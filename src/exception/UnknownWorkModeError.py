from src.exception.BasicWrappedError import BasicWrappedError


class UnknownWorkModeError(BasicWrappedError):
    def __init__(self, mode):
        super(UnknownWorkModeError, self).__init__()

        self.content = f'WorkMode not supported: {mode}'
        self.trans = '未知的工作模式'
