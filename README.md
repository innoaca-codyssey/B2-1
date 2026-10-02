# B2-1: 나만의 용돈 기입장 프로그램 만들기

수입과 지출을 JSONL 파일에 저장하는 콘솔 가계부입니다. 거래 검색, 수정과 삭제, 월별 요약, 예산, 카테고리, CSV 입출력을 제공합니다.

## 실행 방법

Python 3.10 이상에서 표준 라이브러리만 사용합니다.

```bash
python3 -m budget_app --help
python3 -m budget_app --data-dir ./data add
```

거래 추가와 카테고리 추가/삭제는 대화형 입력을 사용합니다. 거래 수정은 옵션 방식으로 고정합니다.

## 저장 형식

`--data-dir`의 기본값은 `./data`입니다. `transactions.jsonl`, `categories.jsonl`, `budgets.jsonl`로 나눠 저장합니다. 카테고리의 초기값은 food, transport, rent, salary, etc입니다.

CSV는 UTF-8, 헤더 포함 형식이며 열은 `date,type,category,amount,memo,tags`입니다. 금액은 양수 정수이고, tags는 쉼표로 구분합니다. 쉼표를 포함한 필드는 CSV의 큰따옴표 규칙을 적용합니다. 가져오기는 전체 입력을 먼저 검증한 뒤 반영합니다.

## 실행 환경

```bash
$ python3 --version
Python 3.14.7
```

macOS arm64에서 실행했습니다. 외부 패키지는 설치하지 않습니다.

## 거래 저장과 오류 처리

```bash
$ python3 -m unittest discover -s tests -v
test_all_help_commands (test_budget.BudgetTests.test_all_help_commands) ... ok
test_bad_import_rolls_back_all_rows (test_budget.BudgetTests.test_bad_import_rolls_back_all_rows) ... ok
test_csv_roundtrip_and_empty_month (test_budget.BudgetTests.test_csv_roundtrip_and_empty_month) ... ok
test_failed_replace_preserves_original_and_removes_temp (test_budget.BudgetTests.test_failed_replace_preserves_original_and_removes_temp) ... ok
test_invalid_cli_and_corrupt_file_have_nonzero_exit (test_budget.BudgetTests.test_invalid_cli_and_corrupt_file_have_nonzero_exit) ... ok
test_invalid_inputs (test_budget.BudgetTests.test_invalid_inputs) ... ok
test_latest_order_after_date_edit_and_delete (test_budget.BudgetTests.test_latest_order_after_date_edit_and_delete) ... ok
test_reopen_budget_search_and_category_use (test_budget.BudgetTests.test_reopen_budget_search_and_category_use) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.871s

OK
```

날짜를 수정하면 파일 안에서도 최신순 위치를 다시 잡습니다. 교체 실패와 잘못된 CSV 입력에서는 원본 파일을 유지합니다. 명령별 도움말과 오류 종료 코드도 검사했습니다.

## 거래 검색과 월별 요약

```bash
$ printf '2026-09-01\nincome\nsalary\n3000000\n월급\nmonthly\n' | python3 -m budget_app --data-dir ../lab/demo-data add
날짜(YYYY-MM-DD): 타입(income/expense): 카테고리: 금액(양수): 메모(선택): 태그(쉼표로 구분): [저장 완료] id=TX-0072ea482b5a

$ printf '2026-09-20\nexpense\nfood\n15000\n점심\nmeal\n' | python3 -m budget_app --data-dir ../lab/demo-data add
날짜(YYYY-MM-DD): 타입(income/expense): 카테고리: 금액(양수): 메모(선택): 태그(쉼표로 구분): [저장 완료] id=TX-4c6e6f283154

$ python3 -m budget_app --data-dir ../lab/demo-data list --limit 3
TX-4c6e6f283154 | 2026-09-20 | expense | food | 15000 | 점심 | meal
TX-0072ea482b5a | 2026-09-01 | income | salary | 3000000 | 월급 | monthly

$ python3 -m budget_app --data-dir ../lab/demo-data search --from 2026-09-01 --to 2026-09-30 --category food --type expense --q 점심 --tag meal
TX-4c6e6f283154 | 2026-09-20 | expense | food | 15000 | 점심 | meal

$ python3 -m budget_app --data-dir ../lab/demo-data budget set --month 2026-09 --amount 10000
[저장 완료] 2026-09 예산 10000원

$ python3 -m budget_app --data-dir ../lab/demo-data summary --month 2026-09 --top 3
총 수입: 3000000원
총 지출: 15000원
잔액: 2985000원
예산: 10000원 (사용률 150.0%)
[경고] 예산 초과
food: 15000원

```

목록과 검색은 날짜 내림차순으로 저장된 JSONL을 한 행씩 읽습니다. 조회 제한이 있으면 필요한 행에서 읽기를 멈춥니다. 예산은 거래 파일과 분리되어 다음 실행에서도 유지됩니다.

## 수정과 CSV 입출력

