# 테스트 설계 베스트 프랙티스

이 문서는 `lm-eval-so`로 **좋은 테스트셋/실험을 설계하는 방법**을 정리합니다.

- 태그/길이/언어 분포 설계
- dataset 버전 관리 원칙
- 샘플링 전략
- multi-model 비교 실험 설계 팁

---

## 1. 태그 / 길이 / 언어 분포 설계

### 1.1 태그(Tag)

태그는 나중에 **breakdown** 과 분석의 기준이 됩니다.

권장 패턴:

- 역할별 태그
  - 예: `task:translation`, `task:summary`, `task:faq`
- 도메인별 태그
  - 예: `domain:billing`, `domain:account`, `domain:search`
- 난이도/유형 태그
  - 예: `difficulty:easy/medium/hard`, `style:formal/casual`

설계 팁:

- **한 샘플에 여러 태그 허용** (Multi-label)
- Evaluator의 breakdown.dimensions 에 `"tag"` 를 넣어두면 태그 별 성능을 바로 볼 수 있음
- 태그 수는 너무 많지 않게(10~30 범위) 관리하는 것이 리포트 가독성에 좋음

### 1.2 길이(Length)

코드에서는 `length_bucket` 을 `short` / `medium` / `long` 으로 자동 추론합니다.

- 기본 기준 (예시 구현)
  - `short`: content 길이 < 200
  - `medium`: 200 <= length < 600
  - `long`: 600 이상

설계 팁:

- 테스트셋 전체가 short에만 몰리지 않게, 최소한 short/medium/long 이 모두 일정 비율 나오도록 구성
- 길이에 따라 모델 성능이 달라지는 경우가 많으므로 breakdown에 `length` 를 항상 포함하는 것을 추천

### 1.3 언어(Language)

멀티 언어를 다룰 경우:

- `metadata.language` 필드에 ISO 코드(`"ko"`, `"en"`, `"ja"` 등)를 넣고
- Evaluator에서 breakdown.dimensions 에 `"language"` 를 추가

설계 팁:

- 한 언어만 테스트해도, 나중을 위해 language 메타데이터는 미리 넣어두는 것이 좋음
- 다국어 테스트의 경우, 언어별 샘플 수가 너무 불균형하지 않게 설계 (예: ko/en 각각 최소 N개 이상)

---

## 2. Dataset 버전 관리

Dataset는 **재현 가능성**을 위해 `dataset_id` + `version` 조합으로 관리해야 합니다.

권장 원칙:

- `dataset_id`
  - 논리적으로 동일한 테스트셋 계열에 공통으로 사용
  - 예: `toy_support_qa`, `news_summary_kr`
- `version`
  - 샘플 집합/전처리/샘플링 전략이 바뀔 때마다 증가 (`v1`, `v2`, `v3` ...)

반드시 버전 올려야 하는 변경 예:

- 원천 데이터(행/열)가 바뀐 경우
- 전처리/필터/샘플링 로직이 바뀌어 **어떤 샘플이 포함되는지** 달라진 경우
- 태그/언어 필드 정의가 크게 변경된 경우

버전 유지 가능한 변경 예 (상황에 따라 다름):

- metadata.json 에 설명 필드 추가, tag_stats를 더 자세히 쓰는 정도

실무에서는 **조금만 애매해도 version을 올리는 쪽이 안전**합니다.

---

## 3. 샘플링 전략

대규모 원천 데이터에서 테스트셋을 추출할 때는 **샘플링 전략**이 중요합니다.

### 3.1 랜덤 샘플링

- 가장 단순한 방법: 전체 코퍼스에서 무작위로 N개 추출
- 장점: 구현이 쉽고, bias를 어느 정도 상쇄
- 단점: 특정 케이스(긴 문장, 희귀 태그)가 충분히 포함되지 않을 수 있음

### 3.2 계층적(Stratified) 샘플링

- 태그/언어/길이 등을 기준으로 **층(stratum)** 을 나눈 뒤, 각 층별로 N개씩 샘플링
- 예:
  - `language in {ko, en}` × `length_bucket in {short, medium, long}` 조합별로 최소 10개씩 추출
- 장점: breakdown 관점에서 통계가 안정됨

### 3.3 집중 샘플링 (Edge-case Focus)

- 모델이 약한 영역에 집중한 테스트셋을 따로 만드는 전략
- 예:
  - `long` + `domain:billing` + `difficulty:hard` 조합만 모은 stress test

설계 팁:

- **하나의 거대한 테스트셋** 만들기보다는, 목적이 다른 소규모 테스트셋 여러 개를 만들고
- 실험 단위(Experiment)에서 어떤 테스트셋을 사용할지 조합하는 방식이 관리에 유리합니다.

---

## 4. Multi-model 비교 실험 설계

여러 모델/설정을 비교하려면 **실험 단위(Experiment)** 를 먼저 정의해야 합니다.

### 4.1 Experiment 단위 정의

`Experiment = Dataset × Backend × RunConfig × EvaluatorConfig`

- Dataset: 어떤 test.jsonl/metadata.json 조합을 썼는지
- Backend: `openai`, `http`, `local-llm` 등
- RunConfig: 모델 이름, decoding 설정 등
- EvaluatorConfig: metric/breakdown/report 설정

Report에는 Experiment 단위가 명확히 드러나야 합니다.

### 4.2 고정해야 하는 것들

공정한 비교를 위해 **다음은 고정**하는 것이 좋습니다.

- Dataset (동일한 샘플 집합)
- EvaluatorConfig (동일한 metric/breakdown 설정)

변경되는 것:

- Backend/모델 (`model: gpt-4o-mini` vs `model: gpt-4.1` 등)
- RunConfig 파라미터 (temperature 등)

### 4.3 Report 기반 비교

여러 Experiment의 `summary.json`/`report.md`를 모아 상위 레벨 리포트를 만들 때는:

- 공통 테이블 키
  - `metric`, `mean`, `std`, `sample_count`
  - `model_id` 또는 `backend:model`
- 추가 메타데이터
  - `dataset_id`, `dataset_version`
  - `prompt_id/prompt_version` (LLM Judge를 쓴 경우)

이 정보가 명확하면, 나중에 pandas/노트북으로 손쉽게 교차 분석할 수 있습니다.

---

## 5. 요약

- 태그/길이/언어 메타데이터를 잘 설계해 두면, breakdown 리포트의 해석력이 크게 올라갑니다.
- Dataset는 `dataset_id` + `version` 조합으로 재현 가능하게 관리해야 합니다.
- 샘플링은 **랜덤 + 계층적 + edge-case 전용 세트**를 혼합하는 전략을 권장합니다.
- Multi-model 비교 실험에서는 Experiment 단위와 Report 스키마를 일관되게 유지하는 것이 중요합니다.
