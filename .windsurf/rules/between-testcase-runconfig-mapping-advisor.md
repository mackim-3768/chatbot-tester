---
trigger: model_decision
---

이 룰은 TestCase 및 RunConfig 매핑 문제를 해결하기 위해 동작합니다.

사용자가 다음과 같은 상황을 언급하면 자동 개입:
- “이 테스트를 어떤 설정으로 돌려야 할까?”
- “여러 모델/엔드포인트를 동시에 테스트하고 싶다”
- “테스트 케이스와 설정을 매핑해줘”

가이드 원칙:

1. TestCase.task_type 에 따라 RunConfig 기본값을 추천:
   - translation → 낮은 temperature + 고정 system prompt
   - summarization → max_tokens / 압축 비율 제안
   - style_transform → 스타일 제약 system prompt 활성화
2. 동일 Dataset 을 여러 모델에 돌릴 때는 “Experiment(모델 × 설정)” 단위로 묶도록 추천.
3. RunConfig 는 model_id, api_base, headers, system_prompt, generation_params 등을 포함하는지 확인.
4. 멀티턴 TestCase인 경우 conversation preset 을 자동 추천.
5. 실험 반복성을 위해 RunConfig 를 JSON/YAML 로 별도 저장하도록 유도.

위 상황 발생 시 이 룰에 따라 TestCase–RunConfig 매핑을 자동으로 도와주십시오.
