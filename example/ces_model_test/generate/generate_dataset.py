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
            f"이 프롬프트와 같은 목적을 가진 한국어 사용자 질문 예시를 {count}개 만들어 주세요. "
            "각 질문은 서로 다른 상황과 맥락을 갖도록 해 주세요. "
            "출력은 반드시 문자열들의 JSON 배열 형식으로만 응답해 주세요. 예: [\"질문1\", \"질문2\", ...]"
        )
    if lang_code == "zh":
        return (
            f"[主题: {topic}]\n{text}\n\n"
            f"上面这句话是该主题的基础提示示例。请基于这个提示，用中文生成 {count} 个用户提问示例，"
            "这些问题都在要求模型执行相同的任务，并且尽量覆盖不同的场景。"
            "请严格以 JSON 数组形式输出结果，例如：[\"问题1\", \"问题2\", ...]。"
        )
    if lang_code == "ja":
        return (
            f"[トピック: {topic}]\n{text}\n\n"
            f"上の文はこのトピックの基本プロンプト例です。このプロンプトと同じ目的を持つ日本語のユーザー質問例を{count}個作成してください。"
            "それぞれ異なる状況や文脈になるようにしてください。"
            "出力は必ず文字列のJSON配列として返してください。例: [\"質問1\", \"質問2\", ...]"
        )

    # default: English
    return (
        f"[Topic: {topic}]\n{text}\n\n"
        f"The sentence above is a base prompt example for this topic. Based on it, generate {count} different English "
        "user questions that ask the model to perform the same kind of task, covering diverse situations. "
        "Respond strictly as a JSON array of strings, e.g. [\"Question 1\", \"Question 2\", ...]."
    )


def _parse_questions(text: str, expected_count: int) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []

    # 1) JSON 배열 파싱 시도
    try:
        data = json.loads(text)
        if isinstance(data, list):
            questions = [str(q).strip() for q in data if str(q).strip()]
            return questions[:expected_count]
    except Exception:
        pass

    # 2) 실패 시, 줄 단위로 파싱하면서 번호/불릿 제거
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    questions: List[str] = []
    for ln in lines:
        # 불릿/숫자 목록 제거 (예: "1. ...", "- ...")
        if ln[0] in "-•*":
            ln = ln[1:].strip()
        i = 0
        while i < len(ln) and (ln[i].isdigit() or ln[i] in ".)】］]"):
            i += 1
        ln = ln[i:].strip()
        if ln:
            questions.append(ln)
        if len(questions) >= expected_count:
            break
    return questions[:expected_count]


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
) -> List[str]:
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

            for q in questions:
                q_text = str(q).strip()
                if not q_text:
                    continue

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
                tags = [topic, f"lang:{lang_code}"]
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
