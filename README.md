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
