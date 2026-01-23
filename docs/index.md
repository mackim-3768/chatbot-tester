# chatbot-tester 문서

`chatbot-tester`는 챗봇을 체계적으로 **테스트·평가**하기 위한 상위 프레임워크입니다.

- **Generator**
  - 원천 데이터(CSV/JSONL 등)를 canonical `TestSample` 데이터셋으로 변환
- **Runner**
  - Dataset × Backend × RunConfig 조합으로 실제 챗봇/모델을 호출하고 `RunResult`를 수집
- **Evaluator**
  - RunResult + Dataset을 기반으로 다양한 메트릭(`EvalScore`)을 계산하고 리포트 생성

이 사이트는 위 세 모듈을 **Generator → Runner → Evaluator** 순서로 어떻게 사용하는지, 그리고 Quick Start / CLI / API 레퍼런스를 정리한 정적 문서입니다.

## 빠르게 시작하기

가장 먼저 **Quick Start E2E 예제**를 실행해 보는 것을 추천합니다.

- [Quick Start: end-to-end 예제](usage/quickstart-e2e.md)
- [더 많은 예제 (Multi-turn, Custom Metric)](usage/examples.md)

로컬에서 Quick Start를 돌리면 다음을 한 번에 경험할 수 있습니다.

1. 작은 toy dataset(`toy_support_qa`) 생성 (Generator)
2. OpenAI backend(`gpt-4o-mini` 등)를 사용한 챗봇 실행 (Runner)
3. `exact_match` / `keyword_coverage` 메트릭 평가 및 JSON/Markdown 리포트 생성 (Evaluator)

## 사용 방법 문서

보다 구조적으로 프레임워크를 이해하고 싶다면 다음 문서를 참고하세요.

- [Framework Overview](usage/overview.md)
- [Generator 사용법](usage/generator.md)
- [Runner 사용법](usage/runner.md)
- [Evaluator 사용법](usage/evaluator.md)

## 레퍼런스

- [CLI 레퍼런스](reference/cli.md)
- [API 레퍼런스](reference/api.md) — Core 도메인 모델(`TestSample`, `RunConfig`, `RunResult`, `EvalScore`, `EvaluationReport` 등)을 mkdocstrings로 자동 문서화할 수 있습니다.

## 소스 코드

- GitHub: <https://github.com/mackim-3768/chatbot-tester>
