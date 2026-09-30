import argparse
from functools import wraps
from itertools import islice
from pathlib import Path
from .models import positive
from .repository import Store
from .service import BudgetService


def errors(function):
    """CLI 경계에서 오류 출력과 종료 코드를 통일합니다."""
    @wraps(function)
    def wrapped(*args, **kwargs) -> int:
        try:
            function(*args, **kwargs)
            return 0
        except (ValueError, TypeError, KeyError, OSError, UnicodeError, EOFError) as error:
            print(f'[오류] {error}')
            print('[힌트] --help로 입력 형식을 확인하고 저장 파일과 접근 권한을 확인하세요.')
            return 1
        except KeyboardInterrupt:
            print('\n[오류] 입력을 취소했습니다.')
            return 1
    return wrapped


def count(value: str) -> int:
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError('양수 정수를 입력하세요')
    return n


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description='파일 기반 가계부')
    p.add_argument('--data-dir', type=Path, default=Path('data'))
    commands = p.add_subparsers(dest='command', required=True)
    commands.add_parser('add')
    listing = commands.add_parser('list')
    listing.add_argument('--limit', type=count, default=20)
    searching = commands.add_parser('search')
    searching.add_argument('--from', dest='start')
    searching.add_argument('--to', dest='end')
    searching.add_argument('--category')
    searching.add_argument('--type', dest='kind', choices=['income', 'expense'])
    searching.add_argument('--q', dest='query')
    searching.add_argument('--tag')
    summary = commands.add_parser('summary')
    summary.add_argument('--month', required=True)
    summary.add_argument('--top', type=count, default=3)
    budgets = commands.add_parser('budget').add_subparsers(dest='operation', required=True)
    b = budgets.add_parser('set')
    b.add_argument('--month', required=True)
    b.add_argument('--amount', type=int, required=True)
    categories = commands.add_parser('category').add_subparsers(dest='operation', required=True)
    for operation in ['add', 'list', 'remove']:
        categories.add_parser(operation)
    update = commands.add_parser('update')
    update.add_argument('--id', required=True)
    for field in ['date', 'type', 'category', 'memo', 'tags']:
        update.add_argument('--' + field)
    update.add_argument('--amount', type=int)
    delete = commands.add_parser('delete')
    delete.add_argument('--id', required=True)
    importer = commands.add_parser('import')
    importer.add_argument('--from', dest='source', type=Path, required=True)
    exporter = commands.add_parser('export')
    exporter.add_argument('--out', type=Path, required=True)
    exporter.add_argument('--month')
    exporter.add_argument('--from', dest='start')
    exporter.add_argument('--to', dest='end')
    return p


def display(records) -> None:
    seen = False
    for t in records:
        print(f'{t.id} | {t.date} | {t.type} | {t.category} | {t.amount} | {t.memo} | {",".join(t.tags or [])}')
        seen = True
    if not seen:
        print('데이터 없음')


@errors
def execute(a) -> None:
    store = Store(a.data_dir)
    with store.locked():
        store.initialize()
        service = BudgetService(store)
        if a.command == 'add':
            fields = dict(date=input('날짜(YYYY-MM-DD): ').strip(), type=input('타입(income/expense): ').strip(), category=input('카테고리: ').strip(), amount=positive(input('금액(양수): ')), memo=input('메모(선택): '), tags=[t.strip() for t in input('태그(쉼표로 구분): ').split(',') if t.strip()])
            print('[저장 완료] id=' + service.add(**fields).id)
        elif a.command == 'list':
            display(islice(service.transactions.stream(), a.limit))
        elif a.command == 'search':
            display(service.search(a.start, a.end, a.category, a.kind, a.query, a.tag))
        elif a.command == 'summary':
            print('\n'.join(service.summary(a.month, a.top)))
        elif a.command == 'budget':
            service.budget(a.month, a.amount)
            print(f'[저장 완료] {a.month} 예산 {a.amount}원')
        elif a.command == 'category':
            if a.operation == 'list':
                print('\n'.join(service.categories()) or '카테고리 없음')
            else:
                name = input('카테고리명: ').strip()
                service.category(a.operation, name)
                print('[완료] category=' + name)
        elif a.command == 'update':
            fields = {field: getattr(a, field) for field in ['date', 'type', 'category', 'amount', 'memo', 'tags']}
            if not any(v is not None for v in fields.values()):
                raise ValueError('수정할 필드를 지정하세요')
            if fields['tags'] is not None:
                fields['tags'] = [t.strip() for t in fields['tags'].split(',') if t.strip()]
            service.update(a.id, **fields)
            print('[수정 완료] id=' + a.id)
        elif a.command == 'delete':
            service.delete(a.id)
            print('[삭제 완료] id=' + a.id)
        elif a.command == 'import':
            print(f'[완료] imported={service.import_csv(a.source)}')
        elif a.command == 'export':
            if a.month and (a.start or a.end) or not (a.month or a.start or a.end):
                raise ValueError('--month 또는 --from/--to 중 한 가지 조건을 지정하세요')
            n = service.export_csv(a.out, month=a.month, start=a.start, end=a.end)
            print(f'[완료] {a.out} ({n} records)')


def main() -> int:
    return execute(parser().parse_args())
