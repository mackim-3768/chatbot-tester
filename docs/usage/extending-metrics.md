# Metric 확장 가이드 (새 Metric 추가하기)

이 문서는 `lm-eval-so`의 **Evaluator Metric 플러그인**을 확장하는 방법을 정리합니다.

- Metric 인터페이스 개념
- 기본 Metric(`exact_match`, `keyword_coverage`, `llm_judge`) 구조
- 새 Metric 구현 + registry 등록 방법
- G-Eval / LLM-Judge 계열 Metric 설계 시 주의점

> 이 문서는 개념/패턴 위주 가이드이며, 실제 구현체 코드는 `src/lm_eval_so/evaluator/metrics/` 와 `src/lm_eval_so/evaluator/registry.py` 등을 참고하세요.

---

## 1. Metric 인터페이스 개념

Evaluator는 **Metric 플러그인**을 통해 점수를 계산합니다.

개념적으로 Metric은 다음 인터페이스를 가집니다.

- 입력:
  - `TestSampleRecord` (dataset에서 온 한 샘플)
  - `RunRecord` (Runner가 생성한 한 번의 실행 결과)
- 출력:
  - `EvalScore` (metric 이름, 값, 세부 정보가 들어 있는 레코드)

Pseudo-code로 보면:

```python
class Metric(Protocol):
    name: str
    parameters: dict
    requires_reference: bool

    def score(self, sample: TestSampleRecord, run: RunRecord) -> EvalScore:
        ...

    def build_llm_judge_details(self, scores: Iterable[EvalScore]) -> list[LLMJudgeDetail]:
        ...  # 대부분의 Metric에서는 빈 리스트를 반환
```

실제 구현에서는 공통 베이스 클래스(`Metric`)가 있어, 다음과 같은 도움 메서드를 제공합니다.

- `self.make_score(sample, value: float, detail: dict | None)`
  - metric 이름/값/세부정보를 포함하는 `EvalScore`를 생성

`requires_reference: bool`은 **참조 정답(expected)이 필요 여부**를 나타냅니다.

- 예: exact_match → `requires_reference = True`
- 예: keyword_coverage → `requires_reference = False`

---

## 2. 기본 Metric 예시 살펴보기

### 2.1 ExactMatchMetric (`exact_match`)

역할:

- `sample.expected`와 모델 응답(`run.response_text`)이
  - 공백 정규화, 대소문자 옵션에 따라 **완전히 동일한지** 평가

핵심 포인트:

- 파라미터
  - `normalize_whitespace: bool` (기본 True)
  - `case_sensitive: bool` (기본 False)
- 로직
  - expected 또는 answer가 없으면 `skipped` 플래그를 detail에 기록
  - 두 텍스트를 normalize 후 완전 일치하면 `value=1.0`, 아니면 `0.0`
- detail 예시
  - `{ "expected": "...", "answer": "...", "match": true/false }`

### 2.2 KeywordCoverageMetric (`keyword_coverage`)

역할:

- 미리 설정한 키워드 리스트가 응답 텍스트에 얼마나 포함됐는지 **coverage(포함 비율)** 평가

핵심 포인트:

- 파라미터
  - `keywords: list[str]` (필수)
  - `case_sensitive: bool` (기본 False)
- 로직
  - 응답 텍스트를 적절히 lower-case 처리
  - 각 키워드가 포함되면 `matched += 1`
  - `value = matched / total_keywords`
- detail 예시
  - `{ "matched": 2, "total_keywords": 3 }`

### 2.3 LLMJudgeMetric (`llm_judge`)

역할:

- **실제 LLM 호출은 하지 않고**, 이미 Runner/외부 파이프라인이 `RunRecord.raw` 안에 기록해 둔 LLM Judge 점수를 소비
- 예: `run.raw["llm_judge"]["score"]` 에 저장된 1~5점 점수를 읽어서 0~1 사이로 정규화

핵심 포인트:

- 파라미터
  - `prompt_id: str`
  - `prompt_version: str`
  - `criteria: list[str]` (예: ["correctness", "fluency"])
  - `max_score: float` (기본 5.0)
  - `score_key: str` (기본 `"llm_judge.score"`)
