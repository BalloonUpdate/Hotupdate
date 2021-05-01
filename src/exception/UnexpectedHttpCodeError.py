from src.exception.BasicWrappedError import BasicWrappedError


class UnexpectedHttpCodeError(BasicWrappedError):
    def __init__(self, url, httpStatus, data):
        super(UnexpectedHttpCodeError, self).__init__()

        self.content = f'The server did not return 200 as expected\nURL: {url}\nHTTP Code: {httpStatus}\n--------Raw Data Returned--------\n{data[:300]}'
        if len(data) > 300:
            self.content += '\n(and more)...'
