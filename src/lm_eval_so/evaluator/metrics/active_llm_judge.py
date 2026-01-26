from __future__ import annotations

import json
import os
from typing import Any, Mapping

from openai import OpenAI

from ..domain import EvalScore, RunRecord, TestSampleRecord
from .base import Metric


class ActiveLLMJudgeMetric(Metric):
    """
    Active LLM Judge Metric.

    Evaluates a sample by calling an LLM (e.g., GPT-4) as a judge in real-time.
    This contrasts with the passive `LLMJudgeMetric` which consumes pre-computed scores.

    The metric constructs a prompt including the input, expected answer, and the actual answer,
    then asks the LLM to score it (typically 1-5) and provide a reason.

    Parameters (via config):

    - model: str (default "gpt-4")
    - prompt_template: str (optional, overrides default template)
    - max_score: float (default 5.0)
    - api_key: str (optional, defaults to env var OPENAI_API_KEY)
    - base_url: str (optional, defaults to env var OPENAI_BASE_URL)
    """

    requires_reference: bool = False  # Can work without expected output if prompt is designed so

    def __init__(self, *, name: str, parameters: Mapping[str, Any] | None = None) -> None:
        super().__init__(name=name, parameters=parameters)
        p = self.parameters
        self.model = str(p.get("model", "gpt-4"))
        self.prompt_template = str(p.get("prompt_template", ""))
        self.max_score = float(p.get("max_score", 5.0))
        self.api_key = p.get("api_key") or os.getenv("OPENAI_API_KEY")
        self.base_url = p.get("base_url") or os.getenv("OPENAI_BASE_URL")

        # Initialize client lazily or now? Now is fine.
        if not self.api_key:
            # We don't raise error here to allow loading the class, but score() might fail
            pass

        self._client = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY is required for ActiveLLMJudgeMetric")
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def _build_default_prompt(self, user_input: str, expected: str, actual: str) -> str:
        return (
            "You are an impartial judge evaluating the quality of a chatbot response.\n\n"
            "## User Input:\n"
            f"{user_input}\n\n"
            "## Expected Answer (Reference):\n"
            f"{expected}\n\n"
            "## Actual Chatbot Response:\n"
            f"{actual}\n\n"
            "Please evaluate the Actual Chatbot Response based on accuracy and helpfulness compared to the Reference.\n"
            "Provide a score from 1 to 5 (integer) and a brief reasoning.\n"
            "Output strictly in JSON format with keys: 'score' (int) and 'reason' (string)."
        )

    def score(self, sample: TestSampleRecord, run: RunRecord) -> EvalScore:
        user_input = ""
        # Try to find the last user message from messages
        # sample.messages is a list of Message objects or dicts depending on record type
        # TestSampleRecord definition says messages: List[Dict[str, Any]] (dict objects)
        for m in reversed(sample.messages):
            role = m.get("role")
            if role == "user":
                user_input = str(m.get("content", ""))
                break

        expected = str(sample.expected) if sample.expected else "N/A"
        actual = run.response_text or ""

        # Build prompt
        if self.prompt_template:
            # Simple substitution
            prompt = self.prompt_template.format(
                input=user_input,
                expected=expected,
                actual=actual
            )
        else:
            prompt = self._build_default_prompt(user_input, expected, actual)

        try:
            client = self._get_client()
            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )

            content = completion.choices[0].message.content or "{}"
            data = json.loads(content)

            raw_score = float(data.get("score", 0))
            reason = data.get("reason", "No reason provided")

            # Normalize score
            normalized_value = raw_score / self.max_score if self.max_score > 0 else 0.0

            detail = {
                "raw_score": raw_score,
                "reason": reason,
                "prompt_used": prompt,
                "model": self.model
            }

            return self.make_score(sample, value=normalized_value, detail=detail)

        except Exception as e:
            return self.make_score(
                sample,
                value=0.0,
                detail={"error": str(e), "skipped": True}
            )
