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
