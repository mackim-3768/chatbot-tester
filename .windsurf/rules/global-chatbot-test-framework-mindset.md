---
trigger: always_on
---

당신은 항상 다음 “Chatbot Test Framework 3-모듈 아키텍처”를 기반으로 사고해야 합니다.

① Core(shared domain model)
- TestSample(id, input, meta)
- TestCase
- RunConfig(model/backend/config)
- RunResult(request/response/latency/status)
- EvalScore(metric/value/detail)

② Generator
- Loader → Normalizer → Mapper → Filter → Sampler → Writer
- Dataset versioning: dataset_id, version, metadata
- 입력 데이터 → Canonical TestSample 구조로 정규화

③ Runner
- (Dataset × Backend × RunConfig) → RunResult 집합
- ChatBackend Adapter 구조 유지 (OpenAIBackend, HttpBackend 등)
- Rate limit, retry, timeout, logging(request/response/latency)
- Multi-turn context 관리
- RunResult 스키마 절대 깨지지 않게 유지

④ Evaluator
- Metric plugin 구조 (BLEU/ROUGE/BERTScore/LLM-Judge 등)
- per-sample score + aggregate score
- LLM Judge prompt_id/version 관리
- Experiment / Report 구조 유지

요청에 답변할 때는 위 4개 모듈 구조를 항상 기본 전제로 두고 답변하십시오.
