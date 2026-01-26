from typing import Dict, Any


def sample_schema() -> Dict[str, Any]:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Chatbot Test Sample",
        "type": "object",
        "additionalProperties": True,
        "required": ["id", "messages"],
        "properties": {
            "id": {"type": "string"},
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["role", "content"],
                    "properties": {
                        "role": {
                            "type": "string",
                            "enum": [
                                "system",
                                "user",
                                "assistant",
                                "tool",
                                "function",
                            ],
                        },
                        "content": {"type": "string"},
                        "name": {"type": "string"},
                        "metadata": {"type": "object"},
                    },
                    "additionalProperties": True,
                },
            },
            "expected": {},
            "tags": {"type": "array", "items": {"type": "string"}},
            "metadata": {"type": "object"},
        },
    }


def dataset_metadata_schema() -> Dict[str, Any]:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Dataset Metadata",
        "type": "object",
        "required": ["dataset_id", "name", "version", "created_at", "generator_version", "sample_count"],
        "properties": {
            "dataset_id": {"type": "string"},
            "name": {"type": "string"},
            "version": {"type": "string"},
            "created_at": {"type": "string"},
            "source": {"type": ["string", "object", "null"]},
            "generator_version": {"type": "string"},
            "generator_commit": {"type": ["string", "null"]},
            "generator_code_commit": {"type": ["string", "null"]},
            "sample_count": {"type": "integer"},
            "filters": {"type": "object"},
            "sampling": {"type": "object"},
            "tag_stats": {"type": "object"},
            "language_stats": {"type": "object"},
        },
        "additionalProperties": True,
    }
