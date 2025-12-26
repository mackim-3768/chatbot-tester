# Daily Framework Planning – 2025-Wxx-dayN

> Repository: chatbot-tester
> Type: Library / SDK (Generator · Runner · Evaluator)
> Cadence: Daily (주차 내 일차별 사고 기록)
> Focus: Architecture, API design, extensibility, reproducibility

---

## Language Rule (MANDATORY)

- 본 문서의 **모든 내용은 반드시 한국어로 작성**합니다.
- 다음 항목만 예외적으로 영어 사용을 허용합니다:
  - 코드 블록
  - 파일 경로
  - 함수명 / 클래스명 / 모듈명
  - CLI 커맨드
  - 고유 명사 (예: OpenAI, CLI, SDK, Generator, Runner, Evaluator)
- 번역체가 아닌 **기술 기획 문서에 적합한 자연스러운 한국어**를 사용합니다.

---

## 1. Discovery (Ideas)

> Goal: 재사용 가능한 SDK 관점에서의 프레임워크 수준 개선 아이디어를
> **하루 단위로 축적**한다.

### Idea 1
- Affected layer: Generator / Runner
- Current limitation: Generator 모듈이 `openai.OpenAI` 동기 클라이언트를 직접 사용하여, Runner가 지원하는 다양한 백엔드(Azure, Custom)를 활용하지 못하고 중복된 설정 관리 로직을 가짐.
- Proposed improvement: `ChatBackend` 추상화 및 구현체를 `core` 영역으로 이동하고, Generator가 이를 활용하도록 리팩토링.
- Why this matters for an SDK: LLM 연결 로직의 일관성을 확보하고, 사용자가 Generator에서도 Azure OpenAI나 로컬 LLM을 손쉽게 사용할 수 있게 함.

### Idea 2
- Affected layer: Common
- Current limitation: `Message`, `TestSample` 등의 도메인 모델이 각 서브 모듈(generator, runner)에 파편화되어 있어, 모듈 간 데이터 전달 시 변환 로직이 필요함.
- Proposed improvement: 핵심 도메인 모델을 `chatbot_tester.core.types` 또는 `chatbot_tester.core.models`로 통합.
- Why this matters for an SDK: 모듈 간 결합도를 낮추고 데이터 흐름을 단순화하여 프레임워크의 유지보수성 향상.

### Idea 3
- Affected layer: All (Generator / Runner / Evaluator)
- Current limitation: 모듈별로 설정 관리 방식이 제각각임 (`StructureSpec`, `RunnerOptions`, `EvaluatorConfig`). CLI 사용 시 여러 개의 설정 파일을 관리해야 하는 불편함 존재.
- Proposed improvement: 전체 파이프라인을 아우르는 `TesterConfig` 도입 및 단일 YAML 파일 지원.
- Why this matters for an SDK: 사용자 경험(UX)을 통일하고, CI/CD 파이프라인에서의 설정 관리를 용이하게 함.

### Idea 4
- Affected layer: Generator
- Current limitation: `DocToQALoader` 등의 데이터 로더가 하드코딩되어 있어, 사용자가 새로운 데이터 소스(SQL, Custom API 등)를 추가하기 어려움.
- Proposed improvement: `BackendRegistry`와 유사한 `LoaderRegistry`를 도입하여 데이터 소스를 플러그인 형태로 확장 가능하게 변경.
- Why this matters for an SDK: SDK 사용자에게 데이터 파이프라인의 유연성을 제공하여 다양한 운영 환경에 대응 가능.

### Idea 5
- Affected layer: Common
- Current limitation: `Generator`는 파일 시스템 기반 캐싱을, `Runner`는 `storage` 모듈을 통한 별도 저장을 수행하여 데이터 관리 방식이 불일치함.
- Proposed improvement: 통합된 캐싱 및 아티팩트 저장소 인터페이스(`StorageBackend`)를 정의하고 S3, 로컬 파일시스템 등을 지원.
- Why this matters for an SDK: 대규모 데이터셋 처리 시 효율적인 자원 관리 및 중간 결과물 재사용성 증대.

---

## 2. Triage

> Goal: **오늘 기준** 가장 아키텍처적 파급력이 큰 1개 아이디어를 선정한다.

### Selected Idea
- Title: Generator의 ChatBackend 통합 및 비동기 전환
- Primary affected layer(s): Generator, Runner, Core

### Selection Rationale
- Architectural leverage: 프레임워크 전반의 "LLM 접근 계층"을 단일화하여 중복 코드를 제거하고 일관된 동작을 보장함.
- Impact on extensibility / reuse: Generator가 `Runner`의 모든 백엔드(Azure, Local 등)를 즉시 활용할 수 있게 되어 확장성이 대폭 향상됨.
- Reduction of future complexity: 향후 백엔드 관련 기능(재시도, 로깅, 비용 추적 등) 추가 시 한 곳만 수정하면 되므로 유지보수 비용 절감.

### Deferred Ideas (Brief)
- Idea 2 (Shared Domain Models): 중요하지만 `ChatBackend` 통합 이후에 진행하는 것이 의존성 정리에 더 효율적임.
- Idea 3 (Unified Configuration): 현재 구조에서도 동작에는 문제가 없으므로 우선순위 낮음.
- Idea 4 (Loader Plugin): 현재 데이터 소스 요구사항이 다양하지 않아 추후 고려.
- Idea 5 (Unified Storage): 캐싱 전략 통합은 구현 복잡도가 높아 별도 기획 필요.

---

## 3. Spec Draft (Top 1 Only)

