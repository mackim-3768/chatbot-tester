# Quick Start: End-to-End 예제

이 문서는 `example/quickstart/` 디렉터리에 있는 **toy_support_qa** 예제를 기반으로,
Generator → Runner → Evaluator 전체 플로우를 한 번에 실행하는 방법을 정리합니다.

## 1. 사전 준비

### 1.1 의존성 설치

```bash
python -m pip install -r requirements.txt
```

### 1.2 OpenAI API 키 설정

```bash
export OPENAI_API_KEY="sk-..."
export QUICKSTART_MODEL="gpt-4o-mini"  # 선택, 생략 시 기본 gpt-4o-mini
```

## 2. 한 번에 실행 (run_quickstart.sh)

아래 스크립트는 Generator → Runner → Evaluator를 순서대로 실행합니다.

```bash
bash example/quickstart/run_quickstart.sh
```

내부 단계는 대략 다음과 같습니다.

1. **Generator**
   - 입력: `example/quickstart/data/toy_support_qa.csv`
   - 출력: `example/quickstart/dataset/toy_support_qa_v1/`
     - `test.jsonl`
     - `metadata.json`
     - `schema.json`
2. **Runner** (OpenAI backend)
   - Dataset: `toy_support_qa_v1`
   - Backend: `openai`
   - Model: `QUICKSTART_MODEL` (기본: `gpt-4o-mini`)
   - 출력: `example/quickstart/runs/openai_<model>/run_results.jsonl`, `run_metadata.json`
3. **Evaluator**
   - Dataset + RunResult + 설정(`eval_toy.yaml`)을 사용해
   - `exact_match` / `keyword_coverage` 메트릭 평가 수행
   - 출력: `example/quickstart/reports/` 아래 JSON/Markdown 리포트

성공 시 대략 다음과 같은 로그를 볼 수 있습니다.

```text
[quickstart] 1/3: Generating canonical dataset...
/home/.../example/quickstart/dataset/toy_support_qa_v1
[quickstart] 2/3: Running Runner against OpenAI backend...
INFO:chatbot_tester.runner:Starting run: dataset=toy_support_qa backend=openai model=gpt-4o-mini samples=3
...
[quickstart] 3/3: Evaluating run results...
/home/.../example/quickstart/reports/summary.json
/home/.../example/quickstart/reports/scores.jsonl
/home/.../example/quickstart/reports/report.md
[quickstart] Done. Reports written under example/quickstart/reports
```

## 3. 생성되는 파일 구조

실행 후 Quick Start 관련 디렉터리 구조는 대략 다음과 같습니다.

```text
example/quickstart/
  data/
    toy_support_qa.csv
  dataset/
    toy_support_qa_v1/
      test.jsonl
      metadata.json
      schema.json
  runs/
    openai_gpt-4o-mini/   # QUICKSTART_MODEL에 따라 디렉터리 이름이 달라질 수 있음
      run_results.jsonl
      run_metadata.json
  config/
    eval_toy.yaml
  reports/
    summary.json
    scores.jsonl
    report.md
  run_quickstart.sh
```

## 4. 리포트 해석하기

`example/quickstart/reports/report.md` 는 사람이 읽기 좋은 Markdown 리포트입니다.

일반적으로 다음 내용을 포함합니다.

- Experiment metadata
  - dataset 정보 (id/name/version, sample_count 등)
  - run_config (backend, model, 파라미터)
  - evaluator_config (metrics/breakdown/report 설정)
- Metrics summary
  - `exact_match`, `keyword_coverage` 등 metric별 mean/std/sample_count
- Breakdown
  - tag / language / length 기준 metric 분포
- Error cases
  - status가 ok가 아닌 RunResult들의 요약 (Quick Start 예제에서는 대부분 ok)

이를 시작점으로 삼아, 더 큰 Dataset/다양한 Backend/Metric 조합으로 확장해 나갈 수 있습니다.
