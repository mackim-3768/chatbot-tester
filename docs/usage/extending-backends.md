# Backend 확장 가이드 (새 Backend 추가하기)

이 문서는 Runner 모듈에 **새 Backend(모델/엔드포인트)** 를 추가하는 방법을 정리합니다.

- `ChatBackend` 인터페이스 개념
- OpenAI Backend 구현 구조
- timeout / retry / rate-limit / 로깅 베스트 프랙티스

> 실제 구현 코드는 `src/lm_eval_so/core/backends/` 와 `src/lm_eval_so/core/backends/base.py` 를 함께 참고하세요.

---

## 1. ChatBackend 인터페이스 개념

Runner는 다음 개념 위에서 동작합니다.

- **Dataset**: `TestSample` 리스트 (입력 메시지/expected/tags/metadata 포함)
- **RunConfig**: 어떤 backend/모델/파라미터로 실행할지에 대한 설정
- **ChatBackend**: 실제 외부 시스템(API/로컬 모델/ADB 등)에 요청을 보내는 어댑터

`ChatBackend`는 대략 다음과 같은 인터페이스를 가집니다.

```python
class ChatBackend(Protocol):
    async def send(self, request: RunRequest) -> ChatResponse:
        ...
```

- `RunRequest`
  - `sample`: 실행 대상 `TestSample`
  - `run_config`: backend/모델/파라미터 정보
  - `dataset_info`: dataset 메타데이터
  - `trace_id`, `attempt`, `timeout_seconds` 등 실행 컨텍스트
- `ChatResponse`
  - `text`: 모델 응답 텍스트
  - `usage`: 토큰 사용량 정보(optional)
  - `status_code`, `headers`, `raw`(원본 응답 payload) 등

Backend 구현체는 이 인터페이스를 만족하며, 에러 상황에서는 `BackendError` 예외를 일관된 방식으로 던져야 합니다.

---

## 2. OpenAI Backend 예시 구조

OpenAI Backend(예: `openai_backend.py`)는 `AsyncOpenAI` 클라이언트를 감싼 어댑터입니다.

핵심 포인트:

- Backend 등록

  ```python
  @register_backend("openai")
  class OpenAIChatBackend(ChatBackend):
      ...
  ```

  - `@register_backend("openai")` 데코레이터를 통해 registry에 이름을 등록합니다.
  - Runner CLI에서 `--backend openai` 로 선택할 수 있게 됩니다.

- 초기화 & 클라이언트 생성

  ```python
  def _get_client(self) -> AsyncOpenAI:
      api_key = self.backend_options.get("api_key") or os.getenv("OPENAI_API_KEY")
      if not api_key:
          raise BackendError("OPENAI_API_KEY is not set", error_type="auth", retryable=False)
      base_url = self.backend_options.get("base_url") or os.getenv("OPENAI_BASE_URL")
      self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
      return self._client
  ```

  - 환경 변수 또는 backend 옵션으로 API 키/엔드포인트를 주입
  - 키가 없으면 `BackendError(error_type="auth")` 로 명확히 실패

- 요청 전송

  ```python
  async def send(self, request: RunRequest) -> ChatResponse:
      client = self._get_client()
      model = request.run_config.model or self.backend_options.get("model")
      if not model:
          raise BackendError("RunConfig.model is required for OpenAI backend", error_type="config", retryable=False)

      params = {
          "model": model,
          "messages": _build_messages(request.messages),
      }
      params.update(self.backend_options.get("request_defaults", {}))
      params.update(request.run_config.parameters)

      try:
          resp = await client.chat.completions.create(**params)
      except RateLimitError as exc:
          raise BackendError(str(exc), error_type="rate_limit", status_code=429, retryable=True)
      except (APIConnectionError, APIError) as exc:
          retryable = getattr(exc, "status_code", 500) >= 500
          raise BackendError(str(exc), error_type="api_error", status_code=getattr(exc, "status_code", None), retryable=retryable)
      except (BadRequestError, AuthenticationError) as exc:
          raise BackendError(str(exc), error_type="request_error", status_code=getattr(exc, "status_code", None), retryable=False)
      except Exception as exc:
          raise BackendError(str(exc), error_type="unknown", retryable=False)

      choice = resp.choices[0]
      text = choice.message.content or ""
      usage = None
      if resp.usage is not None:
          usage = TokenUsage(
              input_tokens=resp.usage.prompt_tokens,
              output_tokens=resp.usage.completion_tokens,
              total_tokens=resp.usage.total_tokens,
          )

      return ChatResponse(
          text=text,
          raw=resp.model_dump(mode="python"),
          usage=usage,
          finish_reason=choice.finish_reason,
          status_code=200,
      )
  ```

  - RunConfig.parameters + backend_options.request_defaults 를 합쳐 OpenAI Chat Completions 호출
  - 다양한 예외를 `BackendError` 로 래핑해 Runner가 처리하기 쉽게 만듦
  - 응답을 `ChatResponse` 로 변환해 Runner로 반환

