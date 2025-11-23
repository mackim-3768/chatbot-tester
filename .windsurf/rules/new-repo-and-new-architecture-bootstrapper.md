---
trigger: model_decision
description: 이 룰은 “새로운 Repo/신규 서비스/새 아키텍처 설계 요청” 발생 시 자동으로 개입합니다.
---

이 룰은 “새로운 Repo/신규 서비스/새 아키텍처 설계 요청” 발생 시 자동으로 개입합니다.

사용자가 다음과 같은 요청을 하면:
- “새로운 repo 구조 만들어줘”
- “새 테스트 프레임워크 설계해줘”
- “이 서비스 아키텍처 잡아줘”

다음 원칙을 기반으로 아키텍처를 부트스트랩합니다.

1. 가능한 경우 Generator / Runner / Evaluator / Core 구조로 자동 매핑을 제안.
2. Task-agnostic core 모델을 먼저 정의하게 유도.
3. Adapter/Plugin 기반으로 확장 가능하도록 유도.
4. config-driven 방식(예: YAML/JSON 기반)으로 Pipeline/Scheduler/Metric을 조정하도록 안내.
5. 디렉터리/패키지 초안을 생성할 때 “core / generator / runner / evaluator / cli / docs” 구조로 제안.
6. 이 아키텍처를 사용할 수 없는 경우, 그 이유와 대안 구조를 분명히 설명.

요약: 새로운 설계 요청 상황에서, Chatbot Test Framework의 원칙을 다시 적용하여 안정적이고 확장 가능한 구조를 구성하도록 돕습니다.
