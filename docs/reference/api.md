# API 레퍼런스 (개요)

이 문서는 `chatbot-tester`의 핵심 Python API를 자동 문서화하기 위한 진입점입니다.
mkdocstrings 플러그인을 활용하면, 아래와 같이 모듈/클래스에 대한 상세 문서를 생성할 수 있습니다.

> 실제 mkdocstrings 블록은 프로젝트 상황에 맞게 조정하면 됩니다.

## Core 도메인 모델

예시:

```markdown
::: chatbot_tester.evaluator.domain.TestSampleRecord

::: chatbot_tester.evaluator.domain.RunRecord

::: chatbot_tester.evaluator.domain.EvalScore

::: chatbot_tester.evaluator.domain.EvaluationResult

::: chatbot_tester.evaluator.domain.EvaluationReport
```

## Runner 모델

```markdown
::: chatbot_tester.runner.models.TestSample

::: chatbot_tester.runner.models.RunConfig

::: chatbot_tester.runner.models.RunResult
```

## Generator 타입

```markdown
::: chatbot_tester.generator.types.TestSample
```

위와 같은 mkdocstrings 지시문을 사용하면, `mkdocs build` 시점에 docstring/타입 정보를 기반으로 API 문서가 자동 생성됩니다.

프로젝트에 맞게 포함할 모델/함수/클래스를 선별해서 추가해 주세요.
