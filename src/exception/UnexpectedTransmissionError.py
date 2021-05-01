from src.exception.BasicWrappedError import BasicWrappedError


class UnexpectedTransmissionError(BasicWrappedError):
    def __init__(self, raw, url):
        super(UnexpectedTransmissionError, self).__init__()

        self.content = f'The Connection to the server was unexpectedly interrupted\nURL: {url}\n{str(raw)}'
