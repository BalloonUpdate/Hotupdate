class BasicWrappedError(Exception):
    def __init__(self, content=''):
        # self.title = title
        self.content = content

    def __str__(self):
        return self.content
