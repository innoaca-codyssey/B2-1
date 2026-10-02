import csv
import calendar
from dataclasses import replace
from datetime import datetime
import os
from pathlib import Path
import tempfile
from typing import Iterator
from uuid import uuid4
import zipfile
from .models import Transaction, positive, valid_date, valid_month
from .repository import Store, TransactionRepository

CSV_FIELDS = ['date', 'type', 'category', 'amount', 'memo', 'tags']


class BudgetService:
    def __init__(self, store: Store):
        self.store = store
        self.transactions = TransactionRepository(store)

    def categories(self) -> list[str]:
        try:
            return [r['name'] for r in self.store.rows('categories')]
        except KeyError as error:
            raise ValueError('카테고리 파일 형식 오류') from error

    def category(self, operation: str, name: str) -> None:
        names = self.categories()
        if not name.strip():
            raise ValueError('카테고리 이름이 비어 있습니다')
        if operation == 'add':
            if name in names:
                raise ValueError('이미 등록된 카테고리: ' + name)
            names.append(name)
        else:
            if name not in names:
                raise ValueError('없는 카테고리: ' + name)
            if any(t.category == name for t in self.transactions.stream()):
                raise ValueError('사용 중인 카테고리는 삭제할 수 없습니다')
            if any(r['category'] == name for r in self.store.rows('recurring')):
                raise ValueError('반복 규칙에서 사용하는 카테고리는 삭제할 수 없습니다')
            names.remove(name)
        self.store.replace('categories', ({'name': n} for n in names))

    def add(self, **fields) -> Transaction:
        transaction = Transaction(id='TX-' + uuid4().hex[:12], **fields)
        transaction.validate(self.categories())
        self.transactions.write(transaction)
        return transaction

    def update(self, identifier: str, **fields) -> None:
        old = self.transactions.find(identifier)
        transaction = replace(old, **{k: v for k, v in fields.items() if v is not None})
        transaction.validate(self.categories())
        self.transactions.write(transaction, identifier)

    def delete(self, identifier: str) -> None:
        self.transactions.find(identifier)
        self.transactions.write(None, identifier)

    def search(self, start: str | None = None, end: str | None = None, category: str | None = None, kind: str | None = None, query: str | None = None, tag: str | None = None, month: str | None = None) -> Iterator[Transaction]:
        if start:
            valid_date(start)
        if end:
            valid_date(end)
        if start and end and start > end:
            raise ValueError('시작일이 종료일보다 늦습니다')
        if month:
            valid_month(month)
        for t in self.transactions.stream():
            if start and t.date < start or end and t.date > end:
                continue
            if month and not t.date.startswith(month):
                continue
            if category and t.category != category or kind and t.type != kind:
                continue
            if query and query.casefold() not in t.memo.casefold():
                continue
            if tag and tag not in (t.tags or []):
                continue
            yield t

    def budget(self, month: str, amount: int) -> None:
        valid_month(month)
        positive(amount)
        rows = list(self.store.rows('budgets'))
        rows = [r for r in rows if r.get('month') != month]
        rows.append({'month': month, 'amount': amount})
        self.store.replace('budgets', rows)

    def summary(self, month: str, top: int) -> list[str]:
        valid_month(month)
        income = expense = count = 0
        categories: dict[str, int] = {}
        for transaction in self.search(month=month):
            count += 1
            if transaction.type == 'income':
                income += transaction.amount
            else:
                expense += transaction.amount
                categories[transaction.category] = categories.get(transaction.category, 0) + transaction.amount
        output = [] if count else ['데이터 없음']
        output.extend([f'총 수입: {income}원', f'총 지출: {expense}원', f'잔액: {income - expense}원'])
        try:
            for row in self.store.rows('budgets'):
                if row['month'] == month:
                    amount = positive(row['amount'])
                    output.append(f'예산: {amount}원 (사용률 {expense / amount * 100:.1f}%)')
                    if expense > amount:
                        output.append('[경고] 예산 초과')
        except KeyError as error:
            raise ValueError('예산 파일 형식 오류') from error
        for name, amount in sorted(categories.items(), key=lambda pair: (-pair[1], pair[0]))[:top]:
            output.append(f'{name}: {amount}원')
        return output

    def import_csv(self, path: Path) -> int:
        new = []
        categories = self.categories()
        with path.open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)) or not set(CSV_FIELDS[:4]).issubset(reader.fieldnames) or set(reader.fieldnames) - set(CSV_FIELDS):
                raise ValueError('CSV 헤더는 date,type,category,amount,memo,tags를 사용합니다')
            for number, row in enumerate(reader, 2):
                try:
                    if None in row or any(v is None for v in row.values()):
                        raise ValueError('열 수가 헤더와 다릅니다')
                    t = Transaction('TX-' + uuid4().hex[:12], row['type'], row['date'], positive(row['amount']), row['category'], row.get('memo', ''), [v.strip() for v in row.get('tags', '').split(',') if v.strip()])
                    t.validate(categories)
                    new.append(t)
                except (ValueError, TypeError) as error:
                    raise ValueError(f'CSV {number}행: {error}. 아무 거래도 반영하지 않았습니다') from error
        all_rows = list(self.transactions.stream()) + new
        all_rows.sort(key=lambda t: (t.date, t.id), reverse=True)
        self.store.replace('transactions', (t.record() for t in all_rows))
        return len(new)

    def export_csv(self, path: Path, **filters) -> int:
        if path.resolve() in [p.resolve() for p in self.store.directory.iterdir()]:
            raise ValueError('내보내기 경로는 저장 파일과 분리하세요')
        count = 0
        # 조건 검증이 실패해도 기존 출력 파일을 덮어쓰지 않습니다.
        records = self.search(**filters)
        first = next(records, None)
        with path.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            def rows():
                if first:
                    yield first
                yield from records
            for t in rows():
                row = t.record()
                del row['id']
                row['tags'] = ','.join(t.tags or [])
                writer.writerow(row)
                count += 1
        return count

    def backup(self, directory: Path) -> Path:
        """잠금 안에서 저장 파일을 동일 시점의 ZIP으로 보존합니다."""
        directory.mkdir(parents=True, exist_ok=True)
        name = 'budget-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '-' + uuid4().hex[:6] + '.zip'
        target = directory / name
        fd, temporary = tempfile.mkstemp(dir=directory, prefix='.backup-')
        os.close(fd)
        try:
            with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for store_name in ['transactions', 'categories', 'budgets', 'recurring']:
                    path = self.store.directory / (store_name + '.jsonl')
                    archive.write(path, arcname=path.name)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return target

    def add_recurring(self, day: int, **fields) -> str:
        if not 1 <= day <= 31:
            raise ValueError('반복일은 1~31을 사용하세요')
        identifier = 'RULE-' + uuid4().hex[:12]
        template = Transaction(id=identifier, date='2000-01-01', **fields)
        template.validate(self.categories())
        records = list(self.store.rows('recurring'))
        if any(r['id'] == identifier for r in records):
            raise ValueError('반복 규칙 id 중복입니다. 다시 등록하세요')
        record = template.record()
        record.pop('date')
        record['day'] = day
        records.append(record)
        self.store.replace('recurring', records)
        return identifier

    def generate_recurring(self, month: str) -> int:
        valid_month(month)
        year, number = map(int, month.split('-'))
        existing = list(self.transactions.stream())
        ids = {t.id for t in existing}
        new = []
        for record in self.store.rows('recurring'):
            identifier = 'TX-R-' + record['id'].removeprefix('RULE-') + '-' + month.replace('-', '')
            if not 1 <= record['day'] <= 31:
                raise ValueError('반복 규칙의 날짜를 확인하세요')
            day = min(record['day'], calendar.monthrange(year, number)[1])
            fields = {key: value for key, value in record.items() if key not in ('id', 'day')}
            transaction = Transaction(id=identifier, date=f'{month}-{day:02}', **fields)
            transaction.validate(self.categories())
            if identifier not in ids:
                new.append(transaction)
                ids.add(identifier)
        combined = existing + new
        combined.sort(key=lambda t: (t.date, t.id), reverse=True)
        self.store.replace('transactions', (t.record() for t in combined))
        return len(new)
