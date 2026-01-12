from functools import lru_cache

from pypinyin import Style, lazy_pinyin


def _is_chinese(char: str) -> bool:
    return '\u4e00' <= char <= '\u9fff'


@lru_cache(maxsize=1000)
def _convert_pinyin(text: str, style: Style) -> str:
    results: list[str] = []
    for char in text:
        if _is_chinese(char):
            pinyin = lazy_pinyin(char, style=style)
            results.extend(pinyin)
        elif char.isalnum() or char == '_':
            results.append(char)
        else:
            results.append('_')
    return '_'.join(filter(None, '_'.join(results).split('_')))


class PinyinConverter:
    def __init__(self, style: Style = Style.NORMAL):
        self.style = style

    def convert(self, text: str | None = None) -> str:
        if not text:
            return ''
        return _convert_pinyin(text, self.style)
