# lm-eval-runner

`lm-eval-runner`는 **(Dataset × Backend × RunConfig) → RunResult 집합**을 생산하는 러너(Runner) 모듈입니다.

- **Dataset**: 테스트 샘플 집합 (JSONL 또는 디렉터리)
- **Backend**: 실제 LLM 또는 외부 시스템을 호출하는 어댑터 (`openai`, `adb-cli` 등)
- **RunConfig**: 모델/파라미터/백엔드 옵션 등 실행 설정
- **RunResult**: 각 샘플별 요청/응답/오류/latency/토큰 사용량 등 실행 로그 1행

이 모듈은 라이브러리로도 사용할 수 있지만, 주 사용 방식은 CLI 엔트리포인트인 `lm-eval-runner`입니다.

---

## 1. 핵심 개념: Dataset × Backend × RunConfig → RunResult 집합

Runner는 다음과 같은 도메인 모델을 기준으로 동작합니다.

- **Dataset (`DatasetInfo`, `TestSample`)**
  - 구현: `dataset.py`, `models.TestSample`, `models.DatasetInfo`
  - 입력 형식:
    - JSONL 파일 경로 (`--dataset path/to/test.jsonl`)
    - 또는 디렉터리 경로 (`--dataset path/to/dataset_dir`)
      - 디렉터리 모드에서는 `test.jsonl`을 자동으로 사용
      - `metadata.json`이 있으면 데이터셋 메타데이터로 사용
  - 각 라인(샘플)의 스키마(`TestSample`):
    - `id: str` — 샘플 ID
    - `messages: List[Message]` — 대화 히스토리
      - `role: str` (`user`, `assistant`, `system` 등)
      - `content: str`
      - `name: Optional[str]`
      - `metadata: Optional[dict]`
    - `expected: Any | None` — 평가 시 사용할 정답/레퍼런스(옵션)
    - `tags: List[str] | None` — 태깅 정보(옵션)
    - `metadata: dict | None` — 샘플 단위 메타데이터(옵션)

- **Backend (`ChatBackend`)**
  - 구현: `backends/` (예: `openai_backend.py`, `adb_cli_backend.py`)
  - 인터페이스: `ChatBackend.send(RunRequest) -> ChatResponse`
  - 역할: Runner가 만든 `RunRequest`를 받아 실제 엔드포인트 호출 후 `ChatResponse`로 변환

- **RunConfig (`models.RunConfig`)**
  - 필드:
    - `backend: str`
    - `model: Optional[str]`
    - `parameters: Dict[str, Any]`
    - `backend_options: Dict[str, Any]`
    - `metadata: Optional[Dict[str, Any]]`
  - CLI에서:
    - `--backend` → `RunConfig.backend`
    - `--model` → `RunConfig.model`
    - `--param key=value` → `RunConfig.parameters[key]`
    - `--backend-opt key=value` → `RunConfig.backend_options[key]`

- **RunResult (`models.RunResult`)**
  - 각 샘플 실행에 대한 전체 로그 1행
  - 주요 필드:
    - `sample_id`, `dataset_id`, `backend`, `run_config`
    - `request_messages`, `request_context`
    - `response: ChatResponse | None`
    - `status: RunResultStatus` (`"ok" | "retry" | "timeout" | "error"`)
    - `latency_ms`, `started_at`, `completed_at`, `attempts`, `trace_id`
    - `error: RunError | None`
  - JSONL로 직렬화 시 `RunResult.to_record()`를 사용하며, 이는 Evaluator가 소비하는 표준 포맷입니다.

---

## 2. Dataset & metadata 입력 형식

Runner는 `dataset.py`의 `load_dataset()`을 통해 입력을 읽습니다.

### 2.1. Dataset 경로 규칙

- `--dataset path/to/file.jsonl` (파일)
  - 그대로 JSONL 파일로 취급합니다.
