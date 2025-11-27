# Experiment metadata

- dataset_id: `ces_llm`
- name: `CES topic-based multilingual dataset`
- version: `v1`
- source: `{'type': 'ces_topics', 'topics': ['번역', '문체 변환', '요약']}`

## Overall metrics summary

| metric | mean | std | sample_count |
| --- | ---: | ---: | ---: |
| keyword_coverage_simple (0-1) | 0.0000 | 0.0000 | 60 |
| topic_alignment (0-1) | 0.4833 | 0.4443 | 60 |
| language_match (0-1) | 0.8167 | 0.3869 | 60 |
| context_naturalness (0-1) | 0.4833 | 0.4417 | 60 |
| answer_accuracy (0-1) | 0.3000 | 0.4070 | 60 |
| naturalness (0-1) | 0.3883 | 0.4231 | 60 |
| coherence (0-1) | 0.3933 | 0.4238 | 60 |
| engagingness (0-1) | 0.3133 | 0.3748 | 60 |
| groundedness (0-1) | 0.3333 | 0.4122 | 60 |

## Breakdown

### tag

| metric | bucket | mean | std | sample_count |
| --- | --- | ---: | ---: | ---: |
| keyword_coverage_simple (0-1) | 번역 | 0.0000 | 0.0000 | 20 |
| keyword_coverage_simple (0-1) | lang:ko | 0.0000 | 0.0000 | 15 |
| keyword_coverage_simple (0-1) | scenario:everyday_life | 0.0000 | 0.0000 | 36 |
| keyword_coverage_simple (0-1) | scenario:business | 0.0000 | 0.0000 | 24 |
| keyword_coverage_simple (0-1) | lang:zh | 0.0000 | 0.0000 | 15 |
| keyword_coverage_simple (0-1) | lang:ja | 0.0000 | 0.0000 | 15 |
| keyword_coverage_simple (0-1) | lang:en | 0.0000 | 0.0000 | 15 |
| keyword_coverage_simple (0-1) | 문체 변환 | 0.0000 | 0.0000 | 20 |
| keyword_coverage_simple (0-1) | 요약 | 0.0000 | 0.0000 | 20 |
| topic_alignment (0-1) | 번역 | 0.5800 | 0.4729 | 20 |
| topic_alignment (0-1) | lang:ko | 0.7200 | 0.4183 | 15 |
| topic_alignment (0-1) | scenario:everyday_life | 0.5222 | 0.4547 | 36 |
| topic_alignment (0-1) | scenario:business | 0.4250 | 0.4216 | 24 |
| topic_alignment (0-1) | lang:zh | 0.5400 | 0.4030 | 15 |
| topic_alignment (0-1) | lang:ja | 0.4667 | 0.4541 | 15 |
| topic_alignment (0-1) | lang:en | 0.2067 | 0.3316 | 15 |
| topic_alignment (0-1) | 문체 변환 | 0.3150 | 0.3940 | 20 |
| topic_alignment (0-1) | 요약 | 0.5550 | 0.4129 | 20 |
| language_match (0-1) | 번역 | 0.5000 | 0.5000 | 20 |
| language_match (0-1) | lang:ko | 0.8667 | 0.3399 | 15 |
| language_match (0-1) | scenario:everyday_life | 0.8611 | 0.3458 | 36 |
| language_match (0-1) | scenario:business | 0.7500 | 0.4330 | 24 |
| language_match (0-1) | lang:zh | 0.7333 | 0.4422 | 15 |
| language_match (0-1) | lang:ja | 0.7333 | 0.4422 | 15 |
| language_match (0-1) | lang:en | 0.9333 | 0.2494 | 15 |
| language_match (0-1) | 문체 변환 | 0.9500 | 0.2179 | 20 |
| language_match (0-1) | 요약 | 1.0000 | 0.0000 | 20 |
| context_naturalness (0-1) | 번역 | 0.5900 | 0.4711 | 20 |
| context_naturalness (0-1) | lang:ko | 0.7200 | 0.4183 | 15 |
| context_naturalness (0-1) | scenario:everyday_life | 0.5167 | 0.4506 | 36 |
| context_naturalness (0-1) | scenario:business | 0.4333 | 0.4230 | 24 |
| context_naturalness (0-1) | lang:zh | 0.5333 | 0.3978 | 15 |
| context_naturalness (0-1) | lang:ja | 0.4800 | 0.4549 | 15 |
| context_naturalness (0-1) | lang:en | 0.2000 | 0.3183 | 15 |
| context_naturalness (0-1) | 문체 변환 | 0.3100 | 0.3872 | 20 |
| context_naturalness (0-1) | 요약 | 0.5500 | 0.4093 | 20 |
| answer_accuracy (0-1) | 번역 | 0.3100 | 0.4538 | 20 |
| answer_accuracy (0-1) | lang:ko | 0.2933 | 0.4374 | 15 |
| answer_accuracy (0-1) | scenario:everyday_life | 0.3917 | 0.4499 | 36 |
| answer_accuracy (0-1) | scenario:business | 0.1625 | 0.2811 | 24 |
| answer_accuracy (0-1) | lang:zh | 0.4200 | 0.3970 | 15 |
| answer_accuracy (0-1) | lang:ja | 0.3067 | 0.4250 | 15 |
| answer_accuracy (0-1) | lang:en | 0.1800 | 0.3229 | 15 |
| answer_accuracy (0-1) | 문체 변환 | 0.3000 | 0.3912 | 20 |
| answer_accuracy (0-1) | 요약 | 0.2900 | 0.3713 | 20 |
| naturalness (0-1) | 번역 | 0.3200 | 0.4534 | 20 |
| naturalness (0-1) | lang:ko | 0.4733 | 0.4683 | 15 |
| naturalness (0-1) | scenario:everyday_life | 0.4528 | 0.4456 | 36 |
| naturalness (0-1) | scenario:business | 0.2917 | 0.3662 | 24 |
| naturalness (0-1) | lang:zh | 0.4667 | 0.4093 | 15 |
| naturalness (0-1) | lang:ja | 0.3600 | 0.4208 | 15 |
| naturalness (0-1) | lang:en | 0.2533 | 0.3462 | 15 |
| naturalness (0-1) | 문체 변환 | 0.3350 | 0.3772 | 20 |
| naturalness (0-1) | 요약 | 0.5100 | 0.4085 | 20 |
| coherence (0-1) | 번역 | 0.3400 | 0.4521 | 20 |
| coherence (0-1) | lang:ko | 0.4667 | 0.4657 | 15 |
| coherence (0-1) | scenario:everyday_life | 0.4556 | 0.4481 | 36 |
| coherence (0-1) | scenario:business | 0.3000 | 0.3651 | 24 |
| coherence (0-1) | lang:zh | 0.4867 | 0.4047 | 15 |
| coherence (0-1) | lang:ja | 0.3733 | 0.4250 | 15 |
| coherence (0-1) | lang:en | 0.2467 | 0.3481 | 15 |
| coherence (0-1) | 문체 변환 | 0.3350 | 0.3877 | 20 |
| coherence (0-1) | 요약 | 0.5050 | 0.4068 | 20 |
| engagingness (0-1) | 번역 | 0.2900 | 0.4122 | 20 |
| engagingness (0-1) | lang:ko | 0.3467 | 0.4287 | 15 |
| engagingness (0-1) | scenario:everyday_life | 0.4000 | 0.4110 | 36 |
| engagingness (0-1) | scenario:business | 0.1833 | 0.2640 | 24 |
| engagingness (0-1) | lang:zh | 0.4000 | 0.3502 | 15 |
| engagingness (0-1) | lang:ja | 0.3067 | 0.3855 | 15 |
| engagingness (0-1) | lang:en | 0.2000 | 0.2921 | 15 |
| engagingness (0-1) | 문체 변환 | 0.3100 | 0.3713 | 20 |
| engagingness (0-1) | 요약 | 0.3400 | 0.3353 | 20 |
| groundedness (0-1) | 번역 | 0.3400 | 0.4521 | 20 |
| groundedness (0-1) | lang:ko | 0.3200 | 0.4370 | 15 |
| groundedness (0-1) | scenario:everyday_life | 0.4056 | 0.4453 | 36 |
| groundedness (0-1) | scenario:business | 0.2250 | 0.3282 | 24 |
| groundedness (0-1) | lang:zh | 0.4733 | 0.4041 | 15 |
| groundedness (0-1) | lang:ja | 0.3467 | 0.4287 | 15 |
| groundedness (0-1) | lang:en | 0.1933 | 0.3193 | 15 |
| groundedness (0-1) | 문체 변환 | 0.3150 | 0.3940 | 20 |
| groundedness (0-1) | 요약 | 0.3450 | 0.3866 | 20 |

