먼저 전체 컨셉은 이미 아주 잘 잡아두셨습니다.
이제 “어디를 잘 설계해야 나중에 안 후회할지”를 중심으로, 모듈별로 찝어보겠습니다.
(이 답변에서는 가운데 모듈 이름을 **runner (Chat Test Runner)** 로 부르겠습니다.)

---

## 0. 전체 프레임워크 관점에서 먼저 잡아둘 것

3개 모듈을 따로 개발하더라도, **공통으로 공유해야 깔끔해지는 개념**이 있습니다.

### 공통 도메인 모델 (반드시 shared 패키지로 뺄 것)

최소한 이 정도는 `chatbot_tester_core` 같은 공통 패키지로 분리해 두시는 걸 추천드립니다.

* `TestSample`

  * `id`
  * `input` (텍스트, multi-turn, 이미지 등)
  * `meta` (언어, 토픽, 난이도, 태그 등)
* `TestCase`

  * `id`
  * `samples: List[TestSample]` (혹은 1:1 상관 관계)
  * `task_type` (translation, summarization, style_transfer, chit-chat 등)
  * 기대 출력 존재 여부 (`has_reference: bool`)
* `RunConfig`

  * 어떤 챗봇/모델/엔드포인트를, 어떤 설정으로 돌릴지
  * 예: `model_id, api_base, temperature, max_tokens, system_prompt, headers…`
* `RunResult`

  * `sample_id`
  * `request_payload`
  * `response`
  * `latency_ms`, `status`, `error`
* `EvalScore`

  * `metric_name`
  * `value`
  * `detail` (sub-scores, raw LLM-judge response 등 저장)

이 공통 모델이 깔끔해야,
**Generator → Runner → Evaluator → Report** 흐름이 자연스럽게 이어집니다.

---

## 1. DataSet 생성 모듈 (Generator)

### 1-1. 가장 고민해야 할 포인트

1. **데이터 포맷 설계 (JSONL / Parquet / DB / 기타)**

   * 최소 단위를 무엇으로 할지

     * `sample` 단위?
     * `scenario` 단위(여러 턴/조건이 묶인 세트)?
   * 추천

     * 외부 노출/교환용: `JSONL` (한 줄 = 한 sample)
     * 내부/대량 처리/분석: `Parquet` or DB (나중에 대규모 테스트 시 유리)

2. **Task-agnostic vs Task-specific 구조**

   * 공통 필드 + task-specific 필드를 어떻게 나눌지:

     * `task_type: "translation" | "summarization" | ...`
     * `task_payload: Dict` 안에 세부 필드 넣는 식으로 확장성 확보
   * 장점

     * 같은 프레임워크로 여러 테스트 유형(번역/요약/스타일변환/챗봇 QA)을 커버

3. **Source → Canonical Format 변환 파이프라인**

   * 원천 데이터가 제각각일 때 (CSV, Excel, DB, JSON 등)
   * 공통 패턴:

     1. `Loader` (파일/DB에서 로딩)
     2. `Normalizer` (컬럼명/필드 통일)
     3. `Mapper` (Canonical `TestSample`로 변환)
     4. `Filter` (언어/길이/태그 필터링)
   * 이를 **Composable pipeline** 으로 만들지,
     단순 함수 모음으로 갈지 고민 필요

4. **버전 관리 & 재현성**

   * 같은 데이터셋을 다시 만들었을 때, “동일 버전”이라는 것을 보장할 수 있어야 합니다.
   * 필수 요소:

     * `dataset_id` + `version` (예: `translation_kr2jp_v1`)
     * 생성 스크립트/원천 데이터 Commit hash 기록
     * `metadata.json` 안에

       * 생성 일시
       * 사용한 코드 버전
       * 필터 조건, 샘플 수 등…

5. **샘플링 전략**

   * 전체 코퍼스에서 어떤 기준으로 N개를 뽑을지

     * 랜덤, 난이도 기반, 길이 기반, 토픽 균형 등
   * 나중에 “이 테스트셋이 어디를 커버하고 있는지”를 설명해야 하므로,

     * 샘플링 전략도 메타데이터로 남길 필요 있음

### 1-2. Generator 모듈 기본 아키텍처 예시

```text
dataset_generator/
  ├─ loaders/        # CSVLoader, ExcelLoader, DBLoader...
  ├─ transformers/   # Normalizer, Mapper, Filter, Sampler...
  ├─ writers/        # JSONLWriter, ParquetWriter, DBWriter...
  ├─ registry.py     # 데이터셋별 생성 파이프라인 등록
  └─ cli.py          # `gen-dataset --name translation_kr2jp_v1` 같은 CLI
```