- `--dataset path/to/dataset_dir` (디렉터리)
  - `path/to/dataset_dir/test.jsonl`을 샘플 파일로 사용
  - `metadata.json` 경로는 아래 규칙을 따릅니다.

### 2.2. metadata 경로 규칙

- `--metadata`를 지정한 경우: 해당 경로를 `metadata.json`으로 사용
- 지정하지 않은 경우, 디렉터리 모드에서 `dataset_dir/metadata.json`을 자동 탐색
- 메타데이터 JSON 스키마는 유연하며, 예시는 다음과 같습니다.

```json
{
  "dataset_id": "demo-dataset",
  "name": "Demo dataset",
  "version": "1.0.0",
  "source": "internal",
  "description": "Example dataset for lm-eval-runner",
  "anything_else": "..."
}
```

### 2.3. TestSample 한 줄 예시

```json
{"id": "sample-1", "messages": [{"role": "user", "content": "Hello"}], "tags": ["greeting"]}
```

---

## 3. 지원 백엔드와 backend_options / 환경 변수

Runner는 `backends/` 디렉터리의 어댑터를 통해 다양한 실행 방식을 지원합니다. 기본 내장 백엔드는 다음과 같습니다.

- **openai**: OpenAI 호환 Chat Completions API 호출 (`openai_backend.py`)
- **adb-cli**: ADB로 연결된 디바이스 안에서 CLI 바이너리를 실행 (`adb_cli_backend.py`)

CLI에서 `--backend` 플래그로 백엔드를 선택하며, `--backend-opt key=value`를 통해 각 백엔드별 옵션을 넘길 수 있습니다.

`--backend-opt`와 `--param` 값은 내부적으로 다음 규칙으로 파싱됩니다.

- `key=value` 형태의 문자열을 입력
- `value`는 우선 `json.loads(value)`로 파싱 시도 후, 실패하면 문자열로 그대로 사용
  - 예) `--param temperature=0.7` → `{"temperature": 0.7}` (float)
  - 예) `--backend-opt request_defaults='{"temperature":0.2,"max_tokens":256}'` → dict

### 3.1. OpenAI backend (`backend=openai`)

구현: `backends/openai_backend.py`

#### 필수/옵션 설정

- **필수 조건**
  - `RunConfig.model` 또는 `backend_options["model"]` 중 하나는 반드시 설정되어야 합니다.
  - API Key는 다음 우선순위로 읽습니다.
    1. `backend_options["api_key"]`
    2. 환경 변수 `OPENAI_API_KEY`
- **선택 옵션**
  - Base URL:
    - `backend_options["base_url"]` 또는 환경 변수 `OPENAI_BASE_URL`
  - 공통 요청 기본값(예: `temperature`, `max_tokens` 등):
    - `backend_options["request_defaults"]` (dict)
  - 실행 시점 파라미터:
    - `RunConfig.parameters` (CLI에서 `--param`으로 주입)

#### 예시: 최소 실행

```bash
lm-eval-runner \
  --dataset ./datasets/hello_world \ 
  --backend openai \
  --model gpt-4.1-mini \
  --backend-opt api_key='"YOUR_API_KEY"' \
  --output-dir ./runs/hello_world_openai
```

#### 예시: 파라미터/옵션 포함

```bash
lm-eval-runner \
  --dataset ./datasets/hello_world \ 
  --backend openai \
  --model gpt-4.1-mini \
  --param temperature=0.2 \
  --param max_tokens=256 \
  --backend-opt api_key='"YOUR_API_KEY"' \
  --backend-opt base_url='"https://api.openai.com/v1"' \
  --backend-opt request_defaults='{"top_p":0.9}' \
  --output-dir ./runs/hello_world_openai
```

### 3.2. ADB CLI backend (`backend=adb-cli`)

구현: `backends/adb_cli_backend.py`

ADB로 연결된 디바이스 내부에서 특정 바이너리를 실행하고, stdin으로 JSON payload를 넘겨 stdout JSON을 읽어 `ChatResponse`로 변환합니다.