### language

| metric | bucket | mean | std | sample_count |
| --- | --- | ---: | ---: | ---: |
| keyword_coverage_simple (0-1) | ko | 0.0000 | 0.0000 | 15 |
| keyword_coverage_simple (0-1) | zh | 0.0000 | 0.0000 | 15 |
| keyword_coverage_simple (0-1) | ja | 0.0000 | 0.0000 | 15 |
| keyword_coverage_simple (0-1) | en | 0.0000 | 0.0000 | 15 |
| topic_alignment (0-1) | ko | 0.7200 | 0.4183 | 15 |
| topic_alignment (0-1) | zh | 0.5400 | 0.4030 | 15 |
| topic_alignment (0-1) | ja | 0.4667 | 0.4541 | 15 |
| topic_alignment (0-1) | en | 0.2067 | 0.3316 | 15 |
| language_match (0-1) | ko | 0.8667 | 0.3399 | 15 |
| language_match (0-1) | zh | 0.7333 | 0.4422 | 15 |
| language_match (0-1) | ja | 0.7333 | 0.4422 | 15 |
| language_match (0-1) | en | 0.9333 | 0.2494 | 15 |
| context_naturalness (0-1) | ko | 0.7200 | 0.4183 | 15 |
| context_naturalness (0-1) | zh | 0.5333 | 0.3978 | 15 |
| context_naturalness (0-1) | ja | 0.4800 | 0.4549 | 15 |
| context_naturalness (0-1) | en | 0.2000 | 0.3183 | 15 |
| answer_accuracy (0-1) | ko | 0.2933 | 0.4374 | 15 |
| answer_accuracy (0-1) | zh | 0.4200 | 0.3970 | 15 |
| answer_accuracy (0-1) | ja | 0.3067 | 0.4250 | 15 |
| answer_accuracy (0-1) | en | 0.1800 | 0.3229 | 15 |
| naturalness (0-1) | ko | 0.4733 | 0.4683 | 15 |
| naturalness (0-1) | zh | 0.4667 | 0.4093 | 15 |
| naturalness (0-1) | ja | 0.3600 | 0.4208 | 15 |
| naturalness (0-1) | en | 0.2533 | 0.3462 | 15 |
| coherence (0-1) | ko | 0.4667 | 0.4657 | 15 |
| coherence (0-1) | zh | 0.4867 | 0.4047 | 15 |
| coherence (0-1) | ja | 0.3733 | 0.4250 | 15 |
| coherence (0-1) | en | 0.2467 | 0.3481 | 15 |
| engagingness (0-1) | ko | 0.3467 | 0.4287 | 15 |
| engagingness (0-1) | zh | 0.4000 | 0.3502 | 15 |
| engagingness (0-1) | ja | 0.3067 | 0.3855 | 15 |
| engagingness (0-1) | en | 0.2000 | 0.2921 | 15 |
| groundedness (0-1) | ko | 0.3200 | 0.4370 | 15 |
| groundedness (0-1) | zh | 0.4733 | 0.4041 | 15 |
| groundedness (0-1) | ja | 0.3467 | 0.4287 | 15 |
| groundedness (0-1) | en | 0.1933 | 0.3193 | 15 |

