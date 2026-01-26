# Runner 사용법

이 문서는 canonical Dataset을 실제 챗봇/모델에 실행시켜 `RunResult`를 생성하는 **Runner** 모듈 사용 방법을 정리합니다.

## 1. 역할

Runner는 다음을 담당합니다.

1. Dataset(`test.jsonl` + `metadata.json`) 로드
2. Backend/모델/파라미터(RunConfig) 구성
3. 동시성/timeout/retry/rate-limit 전략 하에 각 `TestSample` 에 대해 요청 전송
4. 응답과 메타데이터를 `RunResult` 레코드로 모아서 JSONL 파일로 저장

## 2. Multi-turn 대화 지원

Runner는 단순 1-turn(User Question -> Answer) 뿐만 아니라, **Multi-turn 대화** 문맥을 유지하며 테스트할 수 있습니다.

- `TestSample`의 `messages` 필드에 여러 턴의 대화(`user`, `assistant`, `user`, ...)가 포함되어 있으면,
- Runner는 이를 순서대로 백엔드에 전달하여 전체 문맥을 반영한 응답을 요청합니다.

예를 들어 데이터셋이 다음과 같이 구성된 경우:

```json
[
  {"role": "user", "content": "Hello"},
  {"role": "assistant", "content": "Hi there!"},
  {"role": "user", "content": "What's the weather?"}
]
```

Runner는 이 전체 리스트를 백엔드의 `messages` 인자로 전달합니다. 이를 통해 이전 대화 내용("Hello" -> "Hi there!")을 기억하는지 테스트할 수 있습니다.

## 3. CLI 개요

Runner는 `python -m lm_eval_so.runner.cli` 형태의 CLI 엔트리포인트를 제공합니다.

```bash
python -m lm_eval_so.runner.cli --help
```

주요 인자:

- Dataset
  - `--dataset`: Dataset JSONL 경로 또는 Dataset 디렉터리
  - `--metadata`: `metadata.json` 경로 (디렉터리로 지정 시 생략 가능)
- Backend 선택
  - `--backend`: backend 이름 (예: `openai`)
  - `--model`: backend에서 사용할 모델 ID (예: `gpt-4o-mini`)
- RunConfig 파라미터
  - `--param key=value`: RunConfig.parameters 에 들어갈 값 (반복 사용 가능)
  - `--backend-opt key=value`: backend 옵션(예: api_base, request_defaults 등)
- Runner 옵션
  - `--engine`: 실행 엔진 (현재 sync 노출)
  - `--max-concurrency`: 동시 실행 개수
  - `--timeout`: 샘플당 timeout (초)
  - `--max-retries`: 재시도 횟수
  - `--rate-limit`: 초당 요청 수 제한
  - `--trace-prefix`: trace_id prefix
- 출력
  - `--output-dir`: run 결과 파일을 저장할 디렉터리 (필수)

## 3. OpenAI Backend 예제 (Quick Start)

Quick Start 예제에서는 OpenAI backend를 사용합니다.

전제:

- 환경 변수 `OPENAI_API_KEY` (필수)
- 선택: `OPENAI_BASE_URL` (커스텀 엔드포인트 사용 시)

실행 예시:

```bash
python -m lm_eval_so.runner.cli \
  --dataset example/quickstart/dataset/toy_support_qa_v1 \
  --backend openai \
  --model gpt-4o-mini \
  --param temperature=0 \
  --output-dir example/quickstart/runs/openai_gpt-4o-mini
```

위 명령은 다음을 수행합니다.

- Dataset 디렉터리(`toy_support_qa_v1`)에서 `test.jsonl`/`metadata.json` 로드
- `backend=openai`, `model=gpt-4o-mini` 설정
- 각 샘플에 대해 OpenAI Chat Completions API 호출
- 응답/latency/status/에러 정보를 포함한 `RunResult` 레코드를 생성
- 결과 파일:
  - `example/quickstart/runs/openai_gpt-4o-mini/run_results.jsonl`
  - `example/quickstart/runs/openai_gpt-4o-mini/run_metadata.json`

## 4. RunResult에 포함되는 정보

세부 필드는 코드(`lm_eval_so.runner.models.RunResult`)를 참고하면 되지만, 개념적으로는 다음과 같습니다.

- 어떤 샘플/데이터셋에 대한 실행인지 (`sample_id`, `dataset_id`)
- 어떤 backend/RunConfig로 실행했는지 (`backend`, `run_config`)
- 어떤 요청을 보냈는지 (`request_messages`, `request_context`)
- 어떤 응답을 받았는지 (`response.text`, 토큰 사용량 등)
- 실행 상태/시간/시도 횟수 (`status`, `latency_ms`, `attempts`)
- 에러가 있었다면 어떤 종류인지 (`error` 타입/메시지/재시도 가능 여부)

이 RunResult를 Evaluator가 소비하여 메트릭을 계산하게 됩니다.

## 5. Runner 옵션 설계시 고려사항

실제 서비스에 붙이는 경우, 다음과 같은 옵션 조합을 상황에 맞게 조절해야 합니다.

- `max_concurrency`: 백엔드가 감당 가능한 동시 요청 수
- `timeout`: API/네트워크 상황에 맞는 적절한 타임아웃
- `max_retries`: 재시도 정책 (429/5xx 등에 대한 backoff 전략과 함께 고려)
- `rate_limit`: 초당 요청/토큰 제한이 있는 API(OpenAI 등)에 필수
- `trace_prefix`: 로그/모니터링 시스템과 연계할 때 유용

Quick Start에서는 단순성을 위해 작은 동시성 + 짧은 run만 수행하지만, 실제 대규모 테스트에서는 위 옵션들이 매우 중요해집니다.

## 6. 파이프라인 유틸리티 (PipelineContext)

Runner CLI 외에 파이썬 스크립트로 직접 복잡한 파이프라인(Generation -> Finetuning -> Eval)을 구성할 때, MLflow 관리를 돕는 `PipelineContext`를 사용할 수 있습니다.

```python
from lm_eval_so.utils import PipelineContext

# 실험 이름과 아티팩트 저장소를 지정하여 컨텍스트 실행
with PipelineContext("my_experiment", "output_dir") as ctx:
    # 전역 파라미터 로깅
    ctx.log_params({"model": "v1.0"})

    # 각 단계를 중첩된 Run(Nested Run)으로 관리
    with ctx.step("step1_generation") as step_dir:
        # step_dir 경로에 데이터 생성
        ...
        # 아티팩트 및 메트릭 로깅
        ctx.log_artifact("dataset.jsonl")
        ctx.log_metrics({"count": 100})
```

이를 통해 구조화된 MLflow Run 트리를 손쉽게 생성할 수 있습니다.

