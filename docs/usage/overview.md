# Framework Overview

이 문서는 `lm-eval-so` 프레임워크의 큰 그림을 설명합니다.

- Core 도메인 모델
- Generator → Runner → Evaluator 데이터 플로우
- Report 구조(Experiment/metrics/breakdown 등)의 개요

## 1. Core 도메인 모델

프레임워크 전역에서 공유하는 공통 모델은 대략 다음과 같습니다.

- **TestSample**
  - `id`: 샘플 ID
  - `messages`: 대화 맥락 (`role`, `content` 로 구성된 메시지 리스트)
  - `expected`: 기대 출력(있을 수도, 없을 수도 있음)
  - `tags`: 태그 리스트 (task, domain, language 등)
  - `metadata`: 길이, 토픽, 난이도 등의 부가 정보

- **TestCase** (선택적 개념)
  - 여러 `TestSample` 을 하나의 시나리오로 묶을 때 사용

- **RunConfig**
  - 어떤 백엔드/모델을 어떤 설정으로 돌릴지에 대한 구성
  - 예: `backend="openai"`, `model="gpt-4o-mini"`, `parameters={"temperature": 0.0}`

- **RunResult**
  - 단일 `TestSample` 에 대해 실제 챗봇/모델을 호출한 결과
  - 포함 정보 예시:
    - `sample_id`, `dataset_id`, `backend`, `run_config`
    - 요청 메시지(`request_messages`), 응답 텍스트/토큰 사용량
    - `status` (ok / timeout / error / retry 등)
    - `latency_ms`, `trace_id`, `error` 정보

- **EvalScore**
  - 한 metric에 대한 단일 샘플의 점수
  - `metric_name`, `value`, `detail`(예: expected/answer 페어, 키워드 매칭 수, LLM Judge 세부 정보 등)

이 공통 모델을 기준으로 Generator/Runner/Evaluator가 느슨하게 결합됩니다.

## 2. Generator → Runner → Evaluator 데이터 플로우

### 2.1 Generator (Dataset 생성)

목표: 다양한 포맷의 원천 데이터를 canonical `TestSample` 리스트로 정규화하고, 버전이 붙은 Dataset으로 관리합니다.

전형적인 플로우:

1. **원천 데이터 로딩**
   - CSV / JSONL / DB 등에서 row 단위로 불러오기
2. **정규화 (Canonicalization)**
   - 각 row를 `TestSample` 구조로 매핑
   - 예: `system`, `user`, `expected`, `tags`, `lang` 컬럼 → `messages`/`expected`/`tags`/`metadata`
3. **필터링 / 샘플링**
   - 길이, 언어, 태그 기준 필터
   - 랜덤 샘플링 또는 전략적 샘플링
4. **출력**
   - `test.jsonl`: `TestSample.to_dict()` 리스트
   - `metadata.json`: `dataset_id`, `name`, `version`, `created_at`, `sample_count`, tag/language 분포 등
   - `schema.json`: `TestSample` JSON Schema

Quick Start 예제에서는:

- `example/quickstart/data/toy_support_qa.csv` → `toy_support_qa_v1/test.jsonl` + `metadata.json`

### 2.2 Runner (테스트 실행)

목표: **(Dataset × Backend × RunConfig)** 조합에 대해 실제 챗봇/모델을 호출하고, `RunResult` 레코드 집합을 생성합니다.

전형적인 플로우:

1. Dataset 로드 (`test.jsonl` + `metadata.json`)
2. Backend 선택 (예: `openai`)
3. RunConfig 구성 (`model`, `temperature`, 기타 파라미터)
4. 동시성 / rate limit / retry 전략에 따라 각 `TestSample` 에 대해 요청 전송
5. 결과를 `run_results.jsonl` 및 `run_metadata.json` 형태로 저장

Quick Start 예제에서는:

- Backend: `openai`
- Model: `gpt-4o-mini` (기본값, `QUICKSTART_MODEL` env로 변경 가능)
- 출력: `example/quickstart/runs/openai_<model>/run_results.jsonl`

### 2.3 Evaluator (평가)

목표: Dataset + RunResult를 조합해 다양한 metric을 계산하고, **per-sample score + aggregate report** 를 생성합니다.

전형적인 플로우:

1. Evaluator 설정 로드 (`eval_toy.yaml` 등)
   - `run_config` (메타 정보용)
   - `metrics` (예: `exact_match`, `keyword_coverage`, `llm_judge`)
   - `breakdown` (tag / language / length 기준 집계 설정)
   - `report` 포맷 (JSON / Markdown 등)
2. Dataset(`TestSample`), RunResult를 sample_id 기준으로 조인
3. 각 metric에 대해 모든 (sample, run) 페어에 점수 계산 → `EvalScore` 리스트 생성
4. metric별 통계 계산 (mean, std, sample_count)
5. tag/length/language 별 breakdown 생성
6. LLM Judge 관련 세부 정보 수집 (prompt_id/version, criteria 등)
7. 최종 `EvaluationResult`/`EvaluationReport` 를 JSON/Markdown 파일로 저장

Quick Start 예제에서 생성되는 대표 출력:

- `summary.json` — metric별 요약 테이블 (mean/std/sample_count)
- `scores.jsonl` — per-sample `EvalScore` 레코드
- `report.md` — 사람이 읽기 좋은 Markdown 리포트

## 3. Report 구조 개요

리포트는 보통 다음과 같은 구조를 가집니다.

- **Experiment metadata**
  - 어떤 Dataset / Backend / RunConfig / EvaluatorConfig로 실험했는지 요약
- **Overall metrics summary**
  - metric별 `mean`, `std`, `sample_count` 테이블
- **Breakdown**
  - tag / language / length 기준으로 metric 분포를 나눈 테이블/그래프
- **Error cases / Low-score samples**
  - status가 ok가 아닌 RunResult, 또는 점수가 낮은 샘플 목록
- **LLM Judge 세부 정보 (선택)**
  - `prompt_id`, `prompt_version`, `criteria`, 평가에 사용된 sample 집합 ID 등

이 구조를 지키면, 여러 실험/모델을 비교하는 리포트를 작성할 때도 일관성을 유지할 수 있습니다.

---

다음으로는 각 모듈별 사용법 문서를 참고하세요.

- [Generator 사용법](generator.md)
- [Runner 사용법](runner.md)
- [Evaluator 사용법](evaluator.md)
