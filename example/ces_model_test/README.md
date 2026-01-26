# CES Model Auto Test (lm-eval-so 예제)

기존 [CES_Model_Auto_Tester](https://github.com/tom-shin/CES_Model_Auto_Tester) 흐름을 `lm-eval-so` 프레임워크로 재구성한 예제입니다.

- **Generate**: CES 시나리오 JSON → canonical dataset(JSONL + metadata)
- **ADB Run**: ADB 디바이스의 CLI 모델(`llm_executable`)에 질문을 던지고 응답 수집
- **Evaluate**: Runner 결과 JSONL을 기반으로 Metric 실행 및 리포트 생성

최상위 엔트리포인트는 [main.py](lm-eval-so/example/ces_model_test/main.py)이며, 세 단계를 순차 실행합니다.

```text
example/ces_model_test/
  ├─ generate/
  │   └─ generate_dataset.py
  ├─ adb_run/
  │   └─ run_on_device.py
  ├─ evaluate/
  │   ├─ eval_config.json
  │   └─ evaluate_results.py
  ├─ datasets/           # generate 단계 출력 (자동 생성)
  ├─ runs/               # adb_run 단계 출력 (자동 생성)
  ├─ reports/            # evaluate 단계 출력 (자동 생성)
  ├─ main.py
  └─ README.md
```

## 1. 선행 조건

1. **ADB 디바이스 연결**
   - `adb devices` 에서 최소 1개 디바이스가 `device` 상태로 떠 있어야 합니다.

2. **디바이스 내 CLI 바이너리 준비**

   - 기본값: `/data/local/tmp/llm_executable`
   - stdin 으로 **JSON** 입력을 받고 stdout 으로 아래 형태의 JSON 을 출력해야 합니다.

   ```json
   {
     "text": "model answer text",
     "usage": {
       "input": 123,
       "output": 456,
       "total": 579
     }
   }
   ```

   - 필요 시 [adb_run/run_on_device.py](lm-eval-so/example/ces_model_test/adb_run/run_on_device.py) 안의 `BACKEND_OPTIONS["binary"]`,
     `MODEL_NAME` 를 실제 환경에 맞게 수정하십시오.

3. **Python 패키지 설치**

   루트에서 개발 모드 설치:

   ```bash
   pip install -e .
   ```

## 2. 단계별 실행

### 2.1 Generate: CES 시나리오 → dataset

입력 시나리오 파일은 기존 프로젝트의 JSON 을 재사용합니다.

- 경로: [CES_Model_Auto_Tester/Scenario/ces_llm_questions_all_categories_100.json](lm-eval-so/CES_Model_Auto_Tester/Scenario/ces_llm_questions_all_categories_100.json)
- 구조: `{ "Category": [ { "English": "...", "Chinese": "..." }, ... ] }`

[generate/generate_dataset.py](lm-eval-so/example/ces_model_test/generate/generate_dataset.py) 는 위 시나리오를 읽어
[lm_eval_so.generator.TestSample](lm-eval-so/src/lm_eval_so/runner/models.py:42:0-72:22) 리스트로 변환하고 다음을 생성합니다.

- `example/ces_model_test/datasets/ces_llm_v1/test.jsonl`
- `example/ces_model_test/datasets/ces_llm_v1/metadata.json`
- `example/ces_model_test/datasets/ces_llm_v1/schema.json`

기본 언어는 `English`(메타데이터 `language = "en"`).  
필요 시 파일 상단의 `LANGUAGE_KEY`, `LANG_CODE` 를 수정할 수 있습니다.

직접 실행 예:

```bash
python example/ces_model_test/generate/generate_dataset.py
```

### 2.2 ADB Run: 디바이스에서 모델 실행

[adb_run/run_on_device.py](lm-eval-so/example/ces_model_test/adb_run/run_on_device.py) 는 다음을 수행합니다.

1. `datasets/ces_llm_v1/test.jsonl` + `metadata.json` 로드
2. `lm_eval_so.runner` 의 `adb-cli` 백엔드로 각 샘플을 디바이스에 전달
3. 결과를 JSONL/메타데이터로 저장

기본 설정 (파일 내 상수):

- `BACKEND_NAME = "adb-cli"`
- `MODEL_NAME = "llm_executable"`
- `BACKEND_OPTIONS["binary"] = "/data/local/tmp/llm_executable"`

출력 파일:

- `example/ces_model_test/runs/adb_cli/run_results.jsonl`
- `example/ces_model_test/runs/adb_cli/run_metadata.json`

실행 예:

```bash
python example/ces_model_test/adb_run/run_on_device.py
```

### 2.3 Evaluate: Metric 실행 및 리포트 생성

[evaluate/evaluate_results.py](lm-eval-so/example/ces_model_test/evaluate/evaluate_results.py) 는 Evaluator 모듈을 사용해 다음을 수행합니다.

1. `datasets/ces_llm_v1/test.jsonl`, `metadata.json` 로드
2. `runs/adb_cli/run_results.jsonl` 로드
3. [evaluate/eval_config.json](lm-eval-so/example/ces_model_test/evaluate/eval_config.json) 의 설정을 기반으로 Metric 실행
4. JSON / Markdown 리포트 생성

기본 [eval_config.json](lm-eval-so/example/ces_model_test/evaluate/eval_config.json) 예시:

```json
{
  "run_config": { "backend": "adb-cli", "model": "llm_executable" },
  "metrics": [
    {
      "type": "keyword_coverage",
      "name": "keyword_coverage_simple",
      "parameters": { "keywords": ["test"] }
    }
  ],
  "breakdown": { "dimensions": ["language", "tag"] },
  "report": { "formats": ["json", "markdown"] }
}
```

출력 파일:

- `example/ces_model_test/reports/adb_cli/summary.json`
- `example/ces_model_test/reports/adb_cli/scores.jsonl`
- `example/ces_model_test/reports/adb_cli/report.md`

실행 예:

```bash
python example/ces_model_test/evaluate/evaluate_results.py
```

## 3. main.py 한 번에 실행

위 세 단계를 한 번에 실행하려면:

```bash
python example/ces_model_test/main.py
```

순서대로 다음을 수행합니다.

1. `[1/3] Generating dataset...` → generate 단계
2. `[2/3] Running dataset on ADB device (adb-cli backend)...` → adb_run 단계
3. `[3/3] Evaluating run results...` → evaluate 단계

각 단계에서 생성된 디렉터리/파일 경로는 표준 출력으로 함께 표시됩니다.