#### 필수 backend_options

- `binary`: 디바이스 내부에서 실행할 CLI 바이너리 경로
  - 없을 경우 `BackendError("ADB backend requires 'binary' option", error_type="config")` 발생

#### 선택 backend_options

- `adb_path` (기본값: `"adb"`)
- `device_id` (있으면 `adb -s <device_id>`로 실행)
- `binary_args`
  - 문자열인 경우 `shlex.split()`으로 분해해 인자로 추가
  - 리스트인 경우 각 요소를 문자열로 변환해 인자로 추가

#### CLI 예시

```bash
lm-eval-runner \
  --dataset ./datasets/hello_world \ 
  --backend adb-cli \
  --model my-model-id \
  --backend-opt binary='"/data/local/tmp/chatbot-cli"' \
  --backend-opt device_id='"emulator-5554"' \
  --backend-opt binary_args='"--max-tokens 256 --temperature 0.2"' \
  --output-dir ./runs/hello_world_adb
```

ADB backend는 디바이스 내부 바이너리가 다음과 같은 JSON을 stdin으로 받고, JSON을 stdout으로 반환한다고 가정합니다.

- 입력(JSON):
  - `sample_id`, `messages`, `model`, `parameters`, `metadata`
- 출력(JSON):
  - 최소 `text` 필드 (필수)
  - 선택적으로 `usage`(`input`, `output`, `total`), `finish_reason` 등

---

## 4. `lm-eval-runner` CLI 사용법

엔트리포인트: `src/lm_eval_so/runner/cli.py`

### 4.1. 기본 사용 형태

```bash
lm-eval-runner \
  --dataset <dataset.jsonl or dir> \
  --backend <openai|adb-cli> \
  --model <model_name> \
  --output-dir <run_output_dir> \
  [--metadata <metadata.json>] \
  [--param key=value ...] \
  [--backend-opt key=value ...] \
  [--engine sync] \
  [--max-concurrency N] \
  [--timeout SECS] \
  [--max-retries N] \
  [--rate-limit RPS] \
  [--trace-prefix PREFIX] \
  [--log-level LEVEL] \
  [--version]
```

### 4.2. 주요 옵션 설명

- **Dataset / Metadata**
  - `--dataset` (필수)
    - JSONL 파일 또는 디렉터리 경로
  - `--metadata` (옵션)
    - 명시 시 해당 경로의 JSON을 메타데이터로 사용
    - 미지정 시 디렉터리 모드에서는 `<dataset_dir>/metadata.json` 자동 탐색

- **Backend / 모델 / 파라미터**
  - `--backend`
    - 사용 가능한 값: `openai`, `adb-cli` (또는 registry에 추가한 다른 backend)
  - `--model`
    - OpenAI backend에서는 사실상 필수 (코드에서 미설정 시 에러 발생)
  - `--param key=value` (반복 가능)
    - `RunConfig.parameters[key]`에 매핑
    - 값은 JSON으로 파싱 시도 후, 실패 시 문자열
  - `--backend-opt key=value` (반복 가능)
    - `RunConfig.backend_options[key]`에 매핑
    - 백엔드별 인증정보/엔드포인트/ADB 옵션 등 전달 시 사용

- **Runner 옵션 (`RunnerOptions`)**
  - `--engine`
    - 현재 CLI에서는 `sync`만 노출
    - 내부적으로는 `run_async_job()`을 사용하되, `asyncio.run()`으로 래핑해 동기 CLI 제공
  - `--max-concurrency`
    - 동시에 실행할 샘플 수 (async 세마포어로 제어)
  - `--timeout`
    - 샘플당 timeout(초). `asyncio.wait_for(..., timeout)`에 사용
  - `--max-retries`
    - 재시도 가능한 오류(예: 네트워크/일부 백엔드 오류/timeout 등)에서 최대 재시도 횟수
    - 실제 시도 횟수 = `max_retries + 1`
  - `--rate-limit`
    - 초당 최대 요청 수 (RPS). `_RateLimiter`를 통해 호출 간 간격을 조절
  - `--trace-prefix`
    - `trace_id = "<prefix>-<sample_id>-<random>"` 의 prefix 부분
  - `--output-dir`
    - `run_results.jsonl`, `run_metadata.json`을 저장할 디렉터리 (필수)
  - `--log-level`
    - `DEBUG`, `INFO`, `WARNING`, `ERROR` 등 Python logging 레벨
  - `--version`
    - `lm_eval_so.runner __version__`을 출력하고 종료