### Feature / Improvement Name
Generator의 ChatBackend 통합 및 비동기 전환

### Problem Statement
- 현재 `Generator`는 `openai` 패키지를 직접 import하여 동기 방식으로 호출하므로, `Runner`가 `ChatBackend`를 통해 지원하는 Azure OpenAI, vLLM 등의 다양한 백엔드를 사용할 수 없음.
- API 키 관리, Base URL 설정, 재시도 로직 등이 `Generator`와 `Runner`에 중복 구현되어 있어 유지보수가 어렵고 사용자에게 혼란을 줌.

### Design Approach (High-level)
- Core concept: `ChatBackend` 추상화 및 구현체를 `chatbot_tester.core`로 이동시켜 공유 자산화하고, Generator를 비동기 기반으로 리팩토링하여 이를 활용하도록 변경.
- Key abstractions or interfaces:
  - `src/chatbot_tester/core/backends/`: `ChatBackend`, `OpenAIChatBackend`, `BackendRegistry` 이동.
  - `Generator`: 내부 로직을 `async/await`로 전환하고 `_request_batch` 대신 `ChatBackend.send()` 사용.
- Expected behavior:
  - 사용자는 `generator` 명령어 실행 시 `--backend` 옵션(또는 설정)을 통해 모델 제공자를 선택할 수 있음.
  - `openai` 외에도 `Runner`에 등록된 모든 백엔드를 사용하여 데이터 생성이 가능해짐.

### MVP Scope
- Included in MVP:
  - `ChatBackend` 관련 코드의 `src/chatbot_tester/core/` 이동.
  - `Generator`의 핵심 루프(`_generate_samples_via_openai`)를 비동기 함수로 변환.
  - `Generator` CLI 진입점에 `asyncio.run()` 적용.
  - 기존 `Generator` 기능의 회귀(Regression) 방지 테스트.
- Explicitly excluded:
  - 스트리밍 응답 처리 (Batch 생성은 스트리밍 불필요).
  - 복잡한 병렬 처리 최적화 (기존 배치 처리 구조 유지).

### Optional / Future Extensions
- `Generator` 전용의 고속 비동기 배치 처리 파이프라인 구축.
- `ChatBackend`에 비용 계산(Token counting) 기능 표준화.

### Acceptance Criteria
- [ ] `ChatBackend`가 `core` 패키지로 이동되어 `generator`와 `runner` 양쪽에서 import 가능해야 함.
- [ ] `generator` 모듈이 `openai` 라이브러리를 직접 import 하지 않고 `ChatBackend`를 통해 통신해야 함.
- [ ] 기존 CLI 명령어로 `generator` 실행 시 정상적으로 데이터가 생성되어야 함.
- [ ] 단위 테스트가 통과하며, 구조 변경으로 인한 에러가 없어야 함.

---

## 4. Backlog Draft (Issue-Level)

### Suggested GitHub Issue Title
`[Framework][Core] Generator의 ChatBackend 통합 및 비동기 구조 전환`

### Task Breakdown
- [ ] Core implementation
  - Module: `chatbot_tester.core`, `chatbot_tester.runner`, `chatbot_tester.generator`
  - Summary: `ChatBackend` 이동, `runner` 참조 수정, `generator` 로직 비동기 전환 및 백엔드 연동.
- [ ] CLI changes (if any)
  - Command: `chatbot-tester generator run`
  - Flags / options: `--model` 외에 `--backend` 옵션 추가 (기본값: openai).
- [ ] API impact
  - Breaking change: Yes (내부 API 위치 변경, Generator 함수가 async로 변경됨).
  - Migration needed: Yes (`runner` 사용자 정의 백엔드 사용자는 import 경로 수정 필요).
- [ ] Tests
  - Unit / Integration: 변경된 `generator` 로직에 대한 Mock 백엔드 기반 테스트 작성.
- [ ] Documentation
  - README / Examples / Docstrings: 변경된 모듈 경로 및 Generator의 백엔드 설정 방법 업데이트.

### Notes
- Backward compatibility concerns: `runner.backends`에서 `ChatBackend`를 임포트하던 기존 코드가 깨질 수 있으므로, 기존 위치에 alias를 남겨두는 것(`from ..core.backends import ChatBackend`)을 고려해야 함.
- Refactoring risk: `generator`의 프롬프트 구성 로직(`json_object` format 등)이 특정 백엔드(OpenAI)에 종속적일 수 있으므로, `ChatBackend` 인터페이스가 이를 수용할 수 있는지 확인 필요.

---

## 5. Docs / Notes

### README Updates
- 추가 또는 수정할 섹션: "Architecture" 섹션에 Core 모듈의 역할 추가, "Generator" 섹션에 백엔드 설정 가이드 추가.
- 전달하고자 하는 핵심 메시지: "이제 Generator와 Runner가 동일한 백엔드 시스템을 공유하므로, 한 번의 설정으로 모든 단계에서 다양한 LLM을 활용할 수 있습니다."

### Example Snippet (Optional)

```python
# Before
from chatbot_tester.runner.backends import OpenAIChatBackend

# After
from chatbot_tester.core.backends import OpenAIChatBackend

# Generator usage (Programmatic)
import asyncio
from chatbot_tester.generator import generate_structured_synthetic_dataset

async def main():
    # 이제 비동기로 실행되거나, 내부적으로 이벤트 루프를 처리할 수 있음
    await generate_structured_synthetic_dataset(...)

if __name__ == "__main__":
    asyncio.run(main())
```
