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