---

## 5. 출력 포맷: RunResult JSONL & run_metadata.json

Runner는 실행 결과를 두 개의 파일로 저장합니다.

- `run_results.jsonl` — 각 샘플별 `RunResult.to_record()` 한 줄씩
- `run_metadata.json` — 실행 메타데이터 및 간단 요약 통계

### 5.1. `run_results.jsonl` 한 줄 예시

아래는 `RunResult.to_record()`를 기반으로 한 예시입니다 (한 줄에 한 JSON 객체):

```json
{
  "sample_id": "sample-1",
  "dataset_id": "demo-dataset",
  "backend": "openai",
  "trace_id": "run-sample-1-1a2b3c4d",
  "status": "ok",
  "attempts": 1,
  "latency_ms": 123.4,
  "started_at": "2025-11-23T12:00:00.123456+00:00",
  "completed_at": "2025-11-23T12:00:00.456789+00:00",
  "run_config": {
    "backend": "openai",
    "model": "gpt-4.1-mini",
    "parameters": {
      "temperature": 0.2,
      "max_tokens": 256
    },
    "backend_options": {
      "base_url": "https://api.openai.com/v1"
    }
  },
  "request": {
    "messages": [
      {"role": "user", "content": "Hello"}
    ],
    "context": {
      "sample_tags": ["greeting"],
      "sample_metadata": null,
      "attempt": 1
    }
  },
  "response": {
    "text": "Hi! How can I help you today?",
    "finish_reason": "stop",
    "status_code": 200,
    "tokens": {
      "input": 10,
      "output": 20,
      "total": 30
    }
  },
  "error": null
}
```

Evaluator는 이 JSONL을 입력으로 사용해 샘플별 점수(`EvalScore`)와 집계 결과를 계산할 수 있습니다. 특히 다음 필드들이 평가/리포트에서 자주 사용됩니다.

- `sample_id`, `dataset_id`
- `request.messages` (입력 프롬프트)
- `response.text` (모델 출력)
- `status`, `latency_ms`, `response.tokens.total` 등 실행 메트릭

### 5.2. `run_metadata.json` 예시

`storage.write_run_metadata()`는 다음과 같은 구조의 JSON을 생성합니다.

```json
{
  "generated_at": "2025-11-23T12:00:01.000000+00:00",
  "dataset": {
    "dataset_id": "demo-dataset",
    "name": "Demo dataset",
    "version": "1.0.0",
    "source": "internal",
    "metadata": {
      "dataset_id": "demo-dataset",
      "name": "Demo dataset",
      "version": "1.0.0",
      "source": "internal"
    }
  },
  "run_config": {
    "backend": "openai",
    "model": "gpt-4.1-mini",
    "parameters": {
      "temperature": 0.2
    },
    "backend_options": {
      "base_url": "https://api.openai.com/v1"
    }
  },
  "options": {
    "max_concurrency": 2,
    "timeout_seconds": 60.0,
    "max_retries": 2,
    "retry_backoff_factor": 2.0,
    "retry_backoff_jitter": 0.5,
    "rate_limit_per_second": null,
    "trace_prefix": "run"
  },
  "summary": {
    "total": 1,
    "status_counts": {"ok": 1},
    "latency_ms": {
      "min": 123.4,
      "max": 123.4,
      "avg": 123.4
    },
    "total_tokens": {
      "min": 30,
      "max": 30,
      "avg": 30
    }
  }
}
```

