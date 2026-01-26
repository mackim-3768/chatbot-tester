# Evaluator 사용법

이 문서는 Dataset + RunResult를 기반으로 메트릭을 계산하고 리포트를 생성하는 **Evaluator** 모듈 사용 방법을 정리합니다.

## 1. 역할

Evaluator는 다음을 담당합니다.

1. Dataset(`TestSample`), RunResult를 sample_id 기준으로 조인
2. 설정된 metrics를 실행하여 각 샘플에 대한 `EvalScore` 계산
3. metric별 통계(평균, 표준편차, sample_count) 및 breakdown(tag/language/length 등) 생성
4. LLM Judge 기반 평가 결과 요약(optional)
5. JSON/Markdown 등 사람/머신 친화적인 리포트 파일 생성

## 2. CLI 개요

Evaluator는 `python -m lm_eval_so.evaluator.cli` 형태의 CLI 엔트리포인트를 제공합니다.

```bash
python -m lm_eval_so.evaluator.cli --help
```

주요 인자:

- 입력 데이터
  - `--dataset`: canonical `TestSample` JSONL 경로 (예: `test.jsonl`)
  - `--metadata`: Dataset 메타데이터 JSON 경로 (예: `metadata.json`)
  - `--runs`: `RunResult` JSONL 경로 (예: `run_results.jsonl`)
- 설정
  - `--config`: Evaluator 설정 파일(YAML/JSON)
- 출력
  - `--output`: 리포트 출력 디렉터리
- 포맷 제어
  - `--no-markdown`: Markdown 리포트 생략
  - `--no-json`: JSON summary/scores 생략

## 3. Evaluator 설정 파일 구조 (예: eval_toy.yaml)

기본 구조는 다음과 같습니다.

```yaml
run_config:
  backend: openai
  model: gpt-4o-mini

metrics:
  - type: exact_match
    name: exact_match
    parameters:
      normalize_whitespace: true
      case_sensitive: false

  - type: keyword_coverage
    name: keyword_coverage
    parameters:
      keywords:
        - "비밀번호"
        - "요금제"
        - "export"
      case_sensitive: false

breakdown:
  dimensions:
    - tag
    - language
    - length

report:
  formats:
    - json
    - markdown

min_samples: 1
```

- `run_config`
  - 이 평가가 어떤 RunConfig 환경을 대상으로 하는지 메타 정보를 기록 (실제 실행과 직접 연동되진 않지만, 리포트에 포함됨)
- `metrics`
  - 사용할 metric들의 타입/이름/파라미터
  - type은 registry에 등록된 metric 이름 (`exact_match`, `keyword_coverage`, `llm_judge` 등)
- `breakdown`
  - tag/language/length 등 특정 dimension별로 점수를 나눠 보고 싶을 때 사용
- `report`
  - 어떤 포맷(JSON/Markdown 등)으로 리포트를 생성할지
- `min_samples`
  - 평가를 진행하기 위한 최소 샘플 수 (너무 적으면 스킵하도록 방어)

## 4. Quick Start 예제 실행

Quick Start에서 Evaluator는 다음과 같이 실행됩니다.

```bash
python -m lm_eval_so.evaluator.cli \
  --dataset example/quickstart/dataset/toy_support_qa_v1/test.jsonl \
  --metadata example/quickstart/dataset/toy_support_qa_v1/metadata.json \
  --runs example/quickstart/runs/openai_gpt-4o-mini/run_results.jsonl \
  --config example/quickstart/config/eval_toy.yaml \
  --output example/quickstart/reports
```

실행 결과 예:

- `example/quickstart/reports/summary.json`
- `example/quickstart/reports/scores.jsonl`
- `example/quickstart/reports/report.md`

## 5. Metric 종류 예시

기본 제공 metric들은 대략 다음과 같습니다.

- **exact_match**
  - expected 텍스트와 모델 응답이 (공백 정규화/대소문자 옵션에 따라) 정확히 일치하는지 평가
  - 결과: 0.0 또는 1.0
- **keyword_coverage**
  - 설정된 keywords 리스트 중 응답에 포함된 비율을 평가 (0.0 ~ 1.0)
- **llm_judge**
  - 외부 LLM이 미리 평가해 둔 점수(예: `run.raw["llm_judge"]["score"]`)를 읽어와 0~1로 정규화
  - 외부 LLM이 미리 평가해 둔 점수(예: `run.raw["llm_judge"]["score"]`)를 읽어와 0~1로 정규화
  - 실제 LLM 호출은 하지 않고, Runner/외부 파이프라인이 생성한 결과를 소비하는 형태
- **tool_call_match**
  - 모델의 함수 호출(JSON)이 예상된 호출(JSON)과 일치하는지 평가
  - `allow_order_mismatch`: 순서 무시 여부 (기본값: False)
  - `exclude_args`: 비교에서 제외할 인자 목록 (예: timestamp 등)

## 6. Custom Metric (플러그인) 사용

기본 제공 Metric 외에, 사용자가 직접 파이썬 코드로 작성한 Metric을 사용할 수 있습니다.

### 6.1 플러그인 작성

`lm_eval_so.evaluator.metrics.Metric`을 상속받아 구현하고, `register_metrics` 함수를 통해 등록합니다.

```python
# my_plugin.py
from lm_eval_so.evaluator.metrics import Metric, MetricResult

class MyMetric(Metric):
    def score(self, sample, run):
        # ... 평가 로직 ...
        return self.make_score(sample, value=1.0, detail={})

def register_metrics(registry):
    registry.register("my_metric", lambda cfg: MyMetric(**cfg))
```

### 6.2 플러그인 로드 및 실행

Evaluator CLI 실행 시 `--plugin` 옵션으로 경로를 지정합니다.

```bash
python -m lm_eval_so.evaluator.cli \
  ... \
  --plugin path/to/my_plugin.py
```

### 6.3 설정 파일 반영

설정 파일(`config.yaml`)에서 등록한 `type` 이름을 사용합니다.

```yaml
metrics:
  - type: my_metric
    name: custom_check
    parameters:
      threshold: 0.5
```

자세한 예제는 [More Examples (Custom Metrics)](examples.md#2-custom-metrics-custom_metric) 문서를 참고하세요.

## 7. Report 읽는 법

Evaluator가 생성하는 리포트에는 보통 다음 정보가 포함됩니다.

- Experiment metadata
  - dataset 정보 (id/name/version, sample_count 등)
  - run_config (backend, model, 파라미터)
  - evaluator_config (metrics/breakdown/report 설정)
- Metrics summary
  - metric별 `mean`, `std`, `sample_count` 테이블
- Breakdown
  - tag / language / length 별 metric 분포
- Error cases
  - RunResult.status가 ok가 아닌 샘플들의 요약
- LLM Judge detail (사용한 경우)
  - prompt_id, prompt_version, 평가 기준(criteria), 평가에 사용된 샘플 집합 등

이 구조를 기준으로 여러 실험/모델을 비교하는 고수준 리포트를 손쉽게 만들 수 있습니다.
