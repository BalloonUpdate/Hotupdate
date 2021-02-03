import traceback
from src.entry import Entry

if __name__ == "__main__":
    try:
        entry = Entry()
        entry.main()
    except Exception:
        print(traceback.format_exc())