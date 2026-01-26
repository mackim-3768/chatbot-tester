# 추가 예제 (Examples)

`lm-eval-so` 리포지토리의 `example/` 디렉터리에는 Quick Start 외에도 다양한 사용 사례를 보여주는 예제들이 포함되어 있습니다.

이 문서는 각 예제의 목적과 실행 방법을 설명합니다.

## 1. Multi-turn Chat (`multiturn_chat/`)

단발성 질의응답이 아닌, **대화의 문맥(Context)** 을 유지하며 테스트하는 방법을 보여줍니다.

- **위치**: `example/multiturn_chat/`
- **주요 특징**:
    - JSON 기반 데이터셋 입력 (`messages` 리스트 구조)
    - Runner의 멀티턴 컨텍스트 처리 확인
    - `run_multiturn.sh` 스크립트로 데이터셋 생성부터 평가까지 수행

### 실행 방법

```bash
# OPENAI_API_KEY 설정 필요
export OPENAI_API_KEY="sk-..."

bash example/multiturn_chat/run_multiturn.sh
```

### 데이터셋 구조 예시

`example/multiturn_chat/data/conversations.json`:

```json
[
  {
    "id": "mt_001",
    "messages": [
      {"role": "user", "content": "Hi, I need help with my order."},
      {"role": "assistant", "content": "Sure, what is your order ID?"},
      {"role": "user", "content": "It's ORDER-123."}
    ],
    "expected": "I see your order ORDER-123 is currently in transit.",
    "tags": ["support", "tracking"],
    "lang": "en"
  }
]
```

Runner는 이 `messages`를 순서대로 백엔드에 전달하여 대화 흐름을 재현합니다.

---

## 2. Custom Metrics (`custom_metric/`)

기본 제공 Metric(Exact Match, LLM Judge 등) 외에, **사용자가 직접 파이썬 코드로 작성한 Metric**을 플러그인 형태로 로드하여 사용하는 방법을 보여줍니다.

- **위치**: `example/custom_metric/`
- **주요 특징**:
    - 사용자 정의 Metric 구현 (`plugins/keyword_metric.py`)
    - `KeywordPresenceMetric` 클래스와 `register_metrics` 함수
    - Evaluator CLI의 `--plugin` 옵션을 통한 동적 로딩
    - `run_custom_metric.sh` 스크립트로 실행

### 실행 방법

```bash
# OPENAI_API_KEY 설정 필요
bash example/custom_metric/run_custom_metric.sh
```

### 플러그인 코드 예시

`example/custom_metric/plugins/keyword_metric.py`:

```python
from lm_eval_so.evaluator.metrics import Metric, MetricResult

class KeywordPresenceMetric(Metric):
    def __init__(self, keywords: list[str]):
        self.keywords = keywords

    def evaluate(self, response: str, reference: str | None = None, **kwargs) -> MetricResult:
        # ... 구현 로직 ...
        return MetricResult(score=score, details=...)

def make_keyword_metric(config):
    return KeywordPresenceMetric(keywords=config.get("keywords", []))

def register_metrics(registry):
    # Evaluator가 플러그인을 로드할 때 호출
    registry.register("keyword_presence", make_keyword_metric)
```

### Evaluator 설정 예시

`example/custom_metric/config/eval_config.yaml`:

```yaml
metrics:
  - type: keyword_presence  # 플러그인에서 등록한 이름
    keywords: ["hello", "world"]
```

이 예제를 통해 프로젝트 고유의 평가 로직을 손쉽게 추가할 수 있습니다.