---

## 3. 새 Backend 추가 절차

새 Backend를 추가할 때의 공통 패턴은 다음과 같습니다.

1. `ChatBackend` 인터페이스를 구현하는 클래스 작성
2. `@register_backend("이름")` 데코레이터로 registry 등록
3. Backend 옵션/환경 변수 설계 (`api_key`, `base_url`, `request_defaults` 등)

### 3.1 예: Dummy Backend (고정 응답)

테스트/CI 용도로 **외부 API를 호출하지 않고 고정 응답만 반환**하는 Backend를 만들 수 있습니다.

개념적 예:

```python
@register_backend("dummy")
class DummyBackend(ChatBackend):
    async def send(self, request: RunRequest) -> ChatResponse:
        text = "This is a dummy response for sample=" + request.sample.id
        return ChatResponse(text=text)
```

이렇게 하면 Runner CLI에서:

```bash
python -m lm_eval_so.runner.cli \
  --dataset path/to/dataset \
  --backend dummy \
  --output-dir runs/dummy
```

형태로 빠른 스모크 테스트를 구현할 수 있습니다.

### 3.2 예: HTTP Generic Backend

어떤 REST API에 `POST /chat` 형태로 요청하고 싶은 경우, 다음과 같은 패턴을 사용할 수 있습니다.

- backend 옵션에:
  - `base_url`: API 베이스 URL
  - `headers`: 인증/커스텀 헤더
  - `request_template`: body 스키마 (messages + run_config를 어떻게 넣을지)

Backend 내부에서는:

- `httpx.AsyncClient` 등으로 HTTP 요청 전송
- 응답 JSON에서 텍스트/토큰 정보만 골라 `ChatResponse` 로 변환

이때도, 오류는 반드시 `BackendError` 로 래핑해 Runner에 전달해야 합니다.

---

## 4. timeout / retry / rate-limit / 로깅 베스트 프랙티스

### 4.1 timeout

- **어디서 timeout을 거는지**가 중요합니다.
  - Runner 레벨: `asyncio.wait_for(backend.send(...), timeout=options.timeout_seconds)`
  - Backend 레벨: HTTP 클라이언트 타임아웃 설정
- 권장 패턴
  - Backend에서는 클라이언트 기본 timeout만 설정
  - Runner에서 per-sample timeout을 일관되게 관리 (이미 구현되어 있음)

### 4.2 retry

- 재시도 로직은 **Runner 쪽**에 두는 것이 일반적입니다.
  - Backend는 `BackendError(retryable=True/False)` 로만 의도 전달
  - Runner는 `max_retries`, `retry_backoff_factor`, `retry_backoff_jitter` 를 사용해 backoff 전략 적용
- Backend 구현에서는:
  - 429, 5xx, 네트워크 에러 등 **재시도 가능한 오류**는 `retryable=True` 로 표시
  - 인증/구성 오류(401/403/400 등)는 `retryable=False`

### 4.3 rate-limit

- Runner에는 `_RateLimiter` 가 있어 초당 요청 수를 제어할 수 있습니다.
- Backend는 rate-limit을 모르면 **최대한 단순히 API 에러만 전달**하고,
  - Runner의 `rate_limit_per_second` 옵션을 통해 전체 실행 속도를 제어하는 구조를 추천합니다.

### 4.4 로깅 / Observability

Backend/Runner 설계 시 반드시 남겨야 할 정보:

- 요청/응답 요약 (전체 raw payload가 아니라도, 텍스트/토큰/상태코드 정도)
- latency, 시도 횟수, trace_id
- error_type / status_code / retryable 여부

권장 패턴:

- Runner의 logger (`lm_eval_so.runner`) 를 사용해 structured logging 지향
- `trace_prefix`/`trace_id` 를 이용해 한 execution 흐름을 추적 가능하게 만들기

---

## 5. 요약

- Backend는 외부 시스템을 감싸는 **어댑터**이며, Runner는 이를 통해 `(Dataset × Backend × RunConfig) → RunResult[]` 를 실행합니다.
- 새 Backend를 추가하려면:
  1. `ChatBackend` 인터페이스를 구현하는 클래스 작성
  2. `@register_backend("이름")` 로 registry에 등록
  3. 필요시 backend 옵션/환경 변수 설계 (`api_key`, `base_url`, `request_defaults` 등)
- timeout/retry/rate-limit은 **Runner와 Backend의 역할을 분리**해서 설계하고,
  - Backend는 오류를 `BackendError(error_type, retryable, status_code, details)` 로만 표현
  - Runner가 동시성/재시도/속도 제어를 담당하도록 하는 것이 바람직합니다.
- 로깅/trace를 충분히 남겨두면, 나중에 점수가 낮은 구간을 디버깅하거나
  새로운 Backend를 붙일 때도 훨씬 수월해집니다.
