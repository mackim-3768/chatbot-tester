# Generator 사용법

이 문서는 CSV/JSONL 등 원천 데이터를 canonical `TestSample` 데이터셋으로 변환하는 **Generator** 모듈 사용 방법을 정리합니다.

## 1. 핵심 개념

- 입력: CSV/JSONL 등의 테이블/레코드 데이터
- 출력:
  - `test.jsonl`: canonical `TestSample` 레코드 리스트
  - `metadata.json`: dataset_id/name/version, 필터/샘플링 정보, 태그/언어 통계
  - `schema.json`: `TestSample` JSON Schema

Generator는 크게 다음 단계를 거칩니다.

1. **Loader**: 파일(CSV/JSONL)에서 row를 읽어옴
2. **Canonicalization**: row → `TestSample` 객체로 변환
3. **Filter/Sample**: 길이/언어/태그 기준 필터링 및 샘플링
4. **Writer**: JSONL, metadata, schema 파일로 출력

## 2. CLI 개요

Generator는 `python -m lm_eval_so.generator.cli` 형태의 CLI 엔트리포인트를 제공합니다.

```bash
python -m lm_eval_so.generator.cli --help
```

주요 인자:

- 입력 관련
  - `--input`: 입력 파일 경로 (필수, CSV/JSONL)
  - `--input-format`: `csv` 또는 `jsonl` (생략 시 확장자로부터 추론)
- Dataset 메타데이터
  - `--dataset-id`: dataset 고유 ID (예: `toy_support_qa`)
  - `--name`: dataset 이름 (예: `"Toy Support QA"`)
  - `--version`: dataset 버전 (예: `v1`)
  - `--source`: 원천 데이터 출처(문자열 또는 JSON)
- 컬럼 매핑 (CSV 전용 예시)
  - `--csv-user-col`: 유저 질문 컬럼명
  - `--csv-expected-col`: 기대 답변 컬럼명
  - `--csv-system-col`: 시스템 프롬프트 컬럼명
  - `--csv-tags-col`: 태그 문자열 컬럼명 (구분자 기본 `|`)
  - `--csv-language-col`: 언어 코드(`ko`, `en` 등) 컬럼명
- 필터/샘플링
  - `--min-len`, `--max-len`: 메시지 길이 기준 필터
  - `--sample-size`: 샘플 개수 (0이면 전체)
  - `--sample-random`: 샘플링 시 랜덤 여부

## 3. JSONL 입력 포맷 (Multi-turn 지원)

CSV 외에도 **JSONL(JSON Lines)** 포맷을 지원합니다. 특히 **Multi-turn 대화** 데이터셋을 생성할 때 유용합니다.

JSONL 파일의 각 라인은 다음 필드를 포함할 수 있습니다:

- `id`: 샘플 ID (생략 시 자동 생성)
- `messages`: 대화 메시지 리스트 (`[{"role": "...", "content": "..."}, ...]`)
- `expected`: 기대 답변
- `tags`: 태그 리스트
- `lang`: 언어 코드
- `metadata`: 기타 메타데이터

### Multi-turn 데이터 예시

```json
{"id": "mt_1", "messages": [{"role": "user", "content": "A"}, {"role": "assistant", "content": "B"}, {"role": "user", "content": "C"}], "expected": "D", "tags": ["chat"], "lang": "en"}
{"id": "mt_2", "messages": [{"role": "user", "content": "X"}], "expected": "Y", "tags": ["single"], "lang": "en"}
```

Generator 실행 시 `--input-format jsonl`을 지정하면 됩니다.

```bash
python -m lm_eval_so.generator.cli \
  --input my_conversations.jsonl \
  --input-format jsonl \
  ...
```

## 4. Quick Start 예제: toy_support_qa

Quick Start에서는 작은 고객지원 QA 예제를 사용합니다.

- 입력: `example/quickstart/data/toy_support_qa.csv`
  - 컬럼: `id, system, user, expected, tags, lang`
- 출력 루트: `example/quickstart/dataset/`

직접 실행 예시:

```bash
python -m lm_eval_so.generator.cli \
  --input example/quickstart/data/toy_support_qa.csv \
  --input-format csv \
  --output-dir example/quickstart/dataset \
  --dataset-id toy_support_qa \
  --name "Toy Support QA" \
  --version v1 \
  --csv-user-col user \
  --csv-expected-col expected \
  --csv-system-col system \
  --csv-tags-col tags \
  --csv-language-col lang \
  --sample-size 3 \
  --sample-random
```

실행 후 생성되는 파일:

- `example/quickstart/dataset/toy_support_qa_v1/test.jsonl`
- `example/quickstart/dataset/toy_support_qa_v1/metadata.json`
- `example/quickstart/dataset/toy_support_qa_v1/schema.json`

## 4. dataset_id / version / metadata 정책

일관된 재현성을 위해 다음 정책을 권장합니다.

- **dataset_id**: 논리적으로 동일한 데이터셋 계열의 ID
- **version**: 데이터 내용/샘플 구성이 바뀔 때마다 증가 (`v1`, `v2`, ...)
- **metadata.json** 필수 정보 예시:
  - `dataset_id`, `name`, `version`, `created_at`
  - `generator_version`, `generator_code_commit`
  - `sample_count`
  - `filters` (min_len/max_len 등)
  - `sampling` (sample_size, sample_random)
  - `tag_stats`, `language_stats`

원천 데이터나 전처리/샘플링 로직이 바뀌어 **샘플 집합이 바뀌는 경우** 반드시 `version`을 올려 주는 것이 좋습니다.
