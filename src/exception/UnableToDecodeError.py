from src.exception.BasicWrappedError import BasicWrappedError


class UnableToDecodeError(BasicWrappedError):
    def __init__(self, raw, url, httpStatus, data):
        super(UnableToDecodeError, self).__init__()

        self.title = 'The Server returned a undecodable message'
        self.content = f'URL: {url}\nHTTP Code: {httpStatus}\n--------Raw Data Returned--------\n{data[:300]}'
        if len(data) > 300:
            self.content += '\n(and more)...'
