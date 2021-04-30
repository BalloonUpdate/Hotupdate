import traceback

from src.entry import Entry
from src.logging.LoggingSystem import LoggingSystem
from src.utils.file import File
from src.common import inDev, devDirectory

if __name__ == "__main__":

    # 检查运行库
    import clr
    if clr.FindAssembly('System.Collections') is None:
        print('AddReference!!')
        from src.common import inDev, devDirectory
        import sys
        if not inDev:
            temp = File(getattr(sys, '_MEIPASS', ''))
            sys.path.append(temp('dotnet').windowsPath)

    try:
        LoggingSystem.init()

        entry = Entry()
        entry.mainThread()
    except SystemExit:
        pass
    except BaseException:
        print(traceback.format_exc())
        errorFile = File('updater.error.log') if not inDev else File(devDirectory + '/updater.error.log')
        errorFile.content = traceback.format_exc()
