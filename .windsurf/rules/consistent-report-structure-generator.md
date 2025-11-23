---
trigger: always_on
---

이 룰은 평가 보고서 구조를 일관되게 유지하도록 돕습니다.

1. Report 는 반드시 다음 섹션 구조를 유지하도록 권장:
   - Experiment metadata (dataset, model, run_config 요약)
   - Overall metrics summary
   - Breakdown (by tag, length, language)
   - Error cases / Low-score samples
   - LLM Judge 세부 정보(prompt_id/version)
2. Markdown/HTML/JSON 중 어떤 형식이든 동일한 필드 구성 유지.
3. 점수 테이블은 “metric name / mean / std / sample_count” 형식으로 표현하도록 추천.
4. 잘못된 출력/비정상 응답은 별도 오류 섹션으로 분리하도록 안내.
5. 여러 모델 비교 시 모델 이름/버전/설정이 헷갈리지 않도록 보고서 상단에 비교표 생성 권장.

리포트 관련 문서나 코드를 작성할 때 위 기준에 따라 자동으로 조언하십시오.
