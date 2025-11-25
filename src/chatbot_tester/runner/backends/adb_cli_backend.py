from __future__ import annotations

import json
import shlex
import subprocess
from typing import Any, Dict, List

from ..exceptions import BackendError
from ..models import ChatResponse, Message, RunRequest, TokenUsage
from ..utils import run_in_thread
from .base import ChatBackend, register_backend


def _messages_to_dict(messages: List[Message]) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for msg in messages:
        entry: Dict[str, Any] = {"role": msg.role, "content": msg.content}
        if msg.name:
            entry["name"] = msg.name
        if msg.metadata:
            entry["metadata"] = msg.metadata
        payload.append(entry)
    return payload


@register_backend("adb-cli")
class AdbCliBackend(ChatBackend):
    """Executes a CLI binary inside an ADB-connected device."""

    async def send(self, request: RunRequest) -> ChatResponse:
        command = self._build_adb_command()
        payload = {
            "sample_id": request.sample.id,
            "messages": _messages_to_dict(request.messages),
            "model": request.run_config.model,
            "parameters": request.run_config.parameters,
            "metadata": request.sample.metadata,
        }
        input_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        stdout = await run_in_thread(
            self._invoke_subprocess,
            command,
            input_bytes,
            request.timeout_seconds,
        )
        return self._parse_response(stdout)

    def _build_adb_command(self) -> List[str]:
        adb_path = self.backend_options.get("adb_path", "adb")
        binary = self.backend_options.get("binary")
        if not binary:
            raise BackendError("ADB backend requires 'binary' option", error_type="config", retryable=False)
        command = [adb_path]
        device_id = self.backend_options.get("device_id")
        if device_id:
            command += ["-s", device_id]
        command += ["shell", binary]
        extra_args = self.backend_options.get("binary_args")
        if isinstance(extra_args, str):
            extra_args = shlex.split(extra_args)
        if isinstance(extra_args, list):
            command += [str(a) for a in extra_args]
        return command

    def _invoke_subprocess(self, command: List[str], input_bytes: bytes, timeout: float | None) -> str:
        try:
            proc = subprocess.run(
                command,
                input=input_bytes,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise BackendError("ADB command timed out", error_type="timeout", retryable=True) from exc
        except FileNotFoundError as exc:
            raise BackendError("adb binary not found", error_type="adb_missing", retryable=False) from exc
        except Exception as exc:  # pragma: no cover
            raise BackendError(str(exc), error_type="adb_error", retryable=False) from exc

        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", errors="ignore")
            raise BackendError(
                f"ADB binary exited with code {proc.returncode}: {stderr.strip()}",
                error_type="adb_exit",
                retryable=True,
            )
        stdout = proc.stdout.decode("utf-8", errors="ignore").strip()
        if not stdout:
            raise BackendError("ADB binary returned empty response", error_type="adb_response", retryable=False)
        return stdout

    def _parse_response(self, stdout: str) -> ChatResponse:
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as exc:
            # Attach raw stdout to error details for easier debugging when device does not return JSON
            snippet_len = 2000
            head = stdout[:snippet_len]
            tail = stdout[-snippet_len:] if len(stdout) > snippet_len else None
            details = {"stdout_head": head}
            if tail is not None:
                details["stdout_tail"] = tail
            raise BackendError(
                "Invalid JSON from device",
                error_type="parse_error",
                retryable=False,
                details=details,
            ) from exc

        text = data.get("text")
        if text is None:
            raise BackendError("Response missing 'text' field", error_type="response_format", retryable=False)

        usage = None
        usage_data = data.get("usage")
        if isinstance(usage_data, dict):
            usage = TokenUsage(
                input_tokens=usage_data.get("input") or usage_data.get("prompt"),
                output_tokens=usage_data.get("output") or usage_data.get("completion"),
                total_tokens=usage_data.get("total"),
            )

        return ChatResponse(
            text=text,
            raw=data,
            usage=usage,
            finish_reason=data.get("finish_reason"),
            status_code=0,
        )
