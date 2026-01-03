"""
FILE : xai.py
xAI SDK wrapper for Grok models
"""

import os
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
    
    @cached_property
    def client(self) -> Client:
        """Lazy-initialized xAI client."""
        return Client(
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
        
        # Create chat and add user message
        # Note: xAI SDK's chat.sample() doesn't accept max_tokens or temperature directly
        # These parameters might need to be set at chat creation or are not supported
        chat = self.client.chat.create(model=self.model_name)
        chat.append(user(prompt))
        
        # Log request
        if self._logger:
            self._logger.info(f"xAI API call - Model: {self.model_name}")
            self._logger.info(f"xAI API call - Prompt length: {len(prompt)} chars")
            if max_tokens:
                self._logger.info(f"xAI API call - max_tokens: {max_tokens} (not supported by xAI SDK, ignoring)")
            if temperature is not None:
                self._logger.info(f"xAI API call - temperature: {temperature} (not supported by xAI SDK, ignoring)")
        
        try:
            # xAI SDK's chat.sample() doesn't accept parameters
            # Parameters like max_tokens and temperature are not supported in the current SDK version
            response = chat.sample()
            
            # Extract content
            content = response.content
            
            # Log response
            if self._logger:
                self._logger.info(f"xAI API response type: {type(response)}")
                if hasattr(response, 'usage'):
                    usage = response.usage
                    if usage:
                        self._logger.info(f"xAI usage - prompt_tokens: {getattr(usage, 'prompt_tokens', 'N/A')}, "
                                        f"completion_tokens: {getattr(usage, 'completion_tokens', 'N/A')}, "
                                        f"total_tokens: {getattr(usage, 'total_tokens', 'N/A')}")
            
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

