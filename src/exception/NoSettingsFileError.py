from src.exception.BasicWrappedError import BasicWrappedError
from src.utils.file import File


class NoSettingsFileError(BasicWrappedError):
    def __init__(self, path: File):
        super(NoSettingsFileError, self).__init__()

        self.title = 'Could not found the Setting-File'
        self.content = 'File not found: ' + path.path
