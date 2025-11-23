# chatbot-tester.generator

어떤 Agent/AI/Client를 사용하더라도 공통 포맷의 챗봇 테스트 DataSet을 생성·변환하는 도구이다. 생성된 DataSet은 상위 프레임워크의 Runner/Evaluator가 그대로 소비할 수 있도록 정규화된다.

## 핵심 목적

- **Provider-agnostic 정규화**  
  다양한 에이전트/모델/클라이언트로부터 온 데이터를 한 가지 공통 스키마로 통일한다.
- **Schema-first, 쉬운 커스터마이징**  
  기본 스키마를 제공하되, 사용자 정의 필드/구조 확장이 쉽다.
- **연결 용이성**  
  어떤 Agent/AI/Client(로그, API, 파일, DB 등)와도 간단히 연결할 수 있도록 어댑터 구조를 제공한다.

## 산출물(Outputs)

기본 출력은 JSON Lines(JSONL)이며, 한 줄이 하나의 샘플을 나타낸다.

```
datasets/
  <dataset_name>/
    schema.json      # JSON Schema: 샘플/메타 구조 정의
    metadata.json    # 데이터셋 수준 메타정보(name, version, source 등)
    train.jsonl      # 학습/평가용 샘플(선택)
    test.jsonl       # 평가용 샘플(선택)
```

추가 포맷(CSV/Parquet/SQLite 등)은 Exporter 확장을 통해 지원한다.

## 기본 스키마 개요(Schema Overview)

- 샘플 필수 필드
  - `id`: string, 샘플 식별자
  - `messages`: array<object>
    - `role`: "system" | "user" | "assistant" | "tool" | "function"
    - `content`: string
    - `name`/`metadata`: optional
  - `expected`: string | object | array, optional(참고 정답/레퍼런스/평가기준)
  - `tags`: array<string>, optional
  - `metadata`: object, optional(출처, 난이도, 도메인 등)

- 데이터셋 메타
  - `dataset_id`, `name`, `version`, `created_at`, `source` 등

이 스키마는 Runner/Evaluator가 바로 사용할 수 있도록 최소 공통 필드를 보장하면서, 사용자 정의 필드 추가를 허용한다.

## 확장 포인트(Extensibility)

- **Source Adapter**: 로그/파일/DB/API/LLM 등 다양한 원천으로부터 데이터를 불러와 정규화  
- **Transformer**: 필터링, 클린징, 증강, 디듀플리케이션 등 파이프라인 처리  
- **Exporter**: JSONL/CSV/Parquet/SQLite 등 다양한 출력 포맷 지원  
- **Schema Extender**: 기본 스키마에 사용자 정의 필드/구조를 손쉽게 추가

## Runner/Evaluator 연동 최소 요구

- `id`, `messages[]`, `expected(optional)` 필드 제공  
- `messages` 항목은 역할/내용이 명확하며 순서가 보존되어야 한다.  
- 샘플 단위로 재현 가능한 입력이 보장되어야 한다.

## 사용 시나리오 예시

- 기존 대화 로그 수집 → 정규화된 DataSet으로 변환  
- 프롬프트 템플릿/규칙에 따라 대량 샘플 생성  
- (선택) LLM/룰 기반 합성 데이터 생성 후 스키마에 맞게 저장

## 추가 문서

- `schema.md`: 상세 스키마와 validation 규칙  
- `adapters.md`: Source Adapter/Exporter 가이드  
- `examples/`: 예시 데이터셋과 템플릿