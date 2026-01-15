from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import logging


@dataclass
class Context:
    """Holds execution-scoped options and logger."""

    options: Dict[str, Any] = field(default_factory=dict)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("chatbot_tester.common"))
    trace_prefix: Optional[str] = None

    def child(self, **options: Any) -> "Context":
        child_opts = {**self.options, **options}
        return Context(options=child_opts, logger=self.logger, trace_prefix=self.trace_prefix)
