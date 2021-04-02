from src.exception.BasicWrappedError import BasicWrappedError


class NotInRightPathError(BasicWrappedError):
    def __init__(self, currentPath):
        super(NotInRightPathError, self).__init__()

        self.title = 'Could not found the directory: ../../.minecraft'
        self.content = f'Please put this file inside .minecraft/updater before executing'