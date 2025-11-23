---
trigger: glob
globs: **/evaluator/**, **/metrics/**, **/report/**
---

이 룰은 Evaluator 및 Metric 구현 시 일관성과 확장성을 유지하기 위한 규칙입니다.

Evaluator 관련 파일을 다룰 때 다음을 기준으로 조언합니다.

1. 모든 Metric/Evaluator는 공통 인터페이스를 따르도록 유도.
2. per-sample score 와 aggregate score 를 분리해서 계산하도록 권장.
3. metric registry(등록 구조)를 활용하도록 조언.
4. LLM Judge 사용 시 prompt_id/version/language/sub_scores 필드 기록 여부 확인.
5. Task type(번역/요약/문체변환/QA)에 따른 metric 구성 가이드를 제공.
6. Experiment(실험) 단위로 평가 결과를 묶고, Report 구조(JSON/Markdown)로 출력하도록 권장.
7. 비용·성능 최적화를 위해 캐싱 또는 부분 샘플 평가 전략도 함께 제안.

Evaluator 파일 변경 시 위 기준을 따라 구조적으로 리뷰합니다.