- 로직
  - `score_key` 경로를 따라 `run.raw`에서 값 조회
  - 없으면 `skipped` 처리
  - 숫자로 캐스팅 후 `value = numeric / max_score`
- `build_llm_judge_details(...)` 구현
  - 한 번의 metric 실행 전체에 대한 LLM-Judge 요약 레코드(`LLMJudgeDetail`) 생성
  - prompt_id/version, language, criteria, sample_count, sample_ids 등을 포함

---

## 3. 새 Metric 구현 절차

새 Metric을 추가하려면 **3단계**입니다.

1. Metric 클래스 구현 (`metrics/` 아래 새 파일 또는 기존 파일 내 클래스 추가)
2. Metric registry에 등록 (`register_default_metrics` 또는 별도 registry 호출)
3. Evaluator 설정 파일(config)에서 metric type/name/parameters 설정

### 3.1 Metric 클래스 구현

예를 들어, **응답 길이 기반 Metric**(너무 짧거나 긴 응답 penalize)을 만든다고 가정해 봅시다.

개념적 구조:

```python
from .base import Metric
from ..domain import EvalScore, RunRecord, TestSampleRecord


class LengthPenaltyMetric(Metric):
    """응답 길이가 너무 짧거나 길 경우 패널티를 주는 예제 metric."""

    requires_reference: bool = False

    def __init__(self, *, name: str, parameters: Mapping[str, Any] | None = None) -> None:
        super().__init__(name=name, parameters=parameters)
        p = self.parameters
        self._min_len = int(p.get("min_len", 1))
        self._max_len = int(p.get("max_len", 512))

    def score(self, sample: TestSampleRecord, run: RunRecord) -> EvalScore:
        text = run.response_text or ""
        length = len(text)

        if length == 0:
            value = 0.0
            detail = {"length": length, "reason": "empty_response"}
        elif length < self._min_len:
            value = 0.3  # 너무 짧으면 패널티
            detail = {"length": length, "reason": "too_short"}
        elif length > self._max_len:
            value = 0.5  # 너무 길어도 패널티
            detail = {"length": length, "reason": "too_long"}
        else:
            value = 1.0
            detail = {"length": length, "reason": "ok"}

        return self.make_score(sample, value=value, detail=detail)
```

위 예시는 **개념적인 패턴**만 보여주며, 실제 값(0.3/0.5 등)은 프로젝트 요구에 맞게 설계해야 합니다.

### 3.2 Metric Registry에 등록

Evaluator는 내부적으로 **MetricRegistry**를 사용해 `type` 이름으로 Metric을 생성합니다.

기본 등록 함수는 대략 다음과 같은 형태입니다.

```python
from .exact_match import ExactMatchMetric
from .keyword import KeywordCoverageMetric
from .llm_judge import LLMJudgeMetric


def register_default_metrics(registry: MetricRegistry) -> None:
    def _safe_register(name: str, factory):
        ...

    _safe_register("exact_match", lambda cfg: ExactMatchMetric(**cfg))
    _safe_register("keyword_coverage", lambda cfg: KeywordCoverageMetric(**cfg))
    _safe_register("llm_judge", lambda cfg: LLMJudgeMetric(**cfg))
```

새 Metric을 등록하려면, 여기에 한 줄을 추가하면 됩니다.

```python
from .length_penalty import LengthPenaltyMetric

    _safe_register("length_penalty", lambda cfg: LengthPenaltyMetric(**cfg))
```

- `"length_penalty"` 문자열이 **Evaluator 설정 파일의 `type` 필드**에서 사용되는 이름이 됩니다.

### 3.3 Evaluator 설정(config)에서 사용하기

등록을 마친 뒤에는 Evaluator 설정 파일(YAML/JSON)에서 새 Metric을 참조할 수 있습니다.

```yaml
metrics:
  - type: length_penalty
    name: length_penalty
    parameters:
      min_len: 10
      max_len: 256
```

- `type`: registry에 등록한 이름
- `name`: 리포트에 표시될 metric 이름 (생략하면 type으로 대체되는 형태를 사용하는 것이 일반적)
- `parameters`: Metric 생성자에 전달할 파라미터

