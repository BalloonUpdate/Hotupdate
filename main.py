import traceback

from src.entry import Entry
from src.utils.file import File

if __name__ == "__main__":

    # 检查运行库
    import clr
    if clr.FindAssembly('System.Collections') is None:
        print('AddReference!!')
        from src.common import inDev
        import sys
        if not inDev:
            temp = File(getattr(sys, '_MEIPASS', ''))
            sys.path.append(temp('dotnet').windowsPath)

    try:
        entry = Entry()
        entry.main()
    except Exception:
        print(traceback.format_exc())
        File('updater.error.log').content = traceback.format_exc()