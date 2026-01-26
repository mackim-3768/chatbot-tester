# LM-Eval-SO

**LM Evaluation & Synthetic Data Orchestrator**

DeepWiki 문서 : [https://deepwiki.com/mackim-3768/lm-eval-so](https://deepwiki.com/mackim-3768/lm-eval-so)
공식 문서(Documentation): [https://mackim-3768.github.io/lm-eval-so/](https://mackim-3768.github.io/lm-eval-so/)

챗봇을 체계적으로 **테스트·평가**하기 위한 프레임워크입니다.

## 📦 설치 및 사용 (Install vs Import)

> [!IMPORTANT]
> **패키지 이름(Install)**과 **임포트 이름(Code)**이 다릅니다. 혼동하지 않도록 주의하세요.

- **설치 (Install)**: `LM-Eval-SO`
  ```bash
  pip install LM-Eval-SO
  ```

- **코드 사용 (Import)**: `lm_eval_so`
  ```python
  import lm_eval_so
  from lm_eval_so.runner import cli
  ```

## 전체 컨셉

프레임워크는 크게 다음 세 가지 기능 영역으로 나눈다.

1. **DataSet 생성 모듈 (Generator)**  
   - 챗봇 테스트에 사용할 입력/출력 샘플, 시나리오, 평가용 데이터셋을 정의·생성하는 모듈  
   - 다양한 포맷의 원천 데이터를 수집·정제해서, 공통 포맷의 테스트 DataSet 으로 변환하는 역할

2. **대화 컨트롤러 (Runner)**  
   - 테스트용 DataSet을 기반으로 실제 챗봇에 질의하고, 응답을 수집하는 실행 컨트롤러  
   - 서로 다른 챗봇(모델/API)에 대해 공통 인터페이스로 요청을 보내고, 결과를 일관된 포맷으로 저장  
   - 추후 다양한 챗봇/엔드포인트를 플러그인처럼 추가하기 쉬운 구조를 지향

3. **평가 모듈 (Evaluator)**  
   - 수집된 챗봇 응답을 기반으로 품질을 정량·정성적으로 평가하는 모듈  
   - 규칙 기반, 모델 기반, 휴리스틱 기반 등 다양한 평가 전략을 조합할 수 있도록 설계  
   - 테스트 결과를 리포트/메트릭 형태로 제공

## 🧩 확장 가이드 (For Developers & AI Agents)

이 라이브러리는 확장을 염두에 두고 설계되었습니다. 새로운 백엔드나 평가 지표를 추가하려면 아래 클래스를 상속받으세요.
더 자세한 내용은 `llms.txt`를 참고하세요.

### 1. Backend 확장
`lm_eval_so.core.backends.base.ChatBackend`를 상속받아 `send` 메서드를 구현하세요.

```python
from lm_eval_so.core.backends.base import ChatBackend, register_backend

@register_backend("my_custom_model")
class MyBackend(ChatBackend):
    async def send(self, request):
        # 구현 로직...
        pass
```

### 2. Metric 확장
`lm_eval_so.evaluator.metrics.base.Metric`을 상속받아 `score` 메서드를 구현하세요.

```python
from lm_eval_so.evaluator.metrics.base import Metric

class MyMetric(Metric):
    def score(self, sample, run):
        # 평가 로직...
        return self.make_score(sample, value=1.0)
```

## Quick Start: 5분 안에 첫 리포트 만들기

아래 순서를 따르면, 작은 toy 데이터셋을 가지고 **Generator → Runner → Evaluator** 전체 플로우를 한 번에 실행해 첫 Evaluation Report(JSON/Markdown)를 만들어볼 수 있다.

1. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```

2. OpenAI API 키 설정 (예시)
   ```bash
   export OPENAI_API_KEY="sk-..."  # GitHub Actions 에서는 repo secrets 사용
   ```

3. Quick Start 스크립트 실행
   ```bash
   bash example/quickstart/run_quickstart.sh
   ```

4. 생성된 산출물 확인
   - Dataset (canonical `TestSample` JSONL)
     - `example/quickstart/dataset/toy_support_qa_v1/test.jsonl`
     - `example/quickstart/dataset/toy_support_qa_v1/metadata.json`
   - Runner 결과(`RunResult` 레코드)
     - `example/quickstart/runs/openai_gpt4-mini/run_results.jsonl`
   - Evaluator 리포트(`EvaluationReport`)
     - `example/quickstart/reports/` 아래 JSON/Markdown 파일

리포트에는 다음 정보가 포함된다.
- Experiment metadata (dataset, backend/run_config, evaluator_config 요약)
- Overall metrics summary (예: `exact_match`, `keyword_coverage`의 mean/std/sample_count)
- Breakdown (tag / language / length 기준)
- Error cases / LLM Judge 세부 정보(구성된 경우)

이를 기반으로 보다 복잡한 데이터셋/백엔드/메트릭 구성을 확장해 나갈 수 있다.