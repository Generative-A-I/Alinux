"""LLM-backed intent parsing for the Alinux shell."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Literal

BUILT_IN_MODELS = {
    "llama-3.3-70b-versatile": {
        "provider": "groq",
        "base_url": "https://api.groq.com/openai/v1",
    },
}


@dataclass(frozen=True)
class AgentAction:
    """The only action contract accepted by the desktop loop."""

    action: Literal["system_command", "launch_app", "respond_to_user"]
    parameter: str
    thought: str = ""

    def __post_init__(self) -> None:
        if self.action not in {"system_command", "launch_app", "respond_to_user"}:
            raise ValueError(f"Unsupported action: {self.action}")
        if not isinstance(self.parameter, str) or len(self.parameter) > 500:
            raise ValueError("Action parameter must be a string of at most 500 characters")
        if not isinstance(self.thought, str) or len(self.thought) > 1000:
            raise ValueError("Action thought must be a string of at most 1000 characters")

    @classmethod
    def model_validate(cls, value: object) -> AgentAction:
        if not isinstance(value, dict):
            raise TypeError("Model response must be a JSON object")
        if set(value) - {"action", "parameter", "thought"}:
            raise ValueError("Model response contains unsupported fields")
        if "action" not in value or "parameter" not in value:
            raise ValueError("Model response must include action and parameter")
        return cls(
            action=value["action"],
            parameter=value["parameter"],
            thought=value.get("thought", ""),
        )

    def model_dump(self) -> dict[str, str]:
        return asdict(self)


SYSTEM_PROMPT = """You are the core brain of Alinux, a minimal Debian 12 Linux desktop using Fluxbox.
Translate the user's request into exactly one safe structured action.
You may use system_command for status, windows, volume up, volume down, or volume mute.
Use launch_app only with terminal, browser, or file manager.
Use respond_to_user for questions, unsupported requests, or requests requiring explanation.
Never invent shell commands, never request arbitrary command execution, and never claim an action succeeded.
Return only valid JSON matching this schema:
{"action":"system_command|launch_app|respond_to_user","parameter":"...","thought":"..."}
For system_command, parameter must be exactly one of: status, windows, volume up, volume down, volume mute.
For launch_app, parameter must be exactly one of: terminal, browser, file manager.
"""

_ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["system_command", "launch_app", "respond_to_user"]},
        "parameter": {"type": "string"},
        "thought": {"type": "string"},
    },
    "required": ["action", "parameter", "thought"],
    "additionalProperties": False,
}


class Agent:
    """Convert natural language into validated actions using an OpenAI-compatible API."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        provider: str | None = None,
        use_default_groq_api: bool = False,
    ) -> None:
        configured_model = model or os.getenv("ALINUX_MODEL")
        if use_default_groq_api:
            provider = "groq"
            configured_model = configured_model or "llama-3.3-70b-versatile"
        self.model = configured_model or "llama3.2:3b"
        model_config = BUILT_IN_MODELS.get(self.model, {})
        self.provider = (provider or os.getenv("ALINUX_PROVIDER") or model_config.get("provider", "openai")).lower()
        self.base_url = base_url or os.getenv("ALINUX_API_BASE_URL") or model_config.get("base_url")
        self.api_key = api_key or os.getenv("ALINUX_API_KEY")
        if self.provider == "groq":
            self.api_key = self.api_key or os.getenv("GROQ_API_KEY")
        self.api_key = self.api_key or os.getenv("OPENAI_API_KEY")
        if self.provider == "groq" and configured_model is None and model is None:
            self.model = "llama-3.3-70b-versatile"
            self.base_url = self.base_url or "https://api.groq.com/openai/v1"
        self._client = None
        self.local = not self.api_key
        if self.local:
            self.provider = "ollama"
            self.model = model or os.getenv("ALINUX_LOCAL_MODEL", "llama3.2:3b")
            self.base_url = os.getenv("ALINUX_LOCAL_API_BASE_URL", "http://127.0.0.1:11434/v1")
        if self.api_key:
            try:
                from openai import OpenAI

                client_options = {"api_key": self.api_key}
                if self.base_url:
                    client_options["base_url"] = self.base_url
                self._client = OpenAI(**client_options)
            except ImportError:
                self._client = None

    def decide(self, user_text: str) -> AgentAction:
        """Return a validated action, falling back safely when the LLM is unavailable."""
        if not user_text.strip():
            return AgentAction(action="respond_to_user", parameter="Please enter a request.")
        try:
            if self.local:
                content = self._local_completion(user_text.strip())
                return AgentAction.model_validate(json.loads(content))
            if self._client is None:
                return AgentAction(
                    action="respond_to_user",
                    parameter="The openai package is not installed. Install it with: pip install 'alinux[openai]'",
                )
            response = self._client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text.strip()},
                ],
            )
            content = response.choices[0].message.content or ""
            return AgentAction.model_validate(json.loads(content))
        except urllib.error.URLError as exc:
            return AgentAction(
                action="respond_to_user",
                parameter=(
                    f"Local model is unavailable: {exc}. Install Ollama, then run "
                    f"'ollama pull {self.model}' and start Ollama."
                ),
            )
        except (json.JSONDecodeError, IndexError, TypeError, ValueError) as exc:
            return AgentAction(
                action="respond_to_user",
                parameter=f"Alinux could not understand the model response safely: {exc}.",
            )
        except Exception as exc:  # noqa: BLE001 - model failures must not stop the shell
            return AgentAction(action="respond_to_user", parameter=f"Alinux model error: {exc}")

    def _local_completion(self, user_text: str) -> str:
        """Call Ollama's native JSON-schema endpoint without extra dependencies."""
        payload = json.dumps(
            {
                "model": self.model,
                "temperature": 0,
                "format": _ACTION_SCHEMA,
                "stream": False,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_text},
                ],
            }
        ).encode("utf-8")
        base_url = self.base_url.rstrip("/").removesuffix("/v1")
        request = urllib.request.Request(
            f"{base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.load(response)
        return result["message"].get("content", "")
