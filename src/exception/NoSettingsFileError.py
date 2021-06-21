from src.exception.BasicWrappedError import BasicWrappedError
from src.utils.file import File


class NoSettingsFileError(BasicWrappedError):
    def __init__(self, path: File):
        super(NoSettingsFileError, self).__init__()

        self.content = 'The SettingFile not found : ' + path.path
        self.trans = '找不到配置文件'
