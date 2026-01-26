# CSV Generator Example

이 예시는 `lm-eval-so.generate` 패키지를 사용해 CSV 데이터를 정규화된 테스트 데이터셋으로 만드는 방법을 보여준다.

## 구성

```
example/generate/csv/
  README.md              # 이 문서
  data/sample.csv        # 예제 원천 데이터
  scripts/run_example.sh # 예제 실행 스크립트
  outputs/               # 생성된 데이터셋 출력 디렉터리(스크립트 실행 후 생성)
```

### sample.csv
열 정의:
- `id`: 샘플 ID
- `system`: 시스템 프롬프트
- `user`: 사용자 질문
- `expected`: 기대 답변
- `tags`: 태그 목록("|" 구분)
- `lang`: 언어 정보

## 실행 방법

1. (루트에서) generator 패키지를 설치하거나 editable 설치:
   ```bash
   pip install -e src/lm_eval_so/generator
   ```

2. 예제 실행:
   ```bash
   cd example/generate/csv
   bash scripts/run_example.sh
   ```

3. 결과 확인:
   - `outputs/support_qa_v1/test.jsonl`
   - `outputs/support_qa_v1/metadata.json`
   - `outputs/support_qa_v1/schema.json`

metadata.json에는 dataset_id/name/version/created_at/generator_version/generator_code_commit/필터/샘플링/태그·언어 통계가 기록된다.
