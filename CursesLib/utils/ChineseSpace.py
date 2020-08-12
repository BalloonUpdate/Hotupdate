import platform


def insertSpaceBehindChinese(text, spaceChar=' '):
    def findChinese(start, word):
        index = 0

        for ch in word[start:]:
            if '\u4e00' <= ch <= '\u9fff':
                return index + startAt
            index += 1
        return -1

    startAt = 0
    for i in range(0, 10):
        pos = findChinese(startAt, text)

        if pos != -1:
            text = text[:pos + 1] + spaceChar + text[pos + 1:]

            startAt = pos + 1
        else:
            break

    return text


def smartStretch(text, spaceChar=' '):
    if platform.platform().startswith('Windows-10'):
        return insertSpaceBehindChinese(text, spaceChar)
    return text

    # if sys.prefix == sys.base_prefix and False:
