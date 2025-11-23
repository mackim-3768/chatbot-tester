from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI

from chatbot_tester.generator import Message, TestSample
from chatbot_tester.generator.schema import sample_schema
from chatbot_tester.generator.utils import ensure_dir
from chatbot_tester.generator.writers import build_metadata, write_jsonl, write_metadata


DATASET_ID = "ces_llm"
DATASET_VERSION = "v1"
DATASET_NAME = "CES LLM Questions"

TOPIC_PROMPTS: Dict[str, Dict[str, str]] = {
    "번역": {
        "ko": "이 문장을 영어로 번역해 주세요.",
        "zh": "请把这句话翻译成英文。",
        "ja": "この文を英語に翻訳してください。",
        "en": "Please translate the following sentence into English.",
    },
    "문체 변환": {
        "ko": "다음 문장을 더 공손한 문체로 바꿔 주세요.",
        "zh": "请把下面的句子改写成更礼貌的语气。",
        "ja": "次の文をより丁寧な文体に書き換えてください。",
        "en": "Rewrite the following sentence in a more formal style.",
    },
    "요약": {
        "ko": "다음 글을 한 문장으로 요약해 주세요.",
        "zh": "请把下面的文章总结成一句话。",
        "ja": "次の文章を一文で要約してください。",
        "en": "Summarize the following passage in one sentence.",
    },
}

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant for evaluating translation, style transfer, and summarization."
)

QUESTION_SYSTEM_PROMPT = (
    "You are a helpful assistant that writes diverse user questions for LLM evaluation."
)

QUESTION_COUNT_ENV = "CES_TOPIC_QUESTION_COUNT"
OPENAI_MODEL_ENV = "CES_OPENAI_MODEL"


def _get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")

    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def _get_question_count() -> int:
    raw = os.getenv(QUESTION_COUNT_ENV)
    if not raw:
        return 5
    try:
        value = int(raw)
        if value <= 0:
            return 5
        return value
    except ValueError:
        return 5


def _build_question_generation_prompt(topic: str, lang_code: str, base_prompt: str, count: int) -> str:
    text = base_prompt.strip()
    if not text:
        return ""

    if lang_code == "ko":
        return (
            f"[토픽: {topic}]\n{text}\n\n"
            f"위 문장은 이 토픽의 기본 프롬프트 예시입니다. "
            f"이 프롬프트와 같은 목적을 가진 한국어 사용자 질문 예시를 최소 {count}개 이상 만들어 주세요. "
            "각 질문은 서로 다른 상황과 맥락을 갖도록 해 주세요. "
            "특히 'everyday_life'(일상 생활), 'business'(비즈니스)와 같은 시나리오를 고르게 포함해 주세요. "
            "출력은 반드시 JSON 배열 형식으로만 응답해 주세요. "
            "각 원소는 {\"scenario\": \"everyday_life\" 또는 \"business\", \"question\": \"질문 텍스트\"} 형태여야 합니다. "
            "예: [{\"scenario\": \"everyday_life\", \"question\": \"...\"}, {\"scenario\": \"business\", \"question\": \"...\"}]"
        )
    if lang_code == "zh":
        return (
            f"[主题: {topic}]\n{text}\n\n"
            f"上面这句话是该主题的基础提示示例。请基于这个提示，用中文生成不少于 {count} 个用户提问示例，"
            "这些问题都在要求模型执行相同的任务，并且尽量覆盖不同的场景。"
            "特别是要均衡覆盖 'everyday_life'(日常生活) 和 'business'(商务场景) 这两类情境。"
            "请严格以 JSON 数组形式输出结果，每个元素必须是 {\"scenario\": \"everyday_life\" 或 \"business\", \"question\": \"问题文本\"} 形式的对象。"
            "例如: [{\"scenario\": \"everyday_life\", \"question\": \"...\"}, {\"scenario\": \"business\", \"question\": \"...\"}]。"
        )
    if lang_code == "ja":
        return (
            f"[トピック: {topic}]\n{text}\n\n"
            f"上の文はこのトピックの基本プロンプト例です。このプロンプトと同じ目的を持つ日本語のユーザー質問例を少なくとも{count}個作成してください。"
            "それぞれ異なる状況や文脈になるようにしてください。"
            "特に 'everyday_life'(日常生活) と 'business'(ビジネス) のシナリオをバランスよく含めてください。"
            "出力は必ずJSON配列として返してください。各要素は {\"scenario\": \"everyday_life\" または \"business\", \"question\": \"質問テキスト\"} 形式のオブジェクトにしてください。"
            "例: [{\"scenario\": \"everyday_life\", \"question\": \"...\"}, {\"scenario\": \"business\", \"question\": \"...\"}]"
        )

    # default: English
    return (
        f"[Topic: {topic}]\n{text}\n\n"
        f"The sentence above is a base prompt example for this topic. Based on it, generate at least {count} different English "
        "user questions that ask the model to perform the same kind of task, covering diverse situations. "
        "Make sure to cover scenarios such as 'everyday_life' and 'business' in a balanced way. "
        "Respond strictly as a JSON array where each element is an object of the form {\"scenario\": \"everyday_life\" or \"business\", \"question\": \"question text\"}. "
        "Example: [{\"scenario\": \"everyday_life\", \"question\": \"...\"}, {\"scenario\": \"business\", \"question\": \"...\"}]."
    )


def _parse_questions(text: str, expected_count: int) -> List[Dict[str, Any]]:
    text = (text or "").strip()
    if not text:
        return []

    def _strip_code_fences(t: str) -> str:
        if not t.startswith("```"):
            return t
        lines = t.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        return "\n".join(lines).strip()

    cleaned = _strip_code_fences(text)

    for candidate in (cleaned, text):
        try:
            data = json.loads(candidate)
            if isinstance(data, list):
                results: List[Dict[str, Any]] = []
                for item in data:
                    if isinstance(item, dict):
                        q_text = str(item.get("question", "")).strip()
                        if not q_text:
                            continue
                        scenario = item.get("scenario")
                        scenario_str = str(scenario).strip() if scenario is not None else None
                        results.append({"question": q_text, "scenario": scenario_str})
                    else:
                        q_text = str(item).strip()
                        if not q_text:
                            continue
                        results.append({"question": q_text, "scenario": None})
                return results[:expected_count]
        except Exception:
            continue

    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    results: List[Dict[str, Any]] = []
    for ln in lines:
        if ln.startswith("``"):
            continue
        if ln in ("[", "]", ","):
            continue

        json_candidate = ln.rstrip().rstrip(",").strip()
        if json_candidate.startswith("{") and "question" in json_candidate:
            try:
                obj = json.loads(json_candidate)
                q_text = str(obj.get("question", "")).strip()
                if not q_text:
                    continue
                scenario = obj.get("scenario")
                scenario_str = str(scenario).strip() if scenario is not None else None
                results.append({"question": q_text, "scenario": scenario_str})
                if len(results) >= expected_count:
                    break
                continue
            except Exception:
                pass

        if ln and ln[0] in "-•*":
            ln = ln[1:].strip()
        i = 0
        while i < len(ln) and (ln[i].isdigit() or ln[i] in ".)】］]"):
            i += 1
        ln = ln[i:].strip()
        if ln:
            results.append({"question": ln, "scenario": None})
        if len(results) >= expected_count:
            break
    return results[:expected_count]


def _build_eval_system_prompt(topic: str, lang_code: str, base_prompt: str) -> str:
    base = DEFAULT_SYSTEM_PROMPT
    return (
        f"{base}\n\n"
        f"Topic: {topic}\n"
        f"Language: {lang_code}\n"
        "Base instruction for this topic:\n"
        f"{base_prompt.strip()}"
    )


def _generate_questions_for_topic(
    client: OpenAI,
    model: str,
    topic: str,
    lang_code: str,
    base_prompt: str,
    count: int,
) -> List[Dict[str, Any]]:
    gen_prompt = _build_question_generation_prompt(topic, lang_code, base_prompt, count)
    if not gen_prompt:
        return []

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": QUESTION_SYSTEM_PROMPT},
            {"role": "user", "content": gen_prompt},
        ],
        temperature=0.7,
    )

    content = resp.choices[0].message.content or ""
    return _parse_questions(content, expected_count=count)


def _build_topic_samples() -> List[TestSample]:
    client = _get_openai_client()
    model = os.getenv(OPENAI_MODEL_ENV, os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    question_count = _get_question_count()

    samples: List[TestSample] = []
    idx = 1

    for topic, lang_map in TOPIC_PROMPTS.items():
        for lang_code, user_text in lang_map.items():
            base_prompt = str(user_text).strip()
            if not base_prompt:
                continue

            questions = _generate_questions_for_topic(
                client=client,
                model=model,
                topic=topic,
                lang_code=lang_code,
                base_prompt=base_prompt,
                count=question_count,
            )
            if not questions:
                continue

            system_prompt = _build_eval_system_prompt(topic, lang_code, base_prompt)

            for item in questions:
                q_text = str(item.get("question", "")).strip()
                if not q_text:
                    continue

                scenario = item.get("scenario")
                scenario_str = str(scenario).strip() if scenario is not None else None

                messages = [
                    Message(role="system", content=system_prompt),
                    Message(role="user", content=q_text),
                ]
                metadata = {
                    "language": lang_code,
                    "topic": topic,
                    "source": "ces_topics_generated",
                    "base_prompt": base_prompt,
                }
                if scenario_str:
                    metadata["scenario"] = scenario_str

                tags = [topic, f"lang:{lang_code}"]
                if scenario_str:
                    tags.append(f"scenario:{scenario_str}")

                sample = TestSample(
                    id=str(idx),
                    messages=messages,
                    expected=None,
                    tags=tags,
                    metadata=metadata,
                )
                samples.append(sample)
                idx += 1

    return samples


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    out_root = Path(__file__).resolve().parents[1] / "datasets" / f"{DATASET_ID}_{DATASET_VERSION}"
    ensure_dir(out_root)

    samples = _build_topic_samples()
    source = {"type": "ces_topics", "topics": list(TOPIC_PROMPTS.keys())}
    name = "CES topic-based multilingual dataset"

    records = [s.to_dict() for s in samples]

    write_jsonl(records, out_root / "test.jsonl")

    meta = build_metadata(
        dataset_id=DATASET_ID,
        name=name,
        version=DATASET_VERSION,
        source=source,
        samples=records,
        filters={},
        sampling={"strategy": "all", "count": len(records)},
        repo_dir=root,
    )
    write_metadata(meta, out_root / "metadata.json")

    schema_path = out_root / "schema.json"
    with schema_path.open("w", encoding="utf-8") as f:
        json.dump(sample_schema(), f, ensure_ascii=False, indent=2)

    print(str(out_root))


if __name__ == "__main__":  # pragma: no cover
    main()
