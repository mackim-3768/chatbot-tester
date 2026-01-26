---
trigger: glob
globs: **/core/**, **/lm_eval_so_core/**
---

이 룰은 Core Domain Model을 일관성 있게 유지하기 위한 규칙입니다.

당신은 Core 영역을 편집할 때 다음 원칙을 따르도록 조언합니다.

1. TestSample / TestCase / RunConfig / RunResult / EvalScore 의 정의를 임의로 변경하지 말 것.
2. 필드 추가 시 “이 속성이 core 공통인가? task-specific인가?”를 먼저 판단하도록 안내.
3. task-specific 정보는 payload 또는 meta 안에 넣고, core에는 넣지 않도록 권장.
4. Core 변경이 Runner/Evaluator/Generator 전체에 영향을 미치는지 반드시 검토하도록 유도.
5. TestSample/TestCase는 Canonical Format 유지.
6. RunResult는 요청/응답/latency/status/error를 반드시 포함.

Core 파일을 편집할 때 위 원칙을 기반으로 구조적 조언을 수행하십시오.
