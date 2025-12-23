from __future__ import annotations

import json
import os
import random
from typing import Any, List, Optional

from openai import OpenAI
from ..types import Message, TestSample
from ..utils import gen_id_from_messages


class ParaphraseAugmenter:
    """
    Augments the dataset by generating paraphrases of user messages.

    It uses an LLM to generate multiple variations of the user's input
    (e.g., formal, casual, concise, with typos) while keeping the expected answer
    roughly the same or adapting it if necessary.
    """

    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
             # Warning: API key is missing
             pass
        self._client = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY is required for ParaphraseAugmenter")
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def augment(self, sample: TestSample, count: int = 3) -> List[TestSample]:
        """
        Generates `count` new samples based on the given sample.
        """
        user_msg = next((m.content for m in sample.messages if m.role == "user"), None)
        if not user_msg:
            return []

        return self._augment_impl(sample, user_msg, count)

    def _augment_impl(self, sample: TestSample, user_msg: str, count: int) -> List[TestSample]:
        prompt = (
            f"Original User Query: \"{user_msg}\"\n"
            f"Generate {count} distinct paraphrases of this query.\n"
            "Return a JSON object with a key 'variations' containing a list of strings."
        )

        try:
            client = self._get_client()
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data augmentation assistant that outputs JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            content = resp.choices[0].message.content or "{}"
            data = json.loads(content)
            variations = data.get("variations", [])

            new_samples = []
            for i, var in enumerate(variations):
                if not isinstance(var, str) or not var.strip():
                    continue

                # Clone messages and replace user content
                new_msgs = []
                for m in sample.messages:
                    if m.role == "user":
                        new_msgs.append(Message(role="user", content=var, name=m.name, metadata=m.metadata))
                    else:
                        new_msgs.append(m)

                # Generate new ID
                new_id = gen_id_from_messages([m.to_dict() for m in new_msgs])

                # Clone tags
                new_tags = list(sample.tags) if sample.tags else []
                new_tags.append("augmented")

                new_sample = TestSample(
                    id=new_id,
                    messages=new_msgs,
                    expected=sample.expected, # Keep expected answer? Usually yes for paraphrase.
                    tags=new_tags,
                    metadata=sample.metadata.copy() if sample.metadata else {}
                )
                new_sample.metadata["original_sample_id"] = sample.id
                new_sample.metadata["augmentation_type"] = "paraphrase"

                new_samples.append(new_sample)

            return new_samples

        except Exception as e:
            # Log error?
            return []
