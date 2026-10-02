from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from budget_app.cli import display
from budget_app.formatting import row, width
from budget_app.models import Transaction
from budget_app.repository import Store
from budget_app.service import BudgetService


class BonusTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / 'data')
        self.store.initialize()
        self.service = BudgetService(self.store)

    def tearDown(self):
        self.temp.cleanup()

    def rule(self, day=31):
        return self.service.add_recurring(day, type='expense', category='rent', amount=1000, memo='월세', tags=[])

    def test_month_end_leap_and_idempotence(self):
        self.rule()
        self.assertEqual(self.service.generate_recurring('2028-02'), 1)
        self.assertEqual(self.service.generate_recurring('2028-02'), 0)
        self.assertEqual(self.service.generate_recurring('2027-02'), 1)
        self.assertEqual([t.date for t in self.service.transactions.stream()], ['2028-02-29','2027-02-28'])

    def test_bad_rule_rolls_back_all_generation(self):
        self.rule()
        records=list(self.store.rows('recurring'))
        records.append(dict(records[0], id='RULE-bad', amount=0))
        self.store.replace('recurring', records)
        before=(self.store.directory/'transactions.jsonl').read_bytes()
        with self.assertRaises(ValueError):
            self.service.generate_recurring('2026-10')
        self.assertEqual((self.store.directory/'transactions.jsonl').read_bytes(),before)

    def test_category_rule_reference_and_invalid_day(self):
        self.rule()
        with self.assertRaises(ValueError):
            self.service.category('remove','rent')
        for day in [0,32]:
            with self.assertRaises(ValueError):
                self.rule(day)

    def test_backup_roundtrip_and_unique_names(self):
        self.rule();self.service.generate_recurring('2026-10')
        first=self.service.backup(self.root/'backups')
        second=self.service.backup(self.root/'backups')
        self.assertNotEqual(first,second)
        with zipfile.ZipFile(first) as archive:
            self.assertEqual(len(archive.namelist()),4)
            for name in archive.namelist():
                self.assertEqual(archive.read(name),(self.store.directory/name).read_bytes())

    def test_table_unicode_alignment_and_stream(self):
        a=Transaction('TX-1','expense','2026-10-01',10,'food','점심',[])
        b=Transaction('TX-2','income','2026-10-02',1000,'salary','salary',[])
        self.assertEqual([width(c) for c in row(a).split(' | ')],[width(c) for c in row(b).split(' | ')])
        consumed=[]
        def stream():
            for t in [a,b]:
                consumed.append(t.id);yield t
        with redirect_stdout(io.StringIO()) as output:
            display(stream())
        self.assertEqual(consumed,['TX-1','TX-2'])
        self.assertIn('AMOUNT',output.getvalue())
        a.memo = '줄1\n줄2\t' + '한글' * 30
        self.assertNotIn('\n',row(a))
        self.assertNotIn('\t',row(a))


if __name__ == '__main__':
    unittest.main()