```bash
$ printf 'coffee\n' | python3 -m budget_app --data-dir ../lab/demo-data category add
카테고리명: [완료] category=coffee
exit=0

$ python3 -m budget_app --data-dir ../lab/demo-data category list
food
transport
rent
salary
etc
coffee
exit=0

$ printf 'food\n' | python3 -m budget_app --data-dir ../lab/demo-data category remove
카테고리명: [오류] 사용 중인 카테고리는 삭제할 수 없습니다
[힌트] --help로 입력 형식을 확인하고 저장 파일과 접근 권한을 확인하세요.
exit=1

$ python3 -m budget_app --data-dir ../lab/demo-data update --id TX-4c6e6f283154 --amount 12000 --memo '점심 수정'
[수정 완료] id=TX-4c6e6f283154
exit=0

$ python3 -m budget_app --data-dir ../lab/demo-data export --out ../lab/export.csv --month 2026-09
[완료] ../lab/export.csv (2 records)
exit=0

$ cat ../lab/export.csv
date,type,category,amount,memo,tags
2026-09-20,expense,food,12000,점심 수정,meal
2026-09-01,income,salary,3000000,월급,monthly
exit=0

$ python3 -m budget_app --data-dir ../lab/import-data import --from ../lab/export.csv
[완료] imported=2
exit=0

$ python3 -m budget_app --data-dir ../lab/import-data list
TX-2ba4f38ba778 | 2026-09-20 | expense | food | 12000 | 점심 수정 | meal
TX-9c47450955b0 | 2026-09-01 | income | salary | 3000000 | 월급 | monthly
exit=0

$ python3 -m budget_app --data-dir ../lab/demo-data delete --id TX-4c6e6f283154
[삭제 완료] id=TX-4c6e6f283154
exit=0

$ python3 -m budget_app --data-dir ../lab/demo-data delete --id TX-4c6e6f283154
[오류] 없는 데이터: TX-4c6e6f283154
[힌트] --help로 입력 형식을 확인하고 저장 파일과 접근 권한을 확인하세요.
exit=1

$ printf 'coffee\n' | python3 -m budget_app --data-dir ../lab/demo-data category remove
카테고리명: [완료] category=coffee
exit=0

$ python3 -m budget_app --data-dir ../lab/demo-data summary --month 2026-08
데이터 없음
총 수입: 0원
총 지출: 0원
잔액: 0원
exit=0

```

사용 중인 카테고리는 삭제를 막습니다. CSV에서 id는 내보내지 않으며, 가져오기는 새 id를 부여합니다. 없는 id는 오류와 해결 힌트를 출력하고 1로 종료합니다. 위 exit 값은 각 명령의 종료 코드입니다.

## 코드 구조와 저장 정책

`models.py`의 Transaction은 필드와 검증을 맡습니다. Store는 JSONL 읽기와 원자적 교체, TransactionRepository는 최신순 거래 순회와 id 조회를 담당합니다. BudgetService는 사용 중인 카테고리 삭제 금지, 월별 집계, CSV 검증을 처리합니다. CLI는 인자와 대화형 입력, 메시지와 종료 코드를 관리합니다.

JSONL은 태그 목록과 문자열을 그대로 저장할 수 있고 행별 파싱이 가능합니다. CSV는 다른 프로그램과 교환하기 좋지만 쉼표와 줄바꿈을 인코딩해야 하므로 입출력용으로 사용합니다. `stream() -> Iterator[Transaction]`은 JSON 객체를 Transaction으로 바꾸고 yield합니다. list는 islice로 제한을 적용하고 search는 조건에 맞는 거래만 yield합니다. 전체 목록을 만들지 않으므로 조회 메모리는 거래 수에 비례해 늘지 않습니다.

최신순 조회를 위해 저장 시 날짜와 id를 내림차순으로 유지합니다. 단건 추가, 수정, 삭제는 파일을 한 번 순회해 같은 폴더의 임시 파일에 기록하고 fsync 후 os.replace로 교체합니다. 중간 실패 시 임시 파일을 삭제하며 기존 파일은 유지합니다. 프로세스끼리의 동시 수정은 데이터 디렉토리의 파일 잠금으로 직렬화합니다. macOS와 Linux에서 fcntl을 사용합니다.

errors 데코레이터는 파일 오류와 검증 오류를 CLI 경계에서 처리합니다. 저장소에서 출력하지 않으므로 서비스 테스트에서 같은 예외를 검사할 수 있습니다. `search(...) -> Iterator[Transaction]`과 `budget(month: str, amount: int) -> None` 같은 타입 힌트는 반환값과 인자 계약을 명시합니다. 실행 시 타입을 자동으로 검증하는 장치는 아니므로 날짜와 금액의 실제 검증은 별도로 수행합니다.

10만 건에서는 list의 제한 조회보다 수정 시 전체 재작성, 조건 검색의 전수 순회, CSV import의 정렬과 전체 메모리 사용이 병목입니다. 규모가 더 커지면 날짜/id 인덱스와 트랜잭션을 제공하는 DB로 이전하거나 외부 정렬을 적용할 수 있습니다. 현재 import는 전체 CSV 검증 후 한 번 교체하는 방식입니다. 깨진 행이 하나라도 있으면 행 번호를 출력하고 전체 반영을 취소합니다. 부분 성공에 따른 중복 재시도를 피하기 위한 선택입니다.

