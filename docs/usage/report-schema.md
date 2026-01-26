# Report Schema (EvaluationResult / EvaluationReport)

이 문서는 Evaluator가 생성하는 **결과 파일 구조**를 정리합니다.

- per-sample 점수: `EvalScore` 리스트 (`scores.jsonl`)
- 집계 리포트: `EvaluationReport` (`summary.json`, `report.md` 등)

아래 설명은 `src/lm_eval_so/evaluator/domain.py` 의 도메인 모델을 기준으로 합니다.

---

## 1. Core 데이터 구조

### 1.1 DatasetMetadata

`metadata.json` 에서 읽어오는 Dataset 메타데이터입니다.

중요 필드:

- `dataset_id: str`
- `version: str`
- `name: str | null`
- `source: any | null` — 원천 데이터 출처
- `created_at: str | null`
- `generator_commit: str | null` — generator 코드 커밋 해시
- `filters: object | null` — 전처리/필터링 조건
- `sampling: object | null` — 샘플링 전략 정보
- `counts: object | null` — 샘플 개수 등 카운트 정보 (예: `{"sample_count": 3}`)
- `languages: object | null` — 언어 분포
- `tags: object | null` — 태그 분포
- `extra: object` — 위에 명시되지 않은 추가 필드

### 1.2 TestSampleRecord

per-sample Dataset 레코드입니다. Evaluator가 dataset JSONL을 읽을 때 사용합니다.

- `id: str`
- `messages: Message[]` — canonical 메시지 리스트 (`role`, `content`, `name`, `metadata` 등)
- `expected: any | null` — 참조 정답 (있을 수도, 없을 수도 있음)
- `tags: string[]` — 태그 리스트
- `metadata: object` — 임의 메타데이터 (예: `{"language": "ko"}`)
- 파생 속성
  - `language: str | null` — `metadata["language"]`
  - `length_bucket: "short" | "medium" | "long"` — messages content 길이로부터 추론

### 1.3 RunRecord

Runner가 생성한 per-sample 실행 결과를 Evaluator용으로 정규화한 구조입니다.

- `sample_id: str`
- `dataset_id: str | null`
- `backend: str` — 예: `"openai"`
- `run_config: object` — Runner에 사용된 설정 전체
- `response_text: str | null` — 응답 텍스트 (없으면 null)
- `status: str` — `ok`, `timeout`, `error`, `retry` 등
- `latency_ms: float | null`
- `trace_id: str`
- `attempts: int`
- `error: object | null` — 오류 정보 (message, error_type, status_code 등)
- `raw: object` — 원본 RunResult 레코드 전체 (LLM Judge 점수 등도 포함)

### 1.4 EvalScore (per-sample metric 결과)

하나의 metric에 대해 하나의 샘플에서 나온 점수입니다.

- `sample_id: str`
- `metric: str` — metric 이름 (`exact_match`, `keyword_coverage`, `llm_judge` 등)
- `value: float` — 0.0~1.0 범위를 권장
- `tags: string[]` — 샘플 태그
- `language: str | null` — 샘플 언어
- `length_bucket: str | null` — `short` / `medium` / `long`
- `detail: object` — metric 세부 정보 (expected/answer, matched keywords, LLM Judge raw score 등)

### 1.5 MetricSummary / MetricBreakdown

집계 레벨 통계를 표현합니다.

**MetricSummary** (전체 요약):

- `metric: str`
- `mean: float`
- `std: float`
- `sample_count: int`

**MetricBreakdown** (dimension별 분해):

- `metric: str`
- `dimension: str` — 예: `"tag"`, `"language"`, `"length"`
- `bucket: str` — 예: 태그 이름, 언어 코드, length_bucket
- `mean: float`
- `std: float`
- `sample_count: int`

### 1.6 ErrorCase

실행 단계에서 status가 ok가 아니었던 샘플에 대한 정보입니다.

- `sample_id: str`
- `status: str` — `timeout`, `error`, `retry` 등
- `trace_id: str`
- `message: str | null` — 에러 메시지
- `latency_ms: float | null`
- `backend: str | null`

### 1.7 LLMJudgeDetail

LLM Judge 기반 metric들의 메타 정보를 모은 요약입니다.

- `metric: str` — 예: `"llm_judge"`
- `prompt_id: str`
- `prompt_version: str`
- `language: str | null` — 단일 언어만 있으면 해당 언어, 혼합이면 null
- `criteria: string[]` — 평가 기준 리스트
- `sample_count: int`
- `sample_ids: string[]` — Judge 평가에 사용된 샘플 ID 리스트

### 1.8 ExperimentMetadata / EvaluationReport / EvaluationResult

**ExperimentMetadata**

- `dataset: DatasetMetadata`
- `run_config: object` — 이 평가가 어떤 RunConfig 환경에 대한 것인지 (backend/model/parameters)
- `evaluator_config: object` — Evaluator 설정 전체 (`metrics`, `breakdown`, `report` 등)

**EvaluationReport**

- `experiment: ExperimentMetadata`
- `summaries: MetricSummary[]`
- `breakdowns: MetricBreakdown[]`
- `error_cases: ErrorCase[]`
- `llm_judge_details: LLMJudgeDetail[]`

