---
trigger: glob
globs: **/datasets/**, **/generator/**, **/metadata/**
---

이 룰은 데이터셋 버전·메타데이터의 일관성 유지에 집중합니다.

1. 데이터셋은 항상 dataset_id + version 을 명확히 포함해야 함.
2. metadata.json 에 다음 항목이 있는지 확인하도록 조언:
   - 생성 일시
   - generator 코드 버전 또는 commit hash
   - 필터링/샘플링 조건
   - 샘플 수, 언어 구성, 태그 구성
3. 동일 dataset_id인데 version 번호가 증가하지 않은 변경이 있으면 경고를 제안.
4. 외부에서 dataset을 불러올 때 “canonical TestSample 구조”를 유지하도록 유도.
5. 원천 데이터가 바뀌었으면 반드시 version bump 하도록 안내.

데이터셋 관련 코드/문서에서 위 기준을 자동으로 점검하고 조언하십시오.
