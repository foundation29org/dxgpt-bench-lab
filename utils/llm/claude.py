"""
FILE : claude.py
Anthropic Claude wrapper
"""

import os
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

    @cached_property
    def client(self):
        return anthropic.Anthropic(
            api_key=self.config.api_key,
            timeout=self.config.timeout
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

        if self._logger:
            self._logger.info(f"Claude API call — Model: {self.model_name}")
            self._logger.info(f"Claude params: max_tokens={max_tok}")

        # Determine if model supports temperature (Claude 4.x+ deprecated it)
        model_lower = self.model_name.lower()
        supports_temperature = not any(
            f"claude-{v}" in model_lower
            for v in ["opus-4", "sonnet-4", "haiku-4"]
        )

        try:
            create_params = dict(
                model=self.model_name,
                max_tokens=max_tok,
                messages=[{"role": "user", "content": prompt}]
            )
            if supports_temperature:
                create_params["temperature"] = temp

            response = self.client.messages.create(**create_params)

            content = response.content[0].text

            if self._logger:
                usage = response.usage
                self._logger.info(
                    f"Claude usage — input={usage.input_tokens}, "
                    f"output={usage.output_tokens}"
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