이 파일은 Experiment/Report 메타데이터의 일부로, Evaluator 리포트 상단에 실험 설정 요약을 표시할 때 활용할 수 있습니다.

---

## 6. OpenAI backend 기준 End-to-End 예시

Issue #2의 완료 기준 중 하나는 "OpenAI backend 기준 end-to-end 예시 명령을 README에서 그대로 복붙해서 실행할 수 있음"입니다. 아래는 최소 예시입니다.

### 6.1. 예시 데이터셋 준비

디렉터리 구조:

```text
datasets/
  hello_world/
    test.jsonl
    metadata.json
```

`datasets/hello_world/test.jsonl` 내용 (예시):

```json
{"id": "sample-1", "messages": [{"role": "user", "content": "Hello"}]}
```

`datasets/hello_world/metadata.json` 내용 (예시):

```json
{
  "dataset_id": "hello-world",
  "name": "Hello World dataset",
  "version": "1.0.0"
}
```

### 6.2. 환경 변수 설정

```bash
export OPENAI_API_KEY="YOUR_API_KEY"
```

### 6.3. 실행 명령

```bash
lm-eval-runner \
  --dataset ./datasets/hello_world \
  --backend openai \
  --model gpt-4.1-mini \
  --param temperature=0.2 \
  --param max_tokens=256 \
  --output-dir ./runs/hello_world_openai
```

실행 후에는 다음 파일이 생성됩니다.

- `./runs/hello_world_openai/run_results.jsonl`
- `./runs/hello_world_openai/run_metadata.json`

이 두 파일을 Evaluator 모듈에 입력하면, per-sample 점수 및 전체 리포트를 생성할 수 있습니다.

---

## 7. ADB CLI backend 간단 예시

ADB backend를 사용할 경우, 디바이스 내부에 JSON 기반 CLI를 배포해 두었다고 가정합니다.

```bash
lm-eval-runner \
  --dataset ./datasets/hello_world \
  --backend adb-cli \
  --model my-model-id \
  --backend-opt binary='"/data/local/tmp/chatbot-cli"' \
  --backend-opt device_id='"emulator-5554"' \
  --backend-opt binary_args='"--max-tokens 256 --temperature 0.2"' \
  --output-dir ./runs/hello_world_adb
```

디바이스 내부 바이너리는 stdin으로 다음 형식의 JSON을 받고, stdout으로 JSON을 반환해야 합니다.

```json
{
  "sample_id": "sample-1",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "model": "my-model-id",
  "parameters": {"temperature": 0.2},
  "metadata": null
}
```

stdout 예시:

```json
{
  "text": "Hi from device!",
  "usage": {
    "input": 10,
    "output": 20,
    "total": 30
  },
  "finish_reason": "stop"
}
```

---

## 8. Evaluator / Report와의 연결

Runner는 **Runner(실행) – Evaluator(채점) – Reporter(리포트)** 파이프라인에서 "실행 로그 생산" 역할을 담당합니다.

- Evaluator는 `run_results.jsonl`을 읽어 다음 정보를 기반으로 점수를 계산합니다.
  - `TestSample` (입력/메타데이터/태그)
  - `RunResult.response.text` (모델 출력)
  - `RunResult.status`, `latency_ms`, `response.tokens.total` 등 실행 메트릭
- `run_metadata.json`은 Experiment/Report 상단에서 다음 정보를 요약하는 데 사용됩니다.
  - Dataset 정보 (`dataset`)
  - RunConfig/Backend 설정 (`run_config`)
  - Runner 옵션 (`options`)
  - 실행 요약 메트릭 (`summary.total`, `summary.status_counts`, `summary.latency_ms`, `summary.total_tokens` 등)

이 README만으로도 Dataset + Backend + RunConfig를 어떻게 조합해서 실행하고, 생성된 RunResult JSONL을 Evaluator에 어떻게 넘기는지 전체 흐름을 이해할 수 있도록 구성되어 있습니다.