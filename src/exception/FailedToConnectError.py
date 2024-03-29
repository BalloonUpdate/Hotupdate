from src.exception.BasicWrappedError import BasicWrappedError


class FailedToConnectError(BasicWrappedError):
    def __init__(self, raw, url):
        super(FailedToConnectError, self).__init__()

        self.content = self.content = f'The server failed to respond timely \n{url}'
