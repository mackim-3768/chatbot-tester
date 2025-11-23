# chatbot-tester-evaluator

Chatbot Tester Evaluator 모듈은 Runner가 남긴 `RunResult` 아티팩트와 Generator가 보장한 `TestSample` 스키마를 입력으로 받아, 다중 Metric을 실행하고 일관된 리포트를 생성하는 것을 목표로 한다. 이 디렉터리는 독립 패키지로 배포될 수 있도록 구성되어 있으며, 상위 `chatbot-tester` 빌드 리포지토리에서는 서브모듈 형태로 포함된다.

## 1. Core Domain Model

Evaluator는 항상 공통 도메인 모델을 따른다.

| Entity | 역할 | 비고 |
| --- | --- | --- |
| `TestSampleRecord` | Generator가 생성한 canonical 샘플 | `id`, `messages`, `expected`, `tags`, `metadata.language` 유지 |
| `RunRecord` | Runner가 저장한 실행 결과 | `status`, `response.text`, `latency_ms`, `trace_id`, `backend`, `model` |
| `EvalScore` | Metric의 per-sample 결과 | metric 이름, 값, 세부 정보(detail), tag/language/length bucket 정보 |
| `EvalSummary` | Metric 집계 결과 | mean / std / sample_count 포맷 필수 |
| `EvaluationReport` | 전체 Experiment 보고서 | Experiment metadata, 전체 요약, tag/length/language breakdown, error cases, LLM Judge 정보 섹션 고정 |

> **Dataset Version Rule**: 모든 `DatasetMetadata`는 반드시 `dataset_id`와 `version`을 포함해야 하며, metadata.json에는 생성 일시, generator commit hash, 필터/샘플링 조건, 샘플 수·언어·태그 구성이 들어가야 한다. Evaluator는 입력 메타에서 이 항목이 빠져 있으면 경고를 출력하도록 설계했다.

## 2. 디렉터리 구조

```text
src/chatbot_tester/evaluator/
  ├─ README.md
  ├─ pyproject.toml
  └─ src/
      ├─ __init__.py
      ├─ cli.py
      ├─ config.py
      ├─ domain.py
      ├─ registry.py
      ├─ metrics/
      │   ├─ base.py
      │   ├─ rule_based.py        # (예정)
      │   └─ llm_judge.py         # (예정)
      └─ report/
          ├─ base.py              # (예정)
          ├─ json_reporter.py     # (예정)
          └─ markdown_reporter.py # (예정)
```

- **metrics/**: Metric 플러그인 디렉터리. 모든 Metric은 `Metric` 추상 클래스를 구현하고 registry를 통해 등록된다.
- **registry.py**: Metric 등록/생성과 lifecycle 관리를 담당.
- **orchestrator.py**(예정): `(Dataset × RunResults × Metrics)` 조합을 실행하고, breakdown/aggregate를 계산한다.
- **report/**: Reporters는 JSON/Markdown 양식을 출력하며, 반드시 `Experiment metadata → Overall metrics → Breakdown(tag/length/language) → Error cases → LLM Judge detail` 섹션 구조를 지킨다.
- **cli.py**: `chatbot-eval`/`chatbot-evaluator` CLI. dataset jsonl + metadata + run-results jsonl + evaluator config를 받아 보고서를 생성한다.

## 3. Metric & Evaluator Guidelines

1. **공통 인터페이스**: Metric은 `score()` 메서드로 per-sample 점수를 반환하고, `summarize()` 메서드로 aggregate를 계산한다.
2. **Registry 기반 확장**: `MetricRegistry`를 통해 metric 이름 ↔ 구현체를 등록한다. config-driven 형태를 유지한다.
3. **LLM Judge 관리**: `llm_judge.py`는 prompt_id/version/language/sub_scores를 detail에 남기도록 강제한다. prompt 지침은 Prompt Evaluation Safety Guard 룰을 따른다.
4. **비용 최적화**: Orchestrator는 metrics마다 `requires_reference` 옵션을 확인하여 reference 없는 샘플은 자동 skip하고 경고만 남긴다. LLM Judge metric은 샘플링 비율을 config로 조절 가능하다.
5. **Breakdown**: 기본으로 `tags`, `language`, `length_bucket` 3가지를 제공한다. 필요 시 config에서 dimension을 추가/제거할 수 있다.
6. **Error Isolation**: Runner 오류(`status in {timeout,error}`)는 `ErrorCase` 섹션에서 별도로 요약하며, 전체 평가 파이프라인이 중단되지 않도록 한다.

## 4. CLI 사용 예시

```bash
chatbot-evaluator \
  --dataset ./datasets/support/test.jsonl \
  --metadata ./datasets/support/metadata.json \
  --runs ./runs/openai_support/results.jsonl \
  --config ./configs/eval_config.json \
  --output ./reports/openai_support
```

- `--dataset`: Generator가 만든 canonical JSONL (id/messages/expected/tags 포함)
- `--metadata`: 동일 dataset의 metadata.json (dataset_id/version 명시 필수)
- `--runs`: Runner 결과 JSONL (`RunResult.to_record()` 포맷 권장)
- `--config`: 아래 예시와 같은 evaluator 설정 파일(JSON/YAML)
- `--output`: 결과 report를 저장할 디렉터리. 경로가 없으면 자동 생성한다.

### config 예시

```json
{
  "run_config": {"backend": "openai", "model": "gpt-4o-mini"},
  "metrics": [
    {"type": "exact_match", "name": "exact_match", "parameters": {"normalize_whitespace": true}},
    {"type": "keyword_coverage", "parameters": {"keywords": ["reset", "account"], "language": "ko"}},
    {"type": "llm_judge", "parameters": {"prompt_id": "support_pair", "prompt_version": "v1", "criteria": ["helpfulness", "safety"], "max_score": 5}}
  ],
  "breakdown": {"dimensions": ["tag", "language", "length"]},
  "report": {"formats": ["json", "markdown"]}
}
```

## 5. 보고서 포맷

Reporters는 다음 필드 구성을 항상 유지한다.

1. **Experiment metadata**: dataset id/version/name/source, run_config, evaluator config 요약.
2. **Overall metrics summary**: 테이블 형태(`metric / mean / std / sample_count`).
3. **Breakdown**: tag/length/language 별 metric summary.
4. **Error cases / Low-score samples**: status, trace_id, latency, metric별 최저 점수.
5. **LLM Judge details**: prompt_id/version/language, 평가 기준(criteria), 사용된 metric 이름, sample count, 샘플 id 목록.

## 6. TODO

- Metric plugin 추가(BLEU/ROUGE/BERTScore 등)
- Experiment comparison 리포트
- 캐싱/샘플링 전략 강화
- PyPI 배포 자동화 스크립트