"""
FILE : claude.py
Anthropic Claude wrapper
"""

import os
import re
import threading
import warnings
import json
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from functools import cached_property
from .base import BaseLLM

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None


def _claude_major_version(model_name: str) -> Optional[int]:
    """Return the leading Claude version number, if present in the model id."""
    version_match = re.search(
        r"claude-(?:[a-z]+-)?(\d+)(?:-|$)",
        model_name.lower(),
    )
    return int(version_match.group(1)) if version_match else None


def supports_temperature(model_name: str) -> bool:
    """Return whether the Claude model accepts the temperature parameter."""
    version = _claude_major_version(model_name)
    return version is None or version < 4


def supports_effort(model_name: str) -> bool:
    """Return whether the model accepts output_config.effort."""
    version = _claude_major_version(model_name)
    return version is not None and version >= 5


def extract_text_blocks(response) -> str:
    """Join visible text blocks, skipping thinking/redacted thinking."""
    parts = []
    for block in getattr(response, "content", None) or []:
        if getattr(block, "type", None) != "text":
            continue
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "".join(parts).strip()


@dataclass(frozen=True)
class ClaudeLLMConfig:
    """Immutable configuration for Anthropic client."""
    api_key: str
    timeout: float = 3600.0

    @classmethod
    def from_env(cls, **overrides) -> 'ClaudeLLMConfig':
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        api_key = overrides.get('api_key') or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "Missing ANTHROPIC_API_KEY. Set it in .env or pass explicitly."
            )
        return cls(
            api_key=api_key,
            timeout=overrides.get('timeout', 3600.0)
        )


class ClaudeLLM(BaseLLM):
    """
    Anthropic Claude wrapper.

    Usage:
        llm = ClaudeLLM("claude-opus-4-5")
        response = llm.generate("What is the diagnosis?")
    """

    def __init__(
        self,
        model_name: str,
        *,
        config: Optional[ClaudeLLMConfig] = None,
        logger=None,
        **config_overrides
    ):
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError(
                "Anthropic package not available. Install with: pip install anthropic"
            )

        if config is not None:
            self.config = config
        else:
            self.config = ClaudeLLMConfig.from_env(**config_overrides)

        self.model_name = model_name
        self._logger = logger
        self._thread_local = threading.local()

    @cached_property
    def client(self):
        return anthropic.Anthropic(
            api_key=self.config.api_key,
            timeout=self.config.timeout
        )

    def get_last_usage(self) -> Optional[Dict[str, Any]]:
        """Return token usage from this thread's latest Claude response."""
        return getattr(self._thread_local, "last_usage", None)

    def _record_usage(self, response) -> None:
        usage = getattr(response, "usage", None)
        usage_record = {
            "input_tokens": getattr(usage, "input_tokens", 0) or 0,
            "cached_input_tokens": getattr(
                usage, "cache_read_input_tokens", 0
            ) or 0,
            "output_tokens": getattr(usage, "output_tokens", 0) or 0,
            "reasoning_tokens": 0,
            "total_tokens": (
                (getattr(usage, "input_tokens", 0) or 0)
                + (getattr(usage, "output_tokens", 0) or 0)
            ),
        }
        self._thread_local.last_usage = usage_record
        if self._logger:
            self._logger.info(
                f"Claude usage — input={usage_record['input_tokens']}, "
                f"output={usage_record['output_tokens']}"
            )
            self._logger.info(
                "LLM_USAGE_JSON %s",
                json.dumps(usage_record, sort_keys=True),
            )

    def generate(
        self,
        prompt: str,
        *,
        variables: Optional[Dict[str, Any]] = None,
        schema: Optional[Union[Dict[str, Any], str]] = None,
        batch_items: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Union[str, Dict[str, Any], List[Any]]:

        if batch_items is not None:
            raise NotImplementedError("Batch processing not supported for Claude")

        if variables:
            try:
                prompt = prompt.format_map(variables)
            except KeyError as e:
                raise KeyError(f"Missing template variable: {e}")

        max_tok = max_tokens or 16000
        temp = temperature if temperature is not None else 0.1
        effort = kwargs.pop("reasoning_effort", None) or kwargs.pop("effort", None)

        if self._logger:
            self._logger.info(f"Claude API call — Model: {self.model_name}")
            self._logger.info(f"Claude params: max_tokens={max_tok}")
            if effort:
                self._logger.info(f"Claude params: effort={effort}")

        try:
            create_params = dict(
                model=self.model_name,
                max_tokens=max_tok,
                messages=[{"role": "user", "content": prompt}]
            )
            if supports_temperature(self.model_name):
                create_params["temperature"] = temp
            if effort and supports_effort(self.model_name):
                create_params["output_config"] = {"effort": effort}

            response = self.client.messages.create(**create_params)
            self._record_usage(response)
            content = extract_text_blocks(response)
            if not content:
                block_types = [
                    getattr(block, "type", type(block).__name__)
                    for block in (response.content or [])
                ]
                raise ValueError(
                    f"Claude {self.model_name} returned no text blocks "
                    f"(content types: {block_types})"
                )

            if schema is not None:
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    warnings.warn(
                        "Claude returned non-JSON despite schema. Returning raw text.",
                        UserWarning
                    )
            return content

        except Exception as e:
            if self._logger:
                self._logger.error(f"Claude API call failed: {type(e).__name__}: {e}")
                import traceback
                self._logger.error(traceback.format_exc())
            raise

    def template(self, template_string: str, *, schema=None, **fixed_params):
        def template_func(**kwargs):
            final_params = {**fixed_params, **kwargs}
            return self.generate(template_string.format(**final_params), schema=schema)
        return template_func


def create_llm(model_name: Optional[str] = None, **config_overrides) -> ClaudeLLM:
    if not model_name:
        raise ValueError("model_name is required for Claude")
    return ClaudeLLM(model_name, **config_overrides)


def quick_generate(prompt: str, model_name: str = "claude-opus-4-5", **kwargs) -> str:
    llm = create_llm(model_name)
    return llm.generate(prompt, **kwargs)
