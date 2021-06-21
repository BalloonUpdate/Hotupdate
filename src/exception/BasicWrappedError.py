class BasicWrappedError(Exception):
    def __init__(self, content='', trans=None):
        # self.title = title
        self.content = content
        self.trans = trans

    def __str__(self):
        return self.content