* 핵심: 새로운 데이터셋을 추가할 때,
  `registry`에 “파이프라인 정의 하나 추가”로 끝나게 만드는 것.

---

## 2. Chat Test Runner (컨트롤러)

여기가 **가장 사고가 많이 필요한 부분**입니다.
왜냐하면, 실제로 이 모듈이 “외부 챗봇/모델들과 맞닿는 경계층”이기 때문입니다.

### 2-1. 가장 고민해야 할 포인트

1. **챗봇/엔드포인트 추상화 (Adapter/Plugin 구조)**

   공통 인터페이스 예:

   ```python
   class ChatBackend(Protocol):
       def send(self, messages: list[Message], config: RunConfig) -> ChatResponse:
           ...
   ```

   * 구현체 예:

     * `OpenAIBackend`, `LocalLlamaBackend`, `HttpGenericBackend`, `OnDeviceSdkBackend` …
   * 새로운 모델/엔드포인트 추가 시,

     * Adapter 하나만 만들면 Runner 나머지는 건드리지 않는 구조.

2. **대화 상태 관리 (세션 / 컨텍스트)**

   * 단일 턴 vs 멀티 턴 대화 테스트:

     * `Session` 개념이 필요할 수 있음
   * 기본 구조:

     * `ConversationState`

       * `history: List[Message]`
       * `meta (세션 id, 테스트 case id 등)`
   * Runner 가 해야 할 일:

     * `TestSample` → `Message 리스트` 로 매핑
     * 필요 시 이전 턴까지 포함해 보내기 (context window 관리)

3. **동시성, Rate Limit, Retry 전략**

   * 실제 운영 챗봇 또는 OpenAI 같은 API를 두드리면

     * Rate limit / timeout / 에러 발생이 필수적으로 따라옴
   * 설계 포인트

     * 동시 실행: `asyncio`, `ThreadPool`, `Ray` 등 무엇으로 할지
     * Rate limiter: 토큰/초, 요청/분 단위
     * Retry 정책: 백오프 전략, 오류 분류 (429/500/타임아웃)

4. **로깅 & 추적 (Observability)**

   * 최소한 저장해야 할 것:

     * 요청 메시지, 응답 메시지, latency, 에러, 시도 횟수
   * 나중에 “이 모델이 왜 이렇게 점수가 낮지?” 라고 했을 때,

     * Runner 로그만으로 충분히 리플레이/디버깅 가능해야 함

5. **입·출력 스키마의 안정성**

   * Runner 의 결과물(`RunResult`)은
     Evaluator와 리포팅이 모두 공유하게 되는 핵심 포맷
   * 절대 “프로토타이핑 단계의 구조”로 방치하면 안 되고,

     * 초기에 시간을 들여 안정적인 스키마를 정의하는 것이 좋습니다.
   * 예:

     ```json
     {
       "sample_id": "xxx",
       "backend": "openai:gpt-4.1",
       "request": {...},
       "response": {
         "text": "...",
         "tokens": {
           "input": 123,
           "output": 456
         }
       },
       "latency_ms": 843,
       "status": "ok",
       "error": null
     }
     ```

6. **실행 단위 설계**

   * 어떤 단위를 “한 번의 run”으로 볼지:

     * 단일 RunConfig + 단일 Dataset?
     * 복수 모델 × 동일 Dataset을 한 번에 돌리는 Job?
   * 추천:

     * Runner는 “**(Dataset, Backend, RunConfig) → RunResult 집합**” 을 처리하는
       최소 단위 Job 을 기준으로 설계
     * 상위 레벨에서 여러 Job을 조합하여 실험(Experiment) 개념으로 관리

### 2-2. Runner 모듈 기본 아키텍처 예시

```text
chat_runner/
  ├─ backends/          # OpenAIBackend, HttpBackend, LocalLLMBackend...
  ├─ session/           # ConversationState, Message 모델
  ├─ rate_limit/        # RateLimiter, RetryPolicy
  ├─ runner.py          # Dataset + Backend + Config → RunResult[]
  ├─ storage/           # 결과 저장(JSONL, DB, S3 등)
  └─ cli.py             # `run-test --dataset xxx --backend openai:gpt-4.1 ...`
```

---

## 3. 평가 모듈 (Evaluator)

### 3-1. 가장 고민해야 할 포인트

1. **Metric/Strategy 추상화**

   * 공통 인터페이스:

     ```python
     class Evaluator(Protocol):
         def evaluate(self, run_results: list[RunResult], dataset: Dataset) -> list[EvalScore]:
             ...
     ```
   * 구현체 유형:

     * Rule-based (정규식, 키워드 포함 여부 등)
     * String similarity (BLEU, ROUGE, BERTScore 등)
     * LLM-as-a-judge (G-Eval 계열)
     * Task-specific (예: 번역 품질 vs 요약 정보보존 vs 스타일 일치도)

