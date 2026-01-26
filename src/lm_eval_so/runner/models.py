from typing import Any, List

from lm_eval_so.core.models import (
    ChatResponse,
    DatasetInfo,
    Message,
    RunConfig,
    RunError,
    RunRequest,
    RunResult,
    RunResultStatus,
    TestSample,
    TokenUsage,
)

def ensure_messages(value: Any) -> List[Message]:
    """Ensure that the input value is converted to a list of Message objects.

    When to use:
        Use this helper when parsing raw input (e.g. from JSON or YAML) that represents 
        chat history, ensuring it's in the correct internal model format.

    Args:
        value: A list of message-like dictionaries or objects.

    Returns:
        List[Message]: Validated list of Message objects.
    """
    return [Message.from_dict(v) for v in value]

__all__ = [
    "ChatResponse",
    "DatasetInfo",
    "Message",
    "RunConfig",
    "RunError",
    "RunRequest",
    "RunResult",
    "RunResultStatus",
    "TestSample",
    "TokenUsage",
    "ensure_messages",
]
