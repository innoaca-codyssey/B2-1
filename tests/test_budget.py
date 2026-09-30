from contextlib import redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from budget_app.cli import execute, parser
from budget_app.repository import Store
from budget_app.service import BudgetService


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.store = Store(self.directory)
        self.store.initialize()
        self.service = BudgetService(self.store)

    def tearDown(self):
        self.temp.cleanup()

    def add(self, day='2026-09-20', amount=1000, category='food', kind='expense'):
        return self.service.add(date=day, amount=amount, category=category, type=kind, memo='점심', tags=['meal'])

    def test_latest_order_after_date_edit_and_delete(self):
        a = self.add('2026-09-10')
        b = self.add('2026-09-20')
        self.assertEqual([t.id for t in self.service.transactions.stream()], [b.id, a.id])
        self.service.update(a.id, date='2026-09-30')
        self.assertEqual([t.id for t in self.service.transactions.stream()], [a.id, b.id])
        self.service.delete(a.id)
        self.assertEqual([t.id for t in self.service.transactions.stream()], [b.id])
        with self.assertRaises(ValueError):
            self.service.delete(a.id)

    def test_reopen_budget_search_and_category_use(self):
        self.add(amount=12000)
        self.service.budget('2026-09', 10000)
        reopened = BudgetService(Store(self.directory))
        self.assertIn('[경고] 예산 초과', reopened.summary('2026-09', 3))
        self.assertEqual(len(list(reopened.search('2026-09-01', '2026-09-30', 'food', 'expense', '점심', 'meal'))), 1)
        with self.assertRaises(ValueError):
            reopened.category('remove', 'food')
        reopened.category('add', 'coffee')
        reopened.category('remove', 'coffee')
        self.assertNotIn('coffee', reopened.categories())

    def test_failed_replace_preserves_original_and_removes_temp(self):
        a = self.add()
        before = (self.directory / 'transactions.jsonl').read_bytes()
        with patch('budget_app.repository.os.replace', side_effect=OSError('교체 실패')):
            with self.assertRaises(OSError):
                self.service.delete(a.id)
        self.assertEqual((self.directory / 'transactions.jsonl').read_bytes(), before)
        self.assertEqual(list(self.directory.glob('.tmp-*')), [])

    def test_bad_import_rolls_back_all_rows(self):
        self.add()
        before = (self.directory / 'transactions.jsonl').read_bytes()
        source = self.directory / 'input.csv'
        source.write_text('date,type,category,amount,memo,tags\n2026-09-01,expense,food,20,valid,\n2026-02-30,expense,food,20,bad,\n')
        with self.assertRaisesRegex(ValueError, '3행'):
            self.service.import_csv(source)
        self.assertEqual((self.directory / 'transactions.jsonl').read_bytes(), before)

    def test_csv_roundtrip_and_empty_month(self):
        self.add()
        output = self.directory / 'out.csv'
        self.assertEqual(self.service.export_csv(output, month='2026-09'), 1)
        self.assertEqual(self.service.import_csv(output), 1)
        self.assertIn('데이터 없음', self.service.summary('2026-08', 3))

    def test_invalid_cli_and_corrupt_file_have_nonzero_exit(self):
        args = parser().parse_args(['--data-dir', str(self.directory), 'update', '--id', 'missing', '--amount', '0'])
        with redirect_stdout(io.StringIO()) as output:
            status = execute(args)
        self.assertEqual(status, 1)
        self.assertIn('[힌트]', output.getvalue())
        (self.directory / 'transactions.jsonl').write_text('{broken\n')
        result = subprocess.run([sys.executable, '-m', 'budget_app', '--data-dir', str(self.directory), 'list'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('Traceback', result.stdout + result.stderr)

    def test_all_help_commands(self):
        commands = [['add'], ['list'], ['search'], ['summary'], ['budget'], ['budget', 'set'], ['category'], ['category', 'add'], ['category', 'list'], ['category', 'remove'], ['update'], ['delete'], ['import'], ['export']]
        for command in commands:
            with self.subTest(command=command):
                result = subprocess.run([sys.executable, '-m', 'budget_app', *command, '--help'], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0)
                self.assertIn('usage:', result.stdout)

    def test_invalid_inputs(self):
        for fields in [dict(day='2026-02-30'), dict(amount=0), dict(amount=-1), dict(kind='other'), dict(category='missing')]:
            with self.assertRaises(ValueError):
                self.add(**fields)


if __name__ == '__main__':
    unittest.main()
