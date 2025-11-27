from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from openai import OpenAI


SYSTEM_PROMPT = """You are an expert evaluator for multilingual chatbot outputs.\nYou will evaluate the quality of the assistant's answer along several criteria.\nYou must strictly follow the scoring guidelines and output format.\n"""


USER_TEMPLATE = """You are given task metadata, a user message, and a model answer.\n\n[Task metadata]\n- Topic: {topic}\n- Language: {language}\n- Base instruction: {base_instruction}\n\n[Conversation]\n- User message:\n{user_message}\n\n- Model answer:\n{model_answer}\n\nEvaluate the answer on these criteria and assign scores:\n1. topic_score (0-5): how well the answer matches the intended topic/task.\n2. lang_match (0 or 1): 1 if the output language matches the expected target language, else 0.\n3. context_score (0-5): contextual appropriateness and coherence with the user message.\n4. accuracy_score (0-5): how accurately the answer responds to the user's request.\n5. naturalness (0-5): fluency and naturalness of the output.\n6. coherence (0-5): internal logical consistency within the answer.\n7. engagingness (0-5): how engaging and pleasant the answer is, given the task.\n8. groundedness (0-5): whether the answer is grounded in the given input without clear hallucinations.\n\nScoring rules:\n- Use the full range 0-5 when appropriate, decimals allowed (e.g. 3.5).\n\nOutput format:\nReturn ONLY a JSON object with exactly these numeric fields:\n  topic_score, lang_match, context_score, accuracy_score,\n  naturalness, coherence, engagingness, groundedness.\nDo not include explanations or any text outside the JSON.\n"""

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RUN_RESULTS = BASE_DIR / "output" / "runs" / "adb_cli" / "run_results.jsonl"


def _infer_language(tags: List[str], meta: Dict[str, Any]) -> str:
    lang = str(meta.get("language") or "").strip()
    if lang:
        return lang
    for t in tags:
        if t.startswith("lang:"):
            return t.split(":", 1)[1]
    return "unknown"


def build_judge_prompt(sample: Dict[str, Any]) -> str:
    request = sample.get("request", {})
    context = request.get("context", {})
    meta = context.get("sample_metadata", {}) or {}
    tags = context.get("sample_tags", []) or []

    topic = str(meta.get("topic") or "unknown")
    language = _infer_language(list(tags), meta)
    base_instruction = str(meta.get("base_prompt") or "").strip()

    messages = request.get("messages", []) or []
    user_message = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_message = str(m.get("content") or "")
            break

    response = sample.get("response", {}) or {}
    model_answer = str(response.get("text") or "")

    return USER_TEMPLATE.format(
        topic=topic,
        language=language,
        base_instruction=base_instruction,
        user_message=user_message,
        model_answer=model_answer,
    )


def call_openai_judge(client: OpenAI, prompt: str, model: str) -> Dict[str, float]:
    completion = client.chat.completions.create(
        model=model,
        temperature=0.0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    content = completion.choices[0].message.content or "{}"
    data = json.loads(content)
    return {
        "topic_score": float(data.get("topic_score", 0.0)),
        "lang_match": float(data.get("lang_match", 0.0)),
        "context_score": float(data.get("context_score", 0.0)),
        "accuracy_score": float(data.get("accuracy_score", 0.0)),
        "naturalness": float(data.get("naturalness", 0.0)),
        "coherence": float(data.get("coherence", 0.0)),
        "engagingness": float(data.get("engagingness", 0.0)),
        "groundedness": float(data.get("groundedness", 0.0)),
    }


def load_runs(path: Path) -> List[Dict[str, Any]]:
    runs: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            runs.append(json.loads(line))
    return runs


def save_runs(path: Path, runs: List[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for obj in runs:
            json.dump(obj, f, ensure_ascii=False)
            f.write("\n")


def apply_llm_judge(input_path: Path, output_path: Path, model: str) -> None:
    runs = load_runs(input_path)
    client = OpenAI()

    for obj in runs:
        if obj.get("status") != "ok":
            continue
        response = obj.setdefault("response", {})
        raw = response.setdefault("raw", {})
        llm_judge = raw.setdefault("llm_judge", {})
        overall = llm_judge.get("overall")
        if overall is not None:
            continue

        prompt = build_judge_prompt(obj)
        scores = call_openai_judge(client, prompt, model)
        llm_judge["overall"] = scores

    save_runs(output_path, runs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_RUN_RESULTS),
        help="Path to run_results.jsonl to read.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to write updated runs. If omitted, overwrites input after creating a .bak backup.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=os.environ.get("OPENAI_JUDGE_MODEL", "gpt-4o-mini"),
        help="OpenAI model name to use for judging.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if args.output:
        output_path = Path(args.output)
    else:
        backup = input_path.with_suffix(input_path.suffix + ".bak")
        if not backup.exists():
            input_path.replace(backup)
        input_path = backup
        output_path = backup.with_name("run_results.jsonl")

    apply_llm_judge(input_path, output_path, args.model)


if __name__ == "__main__":  # pragma: no cover
    main()
