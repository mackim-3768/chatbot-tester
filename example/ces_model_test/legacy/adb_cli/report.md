# Experiment metadata

- dataset_id: `ces_llm`
- name: `CES topic-based multilingual dataset`
- version: `v1`
- source: `{'type': 'ces_topics', 'topics': ['번역', '문체 변환', '요약']}`

## Overall metrics summary

| metric | mean | std | sample_count |
| --- | ---: | ---: | ---: |
| keyword_coverage_simple (0-1) | 0.0000 | 0.0000 | 60 |
| topic_alignment (0-1) | 0.2733 | 0.3614 | 60 |
| language_match (0-1) | 0.7167 | 0.4506 | 60 |
| context_naturalness (0-1) | 0.2733 | 0.3444 | 60 |
| answer_accuracy (0-1) | 0.2283 | 0.3416 | 60 |
| naturalness (0-1) | 0.2967 | 0.3415 | 60 |
| coherence (0-1) | 0.3017 | 0.3500 | 60 |
| engagingness (0-1) | 0.2200 | 0.2982 | 60 |
| groundedness (0-1) | 0.2667 | 0.3515 | 60 |

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
| topic_alignment (0-1) | 번역 | 0.2600 | 0.3800 | 20 |
| topic_alignment (0-1) | lang:ko | 0.3200 | 0.3563 | 15 |
| topic_alignment (0-1) | scenario:everyday_life | 0.2778 | 0.3779 | 36 |
| topic_alignment (0-1) | scenario:business | 0.2667 | 0.3350 | 24 |
| topic_alignment (0-1) | lang:zh | 0.4533 | 0.3896 | 15 |
| topic_alignment (0-1) | lang:ja | 0.2000 | 0.3347 | 15 |
| topic_alignment (0-1) | lang:en | 0.1200 | 0.2613 | 15 |
| topic_alignment (0-1) | 문체 변환 | 0.3000 | 0.3715 | 20 |
| topic_alignment (0-1) | 요약 | 0.2600 | 0.3292 | 20 |
| language_match (0-1) | 번역 | 0.3000 | 0.4583 | 20 |
| language_match (0-1) | lang:ko | 0.6000 | 0.4899 | 15 |
| language_match (0-1) | scenario:everyday_life | 0.7500 | 0.4330 | 36 |
| language_match (0-1) | scenario:business | 0.6667 | 0.4714 | 24 |
| language_match (0-1) | lang:zh | 0.6667 | 0.4714 | 15 |
| language_match (0-1) | lang:ja | 0.6667 | 0.4714 | 15 |
| language_match (0-1) | lang:en | 0.9333 | 0.2494 | 15 |
| language_match (0-1) | 문체 변환 | 0.9000 | 0.3000 | 20 |
| language_match (0-1) | 요약 | 0.9500 | 0.2179 | 20 |
| context_naturalness (0-1) | 번역 | 0.2500 | 0.3626 | 20 |
| context_naturalness (0-1) | lang:ko | 0.3200 | 0.3563 | 15 |
| context_naturalness (0-1) | scenario:everyday_life | 0.2722 | 0.3626 | 36 |
| context_naturalness (0-1) | scenario:business | 0.2750 | 0.3152 | 24 |
| context_naturalness (0-1) | lang:zh | 0.4133 | 0.3538 | 15 |
| context_naturalness (0-1) | lang:ja | 0.2267 | 0.3336 | 15 |
| context_naturalness (0-1) | lang:en | 0.1333 | 0.2599 | 15 |
| context_naturalness (0-1) | 문체 변환 | 0.3100 | 0.3491 | 20 |
| context_naturalness (0-1) | 요약 | 0.2600 | 0.3169 | 20 |
| answer_accuracy (0-1) | 번역 | 0.1800 | 0.3516 | 20 |
| answer_accuracy (0-1) | lang:ko | 0.2667 | 0.3771 | 15 |
| answer_accuracy (0-1) | scenario:everyday_life | 0.2278 | 0.3469 | 36 |
| answer_accuracy (0-1) | scenario:business | 0.2292 | 0.3335 | 24 |
| answer_accuracy (0-1) | lang:zh | 0.4067 | 0.3696 | 15 |
| answer_accuracy (0-1) | lang:ja | 0.1200 | 0.2509 | 15 |
| answer_accuracy (0-1) | lang:en | 0.1200 | 0.2613 | 15 |
| answer_accuracy (0-1) | 문체 변환 | 0.2800 | 0.3544 | 20 |
| answer_accuracy (0-1) | 요약 | 0.2250 | 0.3096 | 20 |
| naturalness (0-1) | 번역 | 0.2100 | 0.3254 | 20 |
| naturalness (0-1) | lang:ko | 0.3333 | 0.3553 | 15 |
| naturalness (0-1) | scenario:everyday_life | 0.3000 | 0.3575 | 36 |
| naturalness (0-1) | scenario:business | 0.2917 | 0.3161 | 24 |
| naturalness (0-1) | lang:zh | 0.4933 | 0.3492 | 15 |
| naturalness (0-1) | lang:ja | 0.1733 | 0.2620 | 15 |
| naturalness (0-1) | lang:en | 0.1867 | 0.2872 | 15 |
| naturalness (0-1) | 문체 변환 | 0.3200 | 0.3544 | 20 |
| naturalness (0-1) | 요약 | 0.3600 | 0.3262 | 20 |
| coherence (0-1) | 번역 | 0.2200 | 0.3458 | 20 |
| coherence (0-1) | lang:ko | 0.3333 | 0.3553 | 15 |
| coherence (0-1) | scenario:everyday_life | 0.3000 | 0.3575 | 36 |
| coherence (0-1) | scenario:business | 0.3042 | 0.3385 | 24 |
| coherence (0-1) | lang:zh | 0.5133 | 0.3703 | 15 |
| coherence (0-1) | lang:ja | 0.1733 | 0.2620 | 15 |
| coherence (0-1) | lang:en | 0.1867 | 0.2872 | 15 |
| coherence (0-1) | 문체 변환 | 0.3200 | 0.3544 | 20 |
| coherence (0-1) | 요약 | 0.3650 | 0.3336 | 20 |
| engagingness (0-1) | 번역 | 0.1700 | 0.2629 | 20 |
| engagingness (0-1) | lang:ko | 0.2933 | 0.3415 | 15 |
| engagingness (0-1) | scenario:everyday_life | 0.2167 | 0.3032 | 36 |
| engagingness (0-1) | scenario:business | 0.2250 | 0.2905 | 24 |
| engagingness (0-1) | lang:zh | 0.3467 | 0.2963 | 15 |
| engagingness (0-1) | lang:ja | 0.1200 | 0.2509 | 15 |
| engagingness (0-1) | lang:en | 0.1200 | 0.2166 | 15 |
| engagingness (0-1) | 문체 변환 | 0.2700 | 0.3422 | 20 |
| engagingness (0-1) | 요약 | 0.2200 | 0.2750 | 20 |
| groundedness (0-1) | 번역 | 0.2100 | 0.3434 | 20 |
| groundedness (0-1) | lang:ko | 0.3200 | 0.3563 | 15 |
| groundedness (0-1) | scenario:everyday_life | 0.2556 | 0.3609 | 36 |
| groundedness (0-1) | scenario:business | 0.2833 | 0.3362 | 24 |
| groundedness (0-1) | lang:zh | 0.4533 | 0.3896 | 15 |
| groundedness (0-1) | lang:ja | 0.1333 | 0.2599 | 15 |
| groundedness (0-1) | lang:en | 0.1600 | 0.2847 | 15 |
| groundedness (0-1) | 문체 변환 | 0.3300 | 0.3703 | 20 |
| groundedness (0-1) | 요약 | 0.2600 | 0.3292 | 20 |

