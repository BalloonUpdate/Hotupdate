import traceback

from src.entry import Entry
from src.logging.LoggingSystem import LoggingSystem
from src.utils.file import File
from src.common import inDev, devDirectory

if __name__ == "__main__":

    try:
        LoggingSystem.init()

        entry = Entry()
        entry.mainThread()
    except SystemExit:
        pass
    except BaseException:
        print(traceback.format_exc())
        input("任意键继续...")
