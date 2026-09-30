from dataclasses import asdict, dataclass
from datetime import date
import re


def valid_date(value: str) -> str:
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('날짜는 YYYY-MM-DD 형식이어야 합니다')
    date.fromisoformat(value)
    return value


def valid_month(value: str) -> str:
    valid_date(value + '-01')
    return value


def positive(value: str | int) -> int:
    amount = int(value)
    if amount <= 0:
        raise ValueError('금액은 양수 정수여야 합니다')
    return amount


@dataclass
class Transaction:
    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: str = ''
    tags: list[str] | None = None

    def validate(self, categories: list[str]) -> None:
        valid_date(self.date)
        if self.type not in ('income', 'expense'):
            raise ValueError('타입은 income 또는 expense여야 합니다')
        if not isinstance(self.amount, int) or isinstance(self.amount, bool):
            raise ValueError('금액은 양수 정수여야 합니다')
        positive(self.amount)
        if self.category not in categories:
            raise ValueError('등록되지 않은 카테고리: ' + self.category)
        if not self.id or not isinstance(self.memo, str):
            raise ValueError('거래 id/메모 형식 오류')
        if self.tags is not None and (not isinstance(self.tags, list) or any(not isinstance(t, str) for t in self.tags)):
            raise ValueError('태그는 문자열 목록이어야 합니다')

    def record(self) -> dict:
        return asdict(self)
