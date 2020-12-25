from src.newupdater.utils.file import File


class BasicDisplayableError(Exception):
    def __init__(self, title='', content=''):
        self.title = title
        self.content = content

    def __str__(self):
        return self.title+': '+self.content


class NotInRightPathError(BasicDisplayableError):
    def __init__(self, currentPath):
        super(NotInRightPathError, self).__init__()

        self.title = '找不到../../.minecraft 文件夹'
        self.content = f'请确认将本文件放置到{currentPath}/.minecraft/folder/updater.exe 再尝试执行'


class NoSettingsFileError(BasicDisplayableError):
    def __init__(self, path: File):
        super(NoSettingsFileError, self).__init__()

        self.title = '设置文件找不到'
        self.content = '请确认' + path.path + '文件存在'


class FailedToConnectError(BasicDisplayableError):
    def __init__(self, raw, url):
        super(FailedToConnectError, self).__init__()

        self.title = '无法连接到服务器'
        self.content = self.content = f'服务器响应超时\n{url}'


class UnableToDecodeError(BasicDisplayableError):
    def __init__(self, raw, url, httpStatus, data):
        super(UnableToDecodeError, self).__init__()

        self.title = '服务器返回了无法解码的信息'
        self.content = f'URL: {url}\nHTTP返回码: {httpStatus}\n--------以下原始数据--------\n{data[:300]}'
        if len(data) > 300:
            self.content += '\n...'


class UnexpectedTransmissionError(BasicDisplayableError):
    def __init__(self, raw, url):
        super(UnexpectedTransmissionError, self).__init__()
        self.title = '与服务器的连接意外中断'
        self.content = f'URL: {url}\n{str(raw)}'


class UnexpectedHttpCodeError(BasicDisplayableError):
    def __init__(self, url, httpStatus, data):
        super(UnexpectedHttpCodeError, self).__init__()
        self.title = '服务器没有按预期返回200'
        self.content = f'URL: {url}\nHTTP Code: {httpStatus}\n--------以下原始数据--------\n{data[:300]}'
        if len(data) > 300:
            self.content += '\n...'

# class FailedHttpRequestError(BasicDisplayableError):
#     def __init__(self, raw, url, httpStatus):
#         super(FailedHttpRequestError, self).__init__()
#
#         self.title = f'HTTP请求失败({httpStatus})'
#         self.content = str(raw)