**EvaluationResult**

- `scores: EvalScore[]` — per-sample 점수 전체
- `report: EvaluationReport` — 집계 리포트

---

## 2. JSON 예시

아래는 매우 단순화한 `EvaluationResult` JSON 예시입니다.

```json
{
  "scores": [
    {
      "sample_id": "toy-001",
      "metric": "exact_match",
      "value": 1.0,
      "tags": ["toy", "support", "ko"],
      "language": "ko",
      "length_bucket": "short",
      "detail": {
        "expected": "비밀번호 재설정을 위해 등록된 이메일을 확인하세요.",
        "answer": "비밀번호 재설정을 위해 등록된 이메일을 확인하세요.",
        "match": true
      }
    },
    {
      "sample_id": "toy-001",
      "metric": "keyword_coverage",
      "value": 1.0,
      "tags": ["toy", "support", "ko"],
      "language": "ko",
      "length_bucket": "short",
      "detail": {
        "matched": 1,
        "total_keywords": 1
      }
    }
  ],
  "report": {
    "experiment": {
      "dataset": {
        "dataset_id": "toy_support_qa",
        "version": "v1",
        "name": "Toy Support QA",
        "created_at": "2025-11-23T07:52:40Z",
        "counts": {"sample_count": 3},
        "languages": {"ko": 2, "en": 1},
        "tags": {"toy": 3, "support": 3}
      },
      "run_config": {
        "backend": "openai",
        "model": "gpt-4o-mini",
        "parameters": {"temperature": 0}
      },
      "evaluator_config": {
        "metrics": [
          {"type": "exact_match", "name": "exact_match"},
          {"type": "keyword_coverage", "name": "keyword_coverage"}
        ],
        "breakdown": {"dimensions": ["tag", "language", "length"]},
        "report": {"formats": ["json", "markdown"]}
      }
    },
    "summaries": [
      {
        "metric": "exact_match",
        "mean": 0.66,
        "std": 0.47,
        "sample_count": 3
      },
      {
        "metric": "keyword_coverage",
        "mean": 0.8,
        "std": 0.2,
        "sample_count": 3
      }
    ],
    "breakdowns": [
      {
        "metric": "exact_match",
        "dimension": "language",
        "bucket": "ko",
        "mean": 1.0,
        "std": 0.0,
        "sample_count": 2
      },
      {
        "metric": "exact_match",
        "dimension": "language",
        "bucket": "en",
        "mean": 0.0,
        "std": 0.0,
        "sample_count": 1
      }
    ],
    "error_cases": [],
    "llm_judge_details": []
  }
}
```

실제 Quick Start 예제의 `summary.json` / `scores.jsonl`는 위 구조를 더 많은 metric과 breakdown으로 확장한 형태입니다.

---

## 3. Markdown 리포트 예시 구조

`report.md` 는 사람이 읽기 좋은 Markdown 리포트로, 보통 다음 섹션을 포함합니다.

```markdown
# Experiment

- Dataset: toy_support_qa v1 (3 samples)
- Backend: openai (model=gpt-4o-mini)
- Evaluator config: metrics=[exact_match, keyword_coverage]

## Overall Metrics

| metric            | mean | std  | sample_count |
|-------------------|------|------|--------------|
| exact_match       | 0.66 | 0.47 | 3            |
| keyword_coverage  | 0.80 | 0.20 | 3            |

## Breakdown by language

| metric      | language | mean | std  | sample_count |
|-------------|----------|------|------|--------------|
| exact_match | ko       | 1.0  | 0.0  | 2            |
| exact_match | en       | 0.0  | 0.0  | 1            |

## Error Cases

No error cases. (all runs status=ok)

## Notes

- All Korean samples were answered correctly.
- English sample shows a mismatch with the reference answer.
```

실제 구현된 Markdown 리포트 구조는 코드(`json_reporter.py` / `markdown_reporter.py`)에 따라 조금씩 다를 수 있지만,
위와 같이 다음 4가지를 항상 포함하도록 설계하는 것을 권장합니다.

1. **Experiment metadata** (dataset / backend / run_config / evaluator_config 요약)
2. **Overall metrics summary** (metric별 mean/std/sample_count)
3. **Breakdown** (tag / language / length 기준 테이블)
4. **Error cases / LLM Judge 세부 정보** (비정상 응답/낮은 점수 샘플)

---

## 4. Report 설계 시 체크리스트

리포트 구조를 확장/변경할 때는 다음을 점검하는 것이 좋습니다.

- Experiment 단위가 명확한가?
  - (Dataset × Backend × RunConfig × EvaluatorConfig) 조합이 하나의 Experiment
- 모든 metric에 대해:
  - per-sample `EvalScore` 가 존재하는가?
  - summary(`MetricSummary`)와 breakdown(`MetricBreakdown`)가 일관된 스키마를 따르는가?
- ErrorCase/LLMJudgeDetail이 별도 섹션으로 정리되어 있는가?
- JSON/Markdown 리포트 모두에서 동일한 정보가 재현 가능한가?

이 기준을 지키면, 여러 모델/버전/설정을 비교하는 상위 실험 리포트를 만들 때도
스키마가 흔들리지 않고 일관성을 유지할 수 있습니다.

