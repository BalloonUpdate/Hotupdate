from src.utils.file import File


class BasicDisplayableError(Exception):
    def __init__(self, title='', content=''):
        self.title = title
        self.content = content

    def __str__(self):
        return self.title+': '+self.content


class NotInRightPathError(BasicDisplayableError):
    def __init__(self, currentPath):
        super(NotInRightPathError, self).__init__()

        self.title = 'Could not found the directory: ../../.minecraft'
        self.content = f'Please put this file inside .minecraft/updater before executing'


class NoSettingsFileError(BasicDisplayableError):
    def __init__(self, path: File):
        super(NoSettingsFileError, self).__init__()

        self.title = 'Could not found the Setting-File'
        self.content = 'File not found: ' + path.path


class FailedToConnectError(BasicDisplayableError):
    def __init__(self, raw, url):
        super(FailedToConnectError, self).__init__()

        self.title = 'Could not connect to the server'
        self.content = self.content = f'The server failed to respond in time \n{url}'


class UnableToDecodeError(BasicDisplayableError):
    def __init__(self, raw, url, httpStatus, data):
        super(UnableToDecodeError, self).__init__()

        self.title = 'The Server returned a message which could not be decoded'
        self.content = f'URL: {url}\nHTTP Code: {httpStatus}\n--------Raw Data Returned--------\n{data[:300]}'
        if len(data) > 300:
            self.content += '\n(and more)...'


class UnexpectedTransmissionError(BasicDisplayableError):
    def __init__(self, raw, url):
        super(UnexpectedTransmissionError, self).__init__()
        self.title = 'Connection was unexpectedly interrupted'
        self.content = f'The Connection to the server was unexpectedly interrupted\nURL: {url}\n{str(raw)}'


class UnexpectedHttpCodeError(BasicDisplayableError):
    def __init__(self, url, httpStatus, data):
        super(UnexpectedHttpCodeError, self).__init__()
        self.title = 'The server did not return 200 as expected'
        self.content = f'URL: {url}\nHTTP Code: {httpStatus}\n--------Raw Data Returned--------\n{data[:300]}'
        if len(data) > 300:
            self.content += '\n(and more)...'

# class FailedHttpRequestError(BasicDisplayableError):
#     def __init__(self, raw, url, httpStatus):
#         super(FailedHttpRequestError, self).__init__()
#
#         self.title = f'HTTP请求失败({httpStatus})'
#         self.content = str(raw)