이렇게 설정하면 Evaluator는 다른 metric들과 동일한 방식으로 `LengthPenaltyMetric`을 실행하게 됩니다.

---

## 4. G-Eval / LLM-Judge Metric 설계 시 주의점

LLM 기반 평가(G-Eval, LLM-as-a-Judge)는 **비용/일관성/버전 관리**가 중요합니다. 설계 시 다음을 권장합니다.

### 4.1 Runner vs Evaluator 역할 분리

현 설계에서는:

- Runner/외부 파이프라인
  - 실제 LLM Judge API를 호출하고, 원본 평가 결과를 `RunRecord.raw` 등에 저장
- Evaluator의 `llm_judge` Metric
  - 이미 계산된 점수를 읽어와 정규화/집계만 수행

이렇게 역할을 분리하면 다음 장점이 있습니다.

- Evaluator 실행 시 **추가 API 비용이 들지 않음**
- 같은 RunResult에 대해 여러 번 재평가/리포트를 만들 수 있음
- LLM Judge 프롬프트/모델이 바뀌더라도 Runner 파이프라인만 교체하면 됨

### 4.2 prompt_id / version / criteria 관리

LLM Judge Metric 파라미터에는 최소 다음 항목을 명시적으로 넣는 것을 권장합니다.

- `prompt_id`: 평가 프롬프트/템플릿을 식별하는 ID
- `prompt_version`: 프롬프트 버전 (예: `v1`, `2025-03-01`)
- `criteria`: LLM Judge가 평가할 기준 리스트 (예: `correctness`, `faithfulness`, `style_match` 등)

이를 `EvalScore.detail` 또는 `LLMJudgeDetail` 에 기록해 두면:

- 나중에 "어떤 기준/프롬프트로 점수를 냈는지"를 추적 가능
- 프롬프트가 개선/변경되었을 때 실험 버전을 명확히 구분 가능

### 4.3 score_key / max_score 설계

- `score_key`: Runner가 `run.raw`에 넣어주는 점수 위치를 문자열 경로로 정의
  - 예: `"llm_judge.score"`, `"judge.overall"`
- `max_score`: LLM이 주는 원점수의 최대값
  - 예: 1~5 점수라면 `max_score=5.0`

Metric 구현에서는:

- `raw_value = _get_nested(run.raw, score_key)` 로 값을 읽어오고
- `value = raw_value / max_score` 로 0~1 범위로 정규화

이렇게 하면 다른 metric들과 동일한 스케일에서 비교/집계하기 편리합니다.

### 4.4 비용/샘플링 전략 (sample_rate)

LLM Judge는 비용이 크기 때문에, Evaluator config에서 **샘플링 비율**을 두는 것도 좋습니다.

예를 들어 MetricConfig에 `sample_rate: 0.2` 라는 필드를 두고,
전체 샘플 중 20%만 LLM Judge를 적용하는 전략을 쓸 수 있습니다.

설계 팁:

- 대규모 테스트에서는 `sample_rate < 1.0` 을 기본값으로 두기
- 어떤 샘플 subset에 LLM Judge를 적용했는지(예: tag/length 기준 stratified sampling) 메타데이터에 기록

---

## 5. 요약

- Metric은 `sample + run → EvalScore`를 계산하는 플러그인 단위입니다.
- 새 Metric을 추가하려면:
  1. `Metric` 베이스 클래스를 상속해 `score()` 구현
  2. Metric registry에 type 이름으로 등록
  3. Evaluator 설정 파일의 `metrics` 리스트에 type/name/parameters 추가
- G-Eval / LLM-Judge 계열 Metric은 Runner와 Evaluator 역할을 분리하고,
  - `prompt_id` / `prompt_version` / `criteria` / `score_key` / `max_score` / `sample_rate`
  를 명시적으로 관리하는 것이 중요합니다.

이 패턴을 따르면, 새로운 task-specific metric(번역 품질/요약 정보보존/스타일 일치도 등)을
일관된 방식으로 추가하고, 보고서 구조도 유지할 수 있습니다.
