from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import tempfile
from typing import Iterable, Iterator
from .models import Transaction


class Store:
    def __init__(self, directory: Path):
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def locked(self):
        with (self.directory / '.lock').open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def rows(self, name: str) -> Iterator[dict]:
        path = self.directory / (name + '.jsonl')
        with path.open(encoding='utf-8') as handle:
            for number, line in enumerate(handle, 1):
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError('객체가 아닙니다')
                    yield row
                except (ValueError, TypeError) as error:
                    raise ValueError(f'{path.name} {number}행 오류: {error}') from error

    def replace(self, name: str, rows: Iterable[dict]) -> None:
        """완성된 임시 파일만 원본 경로로 교체합니다."""
        fd, temporary = tempfile.mkstemp(dir=self.directory, prefix='.tmp-')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False) + '\n')
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.directory / (name + '.jsonl'))
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def initialize(self) -> None:
        defaults = [('transactions', []), ('categories', [{'name': n} for n in ['food', 'transport', 'rent', 'salary', 'etc']]), ('budgets', []), ('recurring', [])]
        for name, rows in defaults:
            if not (self.directory / (name + '.jsonl')).exists():
                self.replace(name, rows)


class TransactionRepository:
    def __init__(self, store: Store):
        self.store = store

    def stream(self) -> Iterator[Transaction]:
        for row in self.store.rows('transactions'):
            try:
                yield Transaction(**row)
            except TypeError as error:
                raise ValueError('거래 파일 형식 오류') from error

    def find(self, identifier: str) -> Transaction:
        for transaction in self.stream():
            if transaction.id == identifier:
                return transaction
        raise ValueError('없는 데이터: ' + identifier)

    def write(self, transaction: Transaction | None, remove_id: str = '') -> None:
        def merged():
            inserted = transaction is None
            for old in self.stream():
                if old.id == remove_id:
                    continue
                if transaction is not None and old.id == transaction.id:
                    raise ValueError('거래 id가 중복됩니다. 다시 등록하세요')
                if not inserted and (transaction.date, transaction.id) > (old.date, old.id):
                    yield transaction.record()
                    inserted = True
                yield old.record()
            if not inserted:
                yield transaction.record()
        self.store.replace('transactions', merged())