## Error cases / Low-score samples

(no error cases)

## LLM Judge details

- metric: `topic_alignment`
  - prompt_id: `overall_eval_v1` version: `1` language: `None`
  - criteria: topic_alignment
  - sample_count: 60
- metric: `language_match`
  - prompt_id: `overall_eval_v1` version: `1` language: `None`
  - criteria: language_match
  - sample_count: 60
- metric: `context_naturalness`
  - prompt_id: `overall_eval_v1` version: `1` language: `None`
  - criteria: context_naturalness
  - sample_count: 60
- metric: `answer_accuracy`
  - prompt_id: `overall_eval_v1` version: `1` language: `None`
  - criteria: answer_accuracy
  - sample_count: 60
- metric: `naturalness`
  - prompt_id: `overall_eval_v1` version: `1` language: `None`
  - criteria: naturalness
  - sample_count: 60
- metric: `coherence`
  - prompt_id: `overall_eval_v1` version: `1` language: `None`
  - criteria: coherence
  - sample_count: 60
- metric: `engagingness`
  - prompt_id: `overall_eval_v1` version: `1` language: `None`
  - criteria: engagingness
  - sample_count: 60
- metric: `groundedness`
  - prompt_id: `overall_eval_v1` version: `1` language: `None`
  - criteria: groundedness
  - sample_count: 60