2. **단일 샘플 vs 집계 레벨**

   * 두 레벨이 모두 있어야 합니다.

     * `per-sample score` (각 샘플 별 세부 점수)
     * `aggregated score` (mean, std, histogram, by-tag breakdown 등)
   * 구조 예:

     * `EvalResult`

       * `sample_scores: Dict[sample_id, Dict[metric_name, value]]`
       * `summary: Dict[metric_name, AggregateStat]`

3. **LLM 기반 평가(G-Eval류) 설계 포인트**

   * 프롬프트 템플릿 버전 관리

     * `prompt_id`, `version`, `language`
   * 평가 기준의 명세화

     * 예: `correctness`, `fluency`, `faithfulness` 등 서브 스코어
   * 비용 최적화

     * 캐싱 (동일 응답에 대해 반복 평가 방지)
     * 샘플링 (데이터셋 일부만 LLM-judge 적용, 나머지는 lightweight metric 사용)

4. **Task 타입별 Metric 구성**

   * 예:

     * 번역 → BLEU, COMET, LLM-judge 등
     * 요약 → ROUGE, BERTScore, LLM-judge (정보보존/간결성)
     * 스타일 변환 → LLM-judge 기반 (스타일 일치도, 의미 유지도)
     * 일반 QA → Exact match / F1 / LLM-judge

   * 이걸 config 드리븐으로:

     ```yaml
     task_type: translation
     metrics:
       - name: bleu
       - name: llm_judge
         prompt_id: translation_pair_v1
     ```

5. **결과 저장 & 리포트 구조**

   * 나중에 “모델 간 비교/버전 간 비교”를 손쉽게 하려면,

     * 최소한 다음 구조를 생각해야 합니다.
   * 개념:

     * `Experiment` (dataset + backend + run_config + evaluator_config)
     * `EvalReport`

       * 실험 ID, 설명
       * 요약 메트릭 테이블
       * 태그별/길이별/언어별 breakdown
   * 출력 포맷:

     * JSON (머신 친화)
     * Markdown/HTML (사람 설명용)

### 3-2. Evaluator 모듈 기본 아키텍처 예시

```text
evaluator/
  ├─ metrics/
  │   ├─ bleu.py
  │   ├─ rouge.py
  │   ├─ bertscore.py
  │   └─ llm_judge.py
  ├─ registry.py       # metric/evaluator 등록
  ├─ orchestrator.py   # config 기반으로 여러 metric 조합 실행
  ├─ report/
  │   ├─ json_reporter.py
  │   └─ md_reporter.py
  └─ cli.py            # `eval-run --run-id xxx --config eval_config.yaml`
```

---

## 4. 상위 리포지토리(지금 이 repo)의 역할 설계

지금 repo (`chatbot-tester`)는 **“빌드/통합/공통 infra 제공자”** 포지션이므로,
아키텍처를 다음처럼 생각해볼 수 있습니다.

```text
chatbot-tester/
  ├─ src/
  │   ├─ chatbot_tester_core/      # 공통 도메인 모델, 공용 유틸
  │   ├─ chatbot_tester_generator/ # git submodule → dataset_generator repo
  │   ├─ chatbot_tester_runner/    # git submodule → chat_runner repo
  │   ├─ chatbot_tester_evaluator/ # git submodule → evaluator repo
  │   └─ chatbot_tester_cli/       # generator/runner/evaluator를 하나로 묶은 CLI
  ├─ pyproject.toml / setup.cfg
  └─ docs/
      ├─ architecture.md
      ├─ dataflow.md  # Generator → Runner → Evaluator 흐름
      └─ plugin_guide.md
```

* 상위 리포지토리에서 신경 쓸 것:

  * 공통 의존성 버전 관리
  * 서브모듈 업데이트/빌드 스크립트
  * 전체 CLI/Entry point (`chatbot-tester ...`) 제공
  * 문서/튜토리얼 관리

---

## 5. 정리

1. **공통 도메인 모델을 먼저 박고 (core 패키지),**
2. Generator/Runner/Evaluator는

   * 각자 도메인에 충실하되
   * 공통 포맷(TestSample / RunResult / EvalScore)을 기준으로 느슨하게 결합
3. Runner는 “여러 챗봇/엔드포인트를 깔끔하게 추상화 + 동시성/에러/로그 관리”에 신경
4. Evaluator는 “metric을 어떻게 플러그인화하고, LLM 기반 평가를 어떻게 버전/비용 관리”할지 설계