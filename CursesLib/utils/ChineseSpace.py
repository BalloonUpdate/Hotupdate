import sys


def insertSpaceBehindChinese(text, spaceChar=' '):
    def findChinese(start, word):
        index = 0

        for ch in word[start:]:
            if '\u4e00' <= ch <= '\u9fff':
                # self.debug(f"-------{ch}|{index}|{word[start:]}")
                # self.debug(f"-------[{ch}]")
                return index + startAt
            index += 1
        return -1

    startAt = 0
    for i in range(0, 10):
        pos = findChinese(startAt, text)

        if pos != -1:
            # self.debug(f"<{raw} at {startAt}>")
            # self.debug(' '+(' '*pos)+f'^ at {str(pos)}')
            text = text[:pos + 1] + spaceChar + text[pos + 1:]

            startAt = pos + 1
        else:
            break

    return text


def smartStretch(text, spaceChar=' '):
    if sys.prefix == sys.base_prefix or True:
        return insertSpaceBehindChinese(text, spaceChar)
    else:
        text
