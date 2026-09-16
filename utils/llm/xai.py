"""
FILE : xai.py
xAI SDK wrapper for Grok models
"""

import os
import threading
import warnings
import json
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from functools import cached_property
from .base import BaseLLM

# Try importing xai-sdk
try:
    from xai_sdk import Client
    from xai_sdk.chat import user, system
    XAI_AVAILABLE = True
except ImportError:
    XAI_AVAILABLE = False
    Client = None
    user = None
    system = None


@dataclass(frozen=True)
class XaiLLMConfig:
    """Immutable configuration for xAI client."""
    api_key: str
    timeout: float = 3600.0  # 1 hour default for reasoning models
    model: Optional[str] = None
    
    @classmethod
    def from_env(cls, **overrides) -> 'XaiLLMConfig':
        """Create config from environment variables with optional overrides."""
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        api_key = overrides.get('api_key') or os.getenv("XAI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "Missing XAI_API_KEY. "
                "Set it in environment or pass explicitly."
            )
        
        timeout = overrides.get('timeout', 3600.0)  # Default 1 hour for reasoning models
        model = overrides.get('model') or overrides.get('deployment_name')
        
        return cls(
            api_key=api_key,
            timeout=timeout,
            model=model
        )


class XaiLLM(BaseLLM):
    """
    xAI SDK wrapper for Grok models.
    
    Usage:
        from utils.llm import XaiLLM
        
        llm = XaiLLM("grok-4-1-fast-reasoning")
        response = llm.generate("What is the capital of France?")
    """
    
    def __init__(
        self,
        model_name: str,
        *,
        config: Optional[XaiLLMConfig] = None,
        logger = None,
        **config_overrides
    ):
        """
        Initialize xAI client.
        
        Args:
            model_name: Model name (e.g., "grok-4-1-fast-reasoning", "grok-4-latest")
            config: Custom XaiLLMConfig object (optional)
            **config_overrides: Override specific config values
        """
        if not XAI_AVAILABLE:
            raise RuntimeError(
                "xAI SDK not available. Install it with: pip install xai-sdk"
            )
        
        if config is not None:
            self.config = config
        else:
            overrides = config_overrides.copy()
            overrides['model'] = model_name
            try:
                self.config = XaiLLMConfig.from_env(**overrides)
            except Exception as e:
                raise
        
        self.model_name = model_name
        self._logger = logger
        self._thread_local = threading.local()
    
    @cached_property
    def client(self) -> Client:
        """Lazy-initialized xAI client."""
        return Client(
            api_key=self.config.api_key,
            timeout=self.config.timeout
        )

    def get_last_usage(self) -> Optional[Dict[str, Any]]:
        """Return token usage from this thread's latest xAI response."""
        return getattr(self._thread_local, "last_usage", None)
    
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
        """
        Generate response using xAI SDK.
        
        Args:
            prompt: Text prompt
            variables: Values to substitute in prompt (not used for xAI)
            schema: Output schema (not directly supported, but can parse JSON)
            batch_items: Not supported by xAI SDK
            max_tokens: Token limit
            temperature: Response randomness
            
        Returns:
            String response
        """
        if batch_items is not None:
            raise NotImplementedError("Batch processing not supported by xAI SDK")
        
        # Substitute variables in prompt if provided
        if variables:
            try:
                prompt = prompt.format_map(variables)
            except KeyError as e:
                raise KeyError(f"Missing template variable: {e}")
        
        # Generation controls belong to chat creation in the xAI SDK.
        chat_params: Dict[str, Any] = {"model": self.model_name}
        if max_tokens is not None:
            chat_params["max_tokens"] = max_tokens
        if temperature is not None:
            chat_params["temperature"] = temperature
        reasoning_effort = kwargs.pop("reasoning_effort", None)
        if reasoning_effort is not None:
            chat_params["reasoning_effort"] = reasoning_effort
        chat = self.client.chat.create(**chat_params)
        chat.append(user(prompt))
        
        # Log request
        if self._logger:
            self._logger.info(f"xAI API call - Model: {self.model_name}")
            self._logger.info(f"xAI API call - Prompt length: {len(prompt)} chars")
            if max_tokens:
                self._logger.info(f"xAI API call - max_tokens: {max_tokens}")
            if temperature is not None:
                self._logger.info(f"xAI API call - temperature: {temperature}")
            if reasoning_effort is not None:
                self._logger.info(
                    f"xAI API call - reasoning_effort: {reasoning_effort}"
                )
        
        try:
            response = chat.sample()
            
            # Extract content
            content = response.content
            
            usage = getattr(response, "usage", None)
            usage_record = {
                "input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                "cached_input_tokens": (
                    getattr(usage, "cached_prompt_text_tokens", 0) or 0
                ),
                "output_tokens": getattr(usage, "completion_tokens", 0) or 0,
                "reasoning_tokens": getattr(usage, "reasoning_tokens", 0) or 0,
                "total_tokens": getattr(usage, "total_tokens", 0) or 0,
            }
            self._thread_local.last_usage = usage_record

            # Log response
            if self._logger:
                self._logger.info(f"xAI API response type: {type(response)}")
                self._logger.info(
                    "LLM_USAGE_JSON %s",
                    json.dumps(usage_record, sort_keys=True),
                )
            
            # Handle schema if provided (parse JSON)
            if schema is not None:
                try:
                    parsed = json.loads(content)
                    return parsed
                except json.JSONDecodeError:
                    warnings.warn(
                        "xAI returned non-JSON despite schema constraint. Returning raw text.",
                        UserWarning
                    )
                    return content
            
            return content
            
        except Exception as e:
            if self._logger:
                self._logger.error(f"xAI API call failed: {type(e).__name__}: {str(e)}")
                import traceback
                self._logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    
    def template(
        self,
        template_string: str,
        *,
        schema: Optional[Union[Dict[str, Any], str]] = None,
        **fixed_params
    ):
        """Create reusable template (not fully implemented for xAI)."""
        # Simple template implementation
        def template_func(**kwargs):
            final_params = {**fixed_params, **kwargs}
            return self.generate(
                template_string.format(**final_params),
                schema=schema
            )
        return template_func


def create_llm(model_name: Optional[str] = None, **config_overrides) -> XaiLLM:
    """Create xAI LLM instance."""
    if not model_name:
        raise ValueError("model_name is required for xAI")
    return XaiLLM(model_name, **config_overrides)


def quick_generate(prompt: str, model_name: str = "grok-4-latest", **kwargs) -> str:
    """Quick one-shot generation."""
    llm = create_llm(model_name)
    return llm.generate(prompt, **kwargs)

