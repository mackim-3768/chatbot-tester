from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class RunnerContext:
    """Holds execution-scoped options and logger."""

    options: Dict[str, Any] = field(default_factory=dict)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("chatbot_tester.core"))
    trace_prefix: Optional[str] = None

    def child(self, **options: Any) -> "RunnerContext":
        child_opts = {**self.options, **options}
        return RunnerContext(options=child_opts, logger=self.logger, trace_prefix=self.trace_prefix)