## 명령 예시

```bash
python3 -m budget_app --data-dir ./data category add
python3 -m budget_app --data-dir ./data update --id TX-... --date 2026-09-30 --tags meal,work
python3 -m budget_app --data-dir ./data delete --id TX-...
python3 -m budget_app --data-dir ./data export --out export.csv --from 2026-09-01 --to 2026-09-30
python3 -m budget_app --data-dir ./data import --from import.csv
python3 -m unittest discover -s tests -v
```

## 백업과 반복 내역 검증

```bash
$ python3 -m unittest discover -s tests -v
test_all_help_commands (test_budget.BudgetTests.test_all_help_commands) ... ok
test_bad_import_rolls_back_all_rows (test_budget.BudgetTests.test_bad_import_rolls_back_all_rows) ... ok
test_csv_roundtrip_and_empty_month (test_budget.BudgetTests.test_csv_roundtrip_and_empty_month) ... ok
test_failed_replace_preserves_original_and_removes_temp (test_budget.BudgetTests.test_failed_replace_preserves_original_and_removes_temp) ... ok
test_invalid_cli_and_corrupt_file_have_nonzero_exit (test_budget.BudgetTests.test_invalid_cli_and_corrupt_file_have_nonzero_exit) ... ok
test_invalid_inputs (test_budget.BudgetTests.test_invalid_inputs) ... ok
test_latest_order_after_date_edit_and_delete (test_budget.BudgetTests.test_latest_order_after_date_edit_and_delete) ... ok
test_reopen_budget_search_and_category_use (test_budget.BudgetTests.test_reopen_budget_search_and_category_use) ... ok
test_backup_roundtrip_and_unique_names (testbonus.BonusTests.test_backup_roundtrip_and_unique_names) ... ok
test_bad_rule_rolls_back_all_generation (testbonus.BonusTests.test_bad_rule_rolls_back_all_generation) ... ok
test_category_rule_reference_and_invalid_day (testbonus.BonusTests.test_category_rule_reference_and_invalid_day) ... ok
test_month_end_leap_and_idempotence (testbonus.BonusTests.test_month_end_leap_and_idempotence) ... ok
test_table_unicode_alignment_and_stream (testbonus.BonusTests.test_table_unicode_alignment_and_stream) ... ok

----------------------------------------------------------------------
Ran 13 tests in 0.835s

OK
```

백업의 네 저장 파일이 원본과 같은지, 같은 달 재생성의 중복 방지, 윤년/말일 처리와 전체 생성 실패 시 원본 보존을 검사했습니다. 테이블은 한글 폭과 줄바꿈을 고려하고 거래를 순회하면서 출력합니다.

## 반복 내역 생성과 백업

```bash
$ printf 'income\nsalary\n3000000\n월급\nmonthly\n25\n' | python3 -m budget_app --data-dir ../lab/bonus-data recurring add
타입(income/expense): 카테고리: 금액(양수): 메모(선택): 태그(쉼표로 구분): 매월 날짜(1~31): [저장 완료] id=RULE-02121f7aa752

$ printf 'expense\nrent\n500000\n월세\nmonthly\n31\n' | python3 -m budget_app --data-dir ../lab/bonus-data recurring add
타입(income/expense): 카테고리: 금액(양수): 메모(선택): 태그(쉼표로 구분): 매월 날짜(1~31): [저장 완료] id=RULE-edbe0b3fa74f

$ python3 -m budget_app --data-dir ../lab/bonus-data recurring list
RULE-02121f7aa752 | 매월 25일 | income | salary | 3000000
RULE-edbe0b3fa74f | 매월 31일 | expense | rent | 500000

$ python3 -m budget_app --data-dir ../lab/bonus-data recurring generate --month 2026-10
[완료] 2026-10 generated=2

$ python3 -m budget_app --data-dir ../lab/bonus-data recurring generate --month 2026-10
[완료] 2026-10 generated=0

$ python3 -m budget_app --data-dir ../lab/bonus-data list
ID                         | DATE       | TYPE    | CATEGORY     | AMOUNT       | MEMO                     | TAGS              
-------------------------------------------------------------------------------------------------------------------------------
TX-R-edbe0b3fa74f-202610   | 2026-10-31 | expense | rent         |       500000 | 월세                     | monthly           
TX-R-02121f7aa752-202610   | 2026-10-25 | income  | salary       |      3000000 | 월급                     | monthly           

$ python3 -m budget_app --data-dir ../lab/bonus-data backup --out-dir ../lab/backups
[백업 완료] ../lab/backups/budget-20261002-214237-060734-f8fcc2.zip

archive members: transactions.jsonl, categories.jsonl, budgets.jsonl, recurring.jsonl
```

규칙은 recurring.jsonl에 저장합니다. 날짜가 없는 달은 말일로 조정하며 규칙 id와 월로 만든 거래 id로 중복을 막습니다. 생성은 모든 규칙을 검증한 뒤 거래 파일을 한 번 교체합니다. backup은 잠금 안에서 네 파일을 ZIP으로 묶고 파일명에 실행 시각을 넣습니다.
