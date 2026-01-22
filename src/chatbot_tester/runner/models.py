from chatbot_tester.core.models import (
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
    from typing import Any, List, Iterable, Mapping
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
