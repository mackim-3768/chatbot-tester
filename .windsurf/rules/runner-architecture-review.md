---
trigger: glob
globs: **/runner/**, **/backends/**, **/chat_runner/**
---

이 룰은 Runner 모듈을 안정적으로 설계하기 위한 가이드입니다.

Runner 관련 파일을 편집할 때 당신은 다음을 점검하며 조언해야 합니다.

1. 모든 백엔드는 ChatBackend 인터페이스(또는 Protocol)를 구현하도록 권장.
2. Adapter 안에 엔드포인트 특수 로직을 캡슐화하고, 외부로는 RunResult만 노출하도록 유도.
3. 요청/응답/latency/status/token 정보는 RunResult에 반드시 남기게 함.
4. Rate limiting, timeout, retry(backoff) 전략 필요 여부를 먼저 검토.
5. 멀티턴 대화라면 ConversationState(history/messages) 구조를 명확히 하도록 도움.
6. Runner는 “(Dataset × Backend × RunConfig) → RunResult 리스트 생산”이라는 최소 단위 Job 모델을 유지하도록 안내.
7. 로깅은 디버깅/재현 가능한 수준으로 충분히 남기도록 조언.

Runner 파일 변경 시 반드시 위 기준을 기반으로 구조적 리뷰를 제공합니다.
