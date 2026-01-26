# CLI 레퍼런스

이 문서는 `lm-eval-so`에서 제공하는 주요 CLI 엔트리포인트를 정리합니다.

각 CLI는 `python -m 모듈명` 형태로 호출하는 것을 기준으로 합니다.

## 1. Generator CLI

엔트리포인트:

```bash
python -m lm_eval_so.generator.cli --help
```

주요 옵션 요약:

- `--input`: 입력 파일 경로 (CSV/JSONL)
- `--input-format`: `csv` 또는 `jsonl` (생략 시 확장자 기반 자동 추론)
- `--output-dir`: 출력 디렉터리 (필수)
- `--dataset-id`, `--name`, `--version`: Dataset 메타데이터
- CSV 컬럼 매핑
  - `--csv-user-col`, `--csv-expected-col`, `--csv-system-col`
  - `--csv-tags-col`, `--csv-tags-sep`, `--csv-language-col`
- 필터/샘플링
  - `--min-len`, `--max-len`
  - `--sample-size`, `--sample-random`

보다 자세한 예시는 [Generator 사용법](../usage/generator.md) 문서를 참고하세요.

## 2. Runner CLI

엔트리포인트:

```bash
python -m lm_eval_so.runner.cli --help
```

주요 옵션 요약:

- Dataset
  - `--dataset`: Dataset JSONL 또는 Dataset 디렉터리 경로
  - `--metadata`: `metadata.json` 경로 (필요 시)
- Backend/RunConfig
  - `--backend`: backend 이름 (예: `openai`)
  - `--model`: 모델 이름/ID (예: `gpt-4o-mini`)
  - `--param key=value`: RunConfig.parameters 에 전달 (반복 사용 가능)
  - `--backend-opt key=value`: backend-specific 옵션
- Runner 옵션
  - `--max-concurrency`, `--timeout`, `--max-retries`, `--rate-limit`, `--trace-prefix`
- 출력
  - `--output-dir`: 결과 파일(JSONL 및 메타데이터)을 저장할 디렉터리

보다 자세한 예시는 [Runner 사용법](../usage/runner.md) 문서를 참고하세요.

## 3. Evaluator CLI

엔트리포인트:

```bash
python -m lm_eval_so.evaluator.cli --help
```

주요 옵션 요약:

- 입력
  - `--dataset`: canonical `TestSample` JSONL 경로
  - `--metadata`: Dataset 메타데이터 JSON 경로
  - `--runs`: `RunResult` JSONL 경로
- 설정
  - `--config`: Evaluator 설정 파일(YAML/JSON)
  - `--plugin`: 사용자 정의 Metric 플러그인 경로 (Python 파일 또는 모듈명, 반복 사용 가능)
- 출력
  - `--output`: 리포트 출력 디렉터리
- 포맷 제어
  - `--no-json`: JSON summary/scores 생략
  - `--no-markdown`: Markdown 리포트 생략

보다 자세한 예시는 [Evaluator 사용법](../usage/evaluator.md) 문서를 참고하세요.

## 4. 기타

향후 `lm_eval_so.*` 패키지에 추가 CLI가 들어가면, 이 문서에 함께 정리해 둘 수 있습니다.
