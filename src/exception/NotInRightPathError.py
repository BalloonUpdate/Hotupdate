from src.exception.BasicWrappedError import BasicWrappedError


class NotInRightPathError(BasicWrappedError):
    def __init__(self, currentPath):
        super(NotInRightPathError, self).__init__()

        self.content = f'Could not found the directory: ../../.minecraft\nPlease put this file inside .minecraft/updater before executing'