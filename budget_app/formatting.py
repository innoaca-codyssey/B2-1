import unicodedata


def width(text: str) -> int:
    return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in ('W', 'F') else 1 for c in text)


def cell(text: str, size: int, numeric=False, truncate=True) -> str:
    text = ' '.join(text.split())
    text = ''.join(c for c in text if ord(c) >= 32 and ord(c) != 127)
    if truncate and width(text) > size:
        output = ''
        for character in text:
            if width(output + character) > size - 3:
                break
            output += character
        text = output + '...'
    padding = ' ' * max(0, size - width(text))
    return padding + text if numeric else text + padding


def header() -> str:
    return ' | '.join(cell(t, w) for t, w in zip(['ID', 'DATE', 'TYPE', 'CATEGORY', 'AMOUNT', 'MEMO', 'TAGS'], [26, 10, 7, 12, 12, 24, 18]))


def row(transaction) -> str:
    values = [transaction.id, transaction.date, transaction.type, transaction.category, str(transaction.amount), transaction.memo, ','.join(transaction.tags or [])]
    return ' | '.join(cell(value, size, numeric=i == 4, truncate=i != 0) for i, (value, size) in enumerate(zip(values, [26, 10, 7, 12, 12, 24, 18])))
