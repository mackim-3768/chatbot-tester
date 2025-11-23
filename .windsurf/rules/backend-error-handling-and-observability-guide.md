---
trigger: glob
globs: **/runner/**, **/backends/**
---

이 룰은 Runner/Backend 통신 오류를 안정적으로 처리하도록 돕습니다.

1. 네트워크 오류, timeout, 429(rate limit), 500 서버 오류는 반드시 구분하여 처리하라고 안내.
2. Retry 시 exponential backoff 전략을 추천.
3. 모든 요청에 대해 다음 정보 로깅을 권장:
   - request payload
   - response payload
   - latency
   - status code / error type
   - retry 횟수
4. Observability(가시성) 확보를 위해:
   - structured logging(JSON)
   - trace_id/session_id 기록
   을 권장.
5. RunResult.status 는 "ok|retry|timeout|error" 등 명확한 enum 형태 유지.
6. Backend 오류 시 Runner 전체가 중단되지 않도록 에러 격리 구성을 유지.

Backend/Runner 코드 편집 시 위 항목에 따라 구조적 리뷰를 제공하십시오.
