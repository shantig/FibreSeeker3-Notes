#!/usr/bin/env python3
"""Provider-neutral Phase 2D structured-model adapters.

Adapters receive one deterministic request and return one normalized result. They
do not query the KB, evaluate evidence, or persist provider responses.
"""

from __future__ import annotations

import abc
import json
import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from query_engine import canonical_json


RESULT_VERSION = "1.0.0"
RESULT_VERSION_V2 = "2.0.0"


@dataclass(frozen=True)
class ModelAdapterInfo:
    provider_id: str
    adapter_id: str
    model_id: str


class ModelAdapter(abc.ABC):
    """Replaceable interface for a structured model completion."""

    @property
    @abc.abstractmethod
    def info(self) -> ModelAdapterInfo:
        raise NotImplementedError

    @abc.abstractmethod
    def complete_structured(self, request: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


def validate_model_result(result: dict[str, Any], request: dict[str, Any] | None = None) -> None:
    required = {
        "result_version", "provider_id", "adapter_id", "model_id", "request_id",
        "provider_response_id", "context_packet_id", "prompt_version",
        "response_format_version", "attempt", "latency_ms", "usage",
        "raw_provider_status", "parse_status", "validation_status",
        "structured_output", "error_type", "error_message", "tool_use_detected",
    }
    if not isinstance(result, dict) or set(result) != required:
        raise ValueError("model result does not match the versioned contract")
    if result["result_version"] not in {RESULT_VERSION, RESULT_VERSION_V2}:
        raise ValueError("unsupported model result version")
    if result["parse_status"] not in {"PARSED", "FAILED", "NOT_ATTEMPTED"}:
        raise ValueError("invalid model parse status")
    if result["validation_status"] not in {"PENDING", "VALID", "FAILED", "NOT_ATTEMPTED"}:
        raise ValueError("invalid model validation status")
    if result["parse_status"] == "PARSED" and not isinstance(result["structured_output"], dict):
        raise ValueError("parsed model result must contain a structured object")
    expected_usage = (
        {"input_tokens", "output_tokens", "total_tokens"}
        if result["result_version"] == RESULT_VERSION
        else {
            "input_tokens", "cached_input_tokens", "output_tokens",
            "reasoning_tokens", "total_tokens",
        }
    )
    if set(result["usage"]) != expected_usage:
        raise ValueError("model result usage does not match the contract")
    if request is not None:
        expected = {
            "request_id": request["request_id"],
            "context_packet_id": request["context_packet_id"],
            "prompt_version": request["prompt_version"],
            "response_format_version": request["response_format_version"],
            "attempt": request["attempt"],
        }
        if any(result[key] != value for key, value in expected.items()):
            raise ValueError("model result does not identify the supplied request")


def _usage(value: dict[str, Any] | None) -> dict[str, int | None]:
    value = value or {}
    input_tokens = value.get("input_tokens")
    output_tokens = value.get("output_tokens")
    total_tokens = value.get("total_tokens")
    if total_tokens is None and isinstance(input_tokens, int) and isinstance(output_tokens, int):
        total_tokens = input_tokens + output_tokens
    return {
        "input_tokens": input_tokens if isinstance(input_tokens, int) else None,
        "output_tokens": output_tokens if isinstance(output_tokens, int) else None,
        "total_tokens": total_tokens if isinstance(total_tokens, int) else None,
    }


def _usage_v2(value: dict[str, Any] | None) -> dict[str, int | None]:
    """Normalize Responses/Codex usage detail without inferring absent metrics."""
    value = value or {}
    base = _usage(value)
    input_details = value.get("input_tokens_details")
    output_details = value.get("output_tokens_details")
    cached = (
        input_details.get("cached_tokens")
        if isinstance(input_details, dict)
        else value.get("cached_input_tokens")
    )
    reasoning = (
        output_details.get("reasoning_tokens")
        if isinstance(output_details, dict)
        else value.get("reasoning_tokens")
    )
    return {
        "input_tokens": base["input_tokens"],
        "cached_input_tokens": cached if isinstance(cached, int) else None,
        "output_tokens": base["output_tokens"],
        "reasoning_tokens": reasoning if isinstance(reasoning, int) else None,
        "total_tokens": base["total_tokens"],
    }


def model_result(
    info: ModelAdapterInfo,
    request: dict[str, Any],
    *,
    latency_ms: float,
    provider_response_id: str | None,
    raw_provider_status: str,
    parse_status: str,
    validation_status: str,
    structured_output: dict[str, Any] | None,
    usage: dict[str, Any] | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
    tool_use_detected: bool = False,
    result_version: str = RESULT_VERSION,
) -> dict[str, Any]:
    """Normalize provider output without retaining raw prompts or responses."""
    return {
        "result_version": result_version,
        "provider_id": info.provider_id,
        "adapter_id": info.adapter_id,
        "model_id": info.model_id,
        "request_id": request["request_id"],
        "provider_response_id": provider_response_id,
        "context_packet_id": request["context_packet_id"],
        "prompt_version": request["prompt_version"],
        "response_format_version": request["response_format_version"],
        "attempt": request["attempt"],
        "latency_ms": round(latency_ms, 3),
        "usage": _usage(usage) if result_version == RESULT_VERSION else _usage_v2(usage),
        "raw_provider_status": raw_provider_status,
        "parse_status": parse_status,
        "validation_status": validation_status,
        "structured_output": structured_output,
        "error_type": error_type,
        "error_message": error_message,
        "tool_use_detected": tool_use_detected,
    }


class ScriptedModelAdapter(ModelAdapter):
    """Offline adapter for deterministic tests and sanitized fixtures."""

    def __init__(
        self,
        responses: list[dict[str, Any] | str | Exception] | Callable[[dict[str, Any]], Any],
        model_id: str = "scripted-fixture",
    ) -> None:
        self._responses = responses
        self._position = 0
        self._info = ModelAdapterInfo("offline", "scripted-v1", model_id)

    @property
    def info(self) -> ModelAdapterInfo:
        return self._info

    def complete_structured(self, request: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter_ns()
        if callable(self._responses):
            response = self._responses(request)
        else:
            if self._position >= len(self._responses):
                response = RuntimeError("scripted response exhausted")
            else:
                response = self._responses[self._position]
                self._position += 1
        latency = (time.perf_counter_ns() - started) / 1_000_000
        if isinstance(response, Exception):
            return model_result(
                self.info, request, latency_ms=latency, provider_response_id=None,
                raw_provider_status="error", parse_status="NOT_ATTEMPTED",
                validation_status="NOT_ATTEMPTED", structured_output=None,
                error_type=type(response).__name__, error_message=str(response),
            )
        if isinstance(response, str):
            try:
                parsed = json.loads(response)
            except json.JSONDecodeError as error:
                return model_result(
                    self.info, request, latency_ms=latency, provider_response_id="scripted",
                    raw_provider_status="completed", parse_status="FAILED",
                    validation_status="NOT_ATTEMPTED", structured_output=None,
                    error_type="JSONDecodeError", error_message=str(error),
                )
        else:
            parsed = response
        return model_result(
            self.info, request, latency_ms=latency, provider_response_id="scripted",
            raw_provider_status="completed", parse_status="PARSED",
            validation_status="PENDING", structured_output=parsed,
        )


class OpenAIResponsesAdapter(ModelAdapter):
    """Standard-library OpenAI Responses API adapter with Structured Outputs."""

    def __init__(
        self,
        model_id: str,
        *,
        api_key: str | None = None,
        endpoint: str = "https://api.openai.com/v1/responses",
        timeout_seconds: int = 120,
    ) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY is required for the OpenAI live adapter")
        self._endpoint = endpoint
        self._timeout = timeout_seconds
        self._info = ModelAdapterInfo("openai", "openai-responses-v2", model_id)

    @property
    def info(self) -> ModelAdapterInfo:
        return self._info

    @staticmethod
    def _output_text(response: dict[str, Any]) -> str | None:
        for item in response.get("output", []):
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    return content.get("text")
        return None

    def complete_structured(self, request: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "model": self.info.model_id,
            "input": [
                {
                    "role": "developer",
                    "content": [{"type": "input_text", "text": request["instructions"]}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": canonical_json(request["input"])}],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "fibreseeker_candidate_proposal",
                    "strict": True,
                    "schema": request["response_schema"],
                }
            },
            "store": False,
        }
        http_request = urllib.request.Request(
            self._endpoint,
            data=canonical_json(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        started = time.perf_counter_ns()
        try:
            with urllib.request.urlopen(http_request, timeout=self._timeout) as response:
                raw = json.loads(response.read().decode("utf-8"))
            latency = (time.perf_counter_ns() - started) / 1_000_000
            text = self._output_text(raw)
            if text is None:
                return model_result(
                    self.info, request, latency_ms=latency,
                    provider_response_id=raw.get("id"),
                    raw_provider_status=str(raw.get("status", "unknown")),
                    parse_status="FAILED", validation_status="NOT_ATTEMPTED",
                    structured_output=None, usage=raw.get("usage"),
                    error_type="MissingOutputText", error_message="provider returned no output_text",
                    result_version=RESULT_VERSION_V2,
                )
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as error:
                return model_result(
                    self.info, request, latency_ms=latency,
                    provider_response_id=raw.get("id"),
                    raw_provider_status=str(raw.get("status", "unknown")),
                    parse_status="FAILED", validation_status="NOT_ATTEMPTED",
                    structured_output=None, usage=raw.get("usage"),
                    error_type="JSONDecodeError", error_message=str(error),
                    result_version=RESULT_VERSION_V2,
                )
            return model_result(
                self.info, request, latency_ms=latency,
                provider_response_id=raw.get("id"),
                raw_provider_status=str(raw.get("status", "unknown")),
                parse_status="PARSED", validation_status="PENDING",
                structured_output=parsed, usage=raw.get("usage"),
                result_version=RESULT_VERSION_V2,
            )
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            latency = (time.perf_counter_ns() - started) / 1_000_000
            status = f"http_{error.code}" if isinstance(error, urllib.error.HTTPError) else "transport_error"
            return model_result(
                self.info, request, latency_ms=latency, provider_response_id=None,
                raw_provider_status=status, parse_status="NOT_ATTEMPTED",
                validation_status="NOT_ATTEMPTED", structured_output=None,
                error_type=type(error).__name__, error_message=str(getattr(error, "reason", error)),
                result_version=RESULT_VERSION_V2,
            )


class CodexExecAdapter(ModelAdapter):
    """Live Codex CLI adapter executed in an ephemeral empty workspace.

    Tool events fail validation. This makes the adapter useful for evaluation
    through an existing local login without granting the model KB filesystem
    retrieval as an alternate evidence path.
    """

    TOOL_EVENT_MARKERS = ("tool", "command", "function_call", "mcp")

    def __init__(
        self,
        model_id: str,
        *,
        executable: str = "codex",
        timeout_seconds: int = 180,
    ) -> None:
        self._executable = executable
        self._timeout = timeout_seconds
        self._info = ModelAdapterInfo("openai", "codex-exec-v2", model_id)

    @property
    def info(self) -> ModelAdapterInfo:
        return self._info

    @staticmethod
    def _events(stdout: str) -> tuple[list[dict[str, Any]], bool, dict[str, Any]]:
        events = []
        tool_use = False
        usage: dict[str, Any] = {}
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            events.append(event)
            event_type = str(event.get("type", "")).casefold()
            item_type = str((event.get("item") or {}).get("type", "")).casefold()
            if any(marker in event_type or marker in item_type for marker in CodexExecAdapter.TOOL_EVENT_MARKERS):
                tool_use = True
            candidate_usage = event.get("usage") or (event.get("turn") or {}).get("usage")
            if isinstance(candidate_usage, dict):
                usage = candidate_usage
        return events, tool_use, usage

    def complete_structured(self, request: dict[str, Any]) -> dict[str, Any]:
        prompt = request["instructions"] + "\n\nINPUT JSON:\n" + canonical_json(request["input"])
        with tempfile.TemporaryDirectory(prefix="fibreseeker-llm-") as directory:
            root = Path(directory)
            schema_path = root / "response.schema.json"
            output_path = root / "last-message.json"
            schema_path.write_text(canonical_json(request["response_schema"]), encoding="utf-8")
            command = [
                self._executable, "exec", "--ignore-user-config", "--ignore-rules",
                "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only",
                "--model", self.info.model_id, "--output-schema", str(schema_path),
                "--output-last-message", str(output_path), "--json", "-",
            ]
            started = time.perf_counter_ns()
            try:
                process = subprocess.run(
                    command, input=prompt, text=True, capture_output=True,
                    cwd=root, timeout=self._timeout, check=False,
                )
                latency = (time.perf_counter_ns() - started) / 1_000_000
            except (subprocess.SubprocessError, OSError) as error:
                latency = (time.perf_counter_ns() - started) / 1_000_000
                return model_result(
                    self.info, request, latency_ms=latency, provider_response_id=None,
                    raw_provider_status="process_error", parse_status="NOT_ATTEMPTED",
                    validation_status="NOT_ATTEMPTED", structured_output=None,
                    error_type=type(error).__name__, error_message=str(error),
                    result_version=RESULT_VERSION_V2,
                )
            events, tool_use, usage = self._events(process.stdout)
            response_id = next(
                (
                    str(event.get("thread_id") or event.get("id"))
                    for event in events
                    if event.get("thread_id") or event.get("id")
                ),
                None,
            )
            if process.returncode != 0:
                return model_result(
                    self.info, request, latency_ms=latency,
                    provider_response_id=response_id,
                    raw_provider_status=f"exit_{process.returncode}",
                    parse_status="NOT_ATTEMPTED", validation_status="NOT_ATTEMPTED",
                    structured_output=None, usage=usage,
                    error_type="CodexExecError",
                    error_message="Codex CLI invocation failed; raw stderr was not retained.",
                    tool_use_detected=tool_use, result_version=RESULT_VERSION_V2,
                )
            try:
                parsed = json.loads(output_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                return model_result(
                    self.info, request, latency_ms=latency,
                    provider_response_id=response_id, raw_provider_status="completed",
                    parse_status="FAILED", validation_status="NOT_ATTEMPTED",
                    structured_output=None, usage=usage,
                    error_type=type(error).__name__, error_message=str(error),
                    tool_use_detected=tool_use, result_version=RESULT_VERSION_V2,
                )
            return model_result(
                self.info, request, latency_ms=latency,
                provider_response_id=response_id, raw_provider_status="completed",
                parse_status="PARSED", validation_status="PENDING",
                structured_output=parsed, usage=usage,
                tool_use_detected=tool_use, result_version=RESULT_VERSION_V2,
            )
