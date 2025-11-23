# OpenAI Generator Example

이 예시는 OpenAI API를 사용해 소량의 지원(고객센터) QA 데이터를 생성하고, 
`chatbot-tester.generator` 패키지의 스키마에 맞는 정규화된 DataSet으로 저장하는 방법을 보여준다.

## 구성

```
example/generate/openai/

  README.md
  generate_dataset.py   # OpenAI를 호출해 정규화된 데이터셋 생성
  outputs/              # 생성된 데이터셋 출력 디렉터리(스크립트 실행 후 생성)
```

## 사전 준비

1. 가상환경 활성화 (선택)
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. generator 패키지 설치 (루트에서 실행)
   ```bash
   pip install -e src/chatbot_tester/generator
   ```

3. OpenAI Python 패키지 설치
   ```bash
   pip install "openai>=1.0.0"
   ```

4. OpenAI 관련 환경 변수 설정

   최소 필요:
   ```bash
   export OPENAI_API_KEY="sk-..."  # 절대 코드/리포에 직접 커밋하지 말 것
   ```

   선택 사항:
   ```bash
   export OPENAI_MODEL="gpt-4o-mini"   # 기본값: gpt-4o-mini
   export OPENAI_BASE_URL="https://api.openai.com/v1"  # 프록시/커스텀 엔드포인트 사용 시
   ```

## 실행 방법

루트 디렉터리(`chatbot-tester`)에서 다음을 실행:

```bash
python example/generate/openai/generate_dataset.py
```

실행이 완료되면 아래 위치에 데이터셋이 생성된다.

```
example/generate/openai/outputs/openai_support_v1/
  test.jsonl      # canonical TestSample 구조의 샘플들
  metadata.json   # dataset_id/name/version/created_at/태그·언어 통계 등
  schema.json     # 샘플 JSON Schema
```

생성된 `test.jsonl`은 Runner/Evaluator에서 바로 소비할 수 있는 정규화된 데이터셋 예시로 사용할 수 있다.

