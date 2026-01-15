from __future__ import annotations
from dataclasses import dataclass, field
import logging
from typing import Any
from chatbot_tester.common.context import Context

@dataclass
class RunnerContext(Context):
    """Holds execution-scoped options and logger."""
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("chatbot_tester.runner"))

    def child(self, **options: Any) -> "RunnerContext":
        child_opts = {**self.options, **options}
        return RunnerContext(options=child_opts, logger=self.logger, trace_prefix=self.trace_prefix)