### language

| metric | bucket | mean | std | sample_count |
| --- | --- | ---: | ---: | ---: |
| keyword_coverage_simple (0-1) | ko | 0.0000 | 0.0000 | 15 |
| keyword_coverage_simple (0-1) | zh | 0.0000 | 0.0000 | 15 |
| keyword_coverage_simple (0-1) | ja | 0.0000 | 0.0000 | 15 |
| keyword_coverage_simple (0-1) | en | 0.0000 | 0.0000 | 15 |
| topic_alignment (0-1) | ko | 0.3200 | 0.3563 | 15 |
| topic_alignment (0-1) | zh | 0.4533 | 0.3896 | 15 |
| topic_alignment (0-1) | ja | 0.2000 | 0.3347 | 15 |
| topic_alignment (0-1) | en | 0.1200 | 0.2613 | 15 |
| language_match (0-1) | ko | 0.6000 | 0.4899 | 15 |
| language_match (0-1) | zh | 0.6667 | 0.4714 | 15 |
| language_match (0-1) | ja | 0.6667 | 0.4714 | 15 |
| language_match (0-1) | en | 0.9333 | 0.2494 | 15 |
| context_naturalness (0-1) | ko | 0.3200 | 0.3563 | 15 |
| context_naturalness (0-1) | zh | 0.4133 | 0.3538 | 15 |
| context_naturalness (0-1) | ja | 0.2267 | 0.3336 | 15 |
| context_naturalness (0-1) | en | 0.1333 | 0.2599 | 15 |
| answer_accuracy (0-1) | ko | 0.2667 | 0.3771 | 15 |
| answer_accuracy (0-1) | zh | 0.4067 | 0.3696 | 15 |
| answer_accuracy (0-1) | ja | 0.1200 | 0.2509 | 15 |
| answer_accuracy (0-1) | en | 0.1200 | 0.2613 | 15 |
| naturalness (0-1) | ko | 0.3333 | 0.3553 | 15 |
| naturalness (0-1) | zh | 0.4933 | 0.3492 | 15 |
| naturalness (0-1) | ja | 0.1733 | 0.2620 | 15 |
| naturalness (0-1) | en | 0.1867 | 0.2872 | 15 |
| coherence (0-1) | ko | 0.3333 | 0.3553 | 15 |
| coherence (0-1) | zh | 0.5133 | 0.3703 | 15 |
| coherence (0-1) | ja | 0.1733 | 0.2620 | 15 |
| coherence (0-1) | en | 0.1867 | 0.2872 | 15 |
| engagingness (0-1) | ko | 0.2933 | 0.3415 | 15 |
| engagingness (0-1) | zh | 0.3467 | 0.2963 | 15 |
| engagingness (0-1) | ja | 0.1200 | 0.2509 | 15 |
| engagingness (0-1) | en | 0.1200 | 0.2166 | 15 |
| groundedness (0-1) | ko | 0.3200 | 0.3563 | 15 |
| groundedness (0-1) | zh | 0.4533 | 0.3896 | 15 |
| groundedness (0-1) | ja | 0.1333 | 0.2599 | 15 |
| groundedness (0-1) | en | 0.1600 | 0.2847 | 15 |

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
