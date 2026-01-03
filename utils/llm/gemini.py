"""
FILE : gemini.py
Google Gemini LLM - Wrapper for Google Gemini API
"""

import os
import warnings
import json
import time
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from functools import cached_property
from .base import BaseLLM

# Try importing Google Gemini SDK
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None
    types = None


# === Core Data Structures ===

@dataclass(frozen=True)
class GeminiLLMConfig:
    """Immutable configuration for Google Gemini client."""
    api_key: str
    model_name: str = "gemini-3-pro-preview"
    thinking_level: Optional[str] = None  # "low", "medium", "high", or None (dynamic)
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls, **overrides) -> 'GeminiLLMConfig':
        """Create config from environment variables with optional overrides."""
        # Try importing dotenv for convenience
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        api_key = overrides.get('api_key') or os.getenv("GOOGLE_GENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "Missing GOOGLE_GENAI_API_KEY or GEMINI_API_KEY. "
                "Set it in environment or pass explicitly."
            )
        
        # Get model name from overrides or use default
        model_name = overrides.get('model_name') or overrides.get('deployment_name') or "gemini-3-pro-preview"
        
        # Extract other parameters
        thinking_level = overrides.get('thinking_level')
        temperature = overrides.get('temperature')
        max_tokens = overrides.get('max_tokens')
        
        # Get any extra params
        extra_params = overrides.get('extra_params', {})
        
        return cls(
            api_key=api_key,
            model_name=model_name,
            thinking_level=thinking_level,
            temperature=temperature,
            max_tokens=max_tokens,
            extra_params=extra_params
        )


# === Main LLM Interface ===

class GeminiLLM(BaseLLM):
    """
    Google Gemini LLM wrapper with clean interface.
    
    Features:
    - Automatic configuration from environment
    - Support for thinking_level parameter (Gemini 3 Pro)
    - Clean error handling
    - Schema support (if available in Gemini API)
    
    Usage:
        # Simple usage with environment variables
        llm = GeminiLLM("gemini-3-pro-preview")
        response = llm.generate("Explain quantum computing")
        
        # With thinking level
        llm = GeminiLLM("gemini-3-pro-preview", thinking_level="low")
        response = llm.generate("Your prompt here")
    """
    
    def __init__(
        self, 
        model_name: Optional[str] = None,
        *,
        config: Optional[GeminiLLMConfig] = None,
        logger = None,
        **config_overrides
    ):
        """
        Initialize with automatic environment config or custom settings.
        
        Args:
            model_name: Gemini model name (e.g., "gemini-3-pro-preview")
            config: Custom GeminiLLMConfig object (optional)
            **config_overrides: Override specific config values
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-genai package not installed. "
                "Install it with: pip install google-genai"
            )
        
        if config is not None:
            # Use provided config
            self.config = config
        else:
            # Auto-configure from environment with overrides
            overrides = config_overrides.copy()
            
            if model_name is not None:
                overrides['model_name'] = model_name
            
            try:
                self.config = GeminiLLMConfig.from_env(**overrides)
            except Exception as e:
                raise
        
        # Store logger
        self._logger = logger
    
    @cached_property
    def client(self) -> 'genai.Client':
        """Lazy-initialized Google Gemini client."""
        return genai.Client(api_key=self.config.api_key)
    
    def generate(
        self,
        prompt: str,
        *,
        variables: Optional[Dict[str, Any]] = None,
        schema: Optional[Union[Dict[str, Any], str]] = None,
        batch_items: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        thinking_level: Optional[str] = None,
        **kwargs
    ) -> Union[str, Dict[str, Any], List[Any]]:
        """
        Generate response from Gemini model.
        
        Args:
            prompt: Input prompt text
            variables: Template variables (not used in Gemini, kept for compatibility)
            schema: Output schema (if supported by Gemini API)
            batch_items: Batch processing (not yet implemented)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            thinking_level: Thinking level for Gemini 3 Pro ("low", "medium", "high", or None for dynamic)
            **kwargs: Additional parameters
        
        Returns:
            Generated text response
        """
        if batch_items is not None:
            # Batch processing not yet implemented for Gemini
            warnings.warn("Batch processing not yet implemented for Gemini. Processing single item.")
        
        # Use provided parameters or fall back to config defaults
        final_temperature = temperature if temperature is not None else self.config.temperature
        final_max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        final_thinking_level = thinking_level if thinking_level is not None else self.config.thinking_level
        
        # Build generation config
        # GenerateContentConfig uses snake_case field names
        generation_config_params = {}
        
        if final_temperature is not None:
            generation_config_params['temperature'] = final_temperature
        
        if final_max_tokens is not None:
            generation_config_params['max_output_tokens'] = final_max_tokens
        
        # Add thinking level for Gemini 3 Pro (if specified and model supports it)
        # Only gemini-3-pro-preview and gemini-3-pro support thinking_level
        # gemini-2.5-pro and other models do NOT support it
        thinking_config = None
        if final_thinking_level is not None:
            # Check if model supports thinking_level (only gemini-3-pro models)
            model_name_lower = self.config.model_name.lower()
            supports_thinking = 'gemini-3' in model_name_lower or 'gpt-3' in model_name_lower
            
            if supports_thinking:
                # Convert string to ThinkingLevel enum
                thinking_level_enum = None
                if hasattr(types, 'ThinkingLevel'):
                    # Map string values to enum
                    level_map = {
                        'low': types.ThinkingLevel.LOW,
                        'medium': types.ThinkingLevel.HIGH,  # Medium maps to HIGH in this SDK
                        'high': types.ThinkingLevel.HIGH,
                    }
                    thinking_level_enum = level_map.get(final_thinking_level.lower(), types.ThinkingLevel.LOW)
                
                if thinking_level_enum is not None:
                    thinking_config = types.ThinkingConfig(thinkingLevel=thinking_level_enum)
                    generation_config_params['thinking_config'] = thinking_config
                    
                    if self._logger:
                        self._logger.info(f"Using thinking_level={final_thinking_level} for {self.config.model_name}")
            else:
                # Model doesn't support thinking_level, skip it
                if self._logger:
                    self._logger.info(f"Model {self.config.model_name} does not support thinking_level, skipping parameter")
        
        try:
            # Build generation config if we have any parameters
            # Use GenerateContentConfig (not GenerationConfig) for client.models.generate_content
            generation_config = None
            if generation_config_params:
                generation_config = types.GenerateContentConfig(**generation_config_params)
            
            # Build request parameters
            request_params = {
                'model': self.config.model_name,
                'contents': prompt,
            }
            
            # Add generation config if we have any parameters (parameter name is 'config', not 'generation_config')
            if generation_config:
                request_params['config'] = generation_config
            
            # Add any extra params from config
            request_params.update(self.config.extra_params)
            
            # Filter out thinking_level from kwargs (it's already in generation_config)
            filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'thinking_level'}
            request_params.update(filtered_kwargs)
            
            # Log request details for debugging
            if self._logger:
                self._logger.info(f"Gemini API call - Model: {self.config.model_name}")
                self._logger.info(f"Gemini API call - Prompt length: {len(prompt)} chars")
                self._logger.info(f"Gemini API call - Config params: {list(generation_config_params.keys()) if generation_config_params else 'None'}")
            
            # Call Gemini API using client.models.generate_content with retry logic
            max_retries = 3
            retry_delay = 1  # Start with 1 second
            
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(**request_params)
                    break  # Success, exit retry loop
                except Exception as e:
                    error_str = str(e).lower()
                    
                    # Check if it's a rate limit error (429)
                    if '429' in error_str or 'resource_exhausted' in error_str or 'quota' in error_str:
                        if attempt < max_retries - 1:
                            # Extract retry delay from error if available
                            retry_delay_seconds = retry_delay
                            
                            # Try to extract retry delay from error message
                            if 'retry in' in error_str or 'retrydelay' in error_str:
                                try:
                                    # Look for "retry in X.Xs" pattern
                                    import re
                                    match = re.search(r'retry in ([\d.]+)s?', error_str, re.IGNORECASE)
                                    if match:
                                        retry_delay_seconds = float(match.group(1)) + 1  # Add 1 second buffer
                                except:
                                    pass
                            
                            if self._logger:
                                self._logger.warning(f"Gemini rate limit exceeded (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay_seconds:.1f}s before retry...")
                            
                            time.sleep(retry_delay_seconds)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        else:
                            # Last attempt failed
                            raise
                    else:
                        # Not a rate limit error, re-raise immediately
                        raise
            
            # Log response details for debugging
            if self._logger:
                self._logger.info(f"Gemini API response type: {type(response)}")
                self._logger.info(f"Gemini API response attributes: {[attr for attr in dir(response) if not attr.startswith('_')][:10]}")
            
            # Extract text from response
            extracted_text = None
            
            # Method 1: Try direct .text property (newer SDK versions)
            # In google-genai SDK, response.text is a property that extracts text from candidates
            # This is the same method that works in emulator.py
            try:
                if hasattr(response, 'text'):
                    # Access response.text directly (it's a property that does the extraction)
                    try:
                        text_value = response.text
                        # Log what we got
                        if self._logger:
                            self._logger.info(f"   response.text type: {type(text_value)}, value: '{text_value[:50] if text_value else 'None/Empty'}...'")
                        
                        # response.text might return None or empty string if response was blocked/truncated
                        if text_value is not None and text_value:
                            extracted_text = str(text_value).strip()
                            if extracted_text and self._logger:
                                self._logger.info(f"✅ Gemini response extracted via response.text property: {len(extracted_text)} chars")
                        elif self._logger:
                            self._logger.warning(f"   ⚠️  response.text returned empty/None: '{text_value}' - checking finish_reason...")
                    except AttributeError as e:
                        if self._logger:
                            self._logger.debug(f"   AttributeError accessing response.text: {e}")
                        # If response.text doesn't exist as property, try getattr
                        text_value = getattr(response, 'text', None)
                        if text_value and not callable(text_value):
                            extracted_text = str(text_value).strip()
                            if extracted_text and self._logger:
                                self._logger.info(f"✅ Gemini response extracted via getattr(response, 'text'): {len(extracted_text)} chars")
            except Exception as e:
                if self._logger:
                    self._logger.debug(f"Method 1 (response.text) failed: {e}")
            
            # Method 2: Access via candidates[0].content.parts (standard method)
            if not extracted_text and hasattr(response, 'candidates') and response.candidates:
                try:
                    candidate = response.candidates[0]
                    
                    # Log candidate details for debugging
                    if self._logger:
                        finish_reason = getattr(candidate, 'finish_reason', None)
                        self._logger.info(f"   Candidate finish_reason: {finish_reason}")
                        self._logger.info(f"   Candidate has 'content': {hasattr(candidate, 'content')}")
                        # Log all candidate attributes for debugging
                        candidate_attrs = [attr for attr in dir(candidate) if not attr.startswith('_')]
                        self._logger.info(f"   Candidate attributes: {candidate_attrs[:10]}")
                    
                    if hasattr(candidate, 'content') and candidate.content:
                        # First try candidate.content.text directly
                        if hasattr(candidate.content, 'text'):
                            content_text = getattr(candidate.content, 'text', None)
                            if callable(content_text):
                                content_text = content_text()
                            if content_text:
                                extracted_text = str(content_text).strip()
                                if extracted_text and self._logger:
                                    self._logger.info(f"Gemini response extracted via .candidates[0].content.text: {len(extracted_text)} chars")
                        
                        # Then try candidate.content.parts (only if parts is not None)
                        if not extracted_text and hasattr(candidate.content, 'parts'):
                            parts = getattr(candidate.content, 'parts', None)
                            if parts is not None:  # Explicitly check for None, not just truthiness
                                # Extract text from parts
                                text_parts = []
                                for part in parts:
                                    # Try part.text
                                    if hasattr(part, 'text'):
                                        part_text = getattr(part, 'text', None)
                                        if callable(part_text):
                                            part_text = part_text()
                                        if part_text:
                                            text_parts.append(str(part_text))
                                    # Or if part is directly a string/dict
                                    elif isinstance(part, str):
                                        text_parts.append(part)
                                    elif isinstance(part, dict) and 'text' in part:
                                        text_parts.append(str(part['text']))
                                
                                if text_parts:
                                    extracted_text = ''.join(text_parts).strip()
                                    if extracted_text and self._logger:
                                        self._logger.info(f"Gemini response extracted via .candidates[0].content.parts: {len(extracted_text)} chars")
                            elif self._logger:
                                self._logger.warning(f"   candidate.content.parts is None (not a list)")
                except Exception as e:
                    if self._logger:
                        self._logger.debug(f"Method 2 (candidates.content.parts) failed: {e}")
            
            # Method 3: Try accessing via response.text() method (if it's a method)
            if not extracted_text:
                try:
                    if hasattr(response, 'text') and callable(getattr(response, 'text', None)):
                        extracted_text = str(response.text()).strip()
                        if extracted_text and self._logger:
                            self._logger.info(f"✅ Gemini response extracted via .text() method: {len(extracted_text)} chars")
                except Exception as e:
                    if self._logger:
                        self._logger.debug(f"Method 3 (.text() method) failed: {e}")
            
            # Method 4: Try str(response) as fallback (like emulator does)
            if not extracted_text:
                try:
                    response_str = str(response)
                    # Check if str(response) contains actual text (not just object representation)
                    if response_str and len(response_str) > 100 and not response_str.startswith('<'):
                        # If it's a long string and doesn't look like object representation, use it
                        extracted_text = response_str.strip()
                        if self._logger:
                            self._logger.info(f"✅ Gemini response extracted via str(response) fallback: {len(extracted_text)} chars")
                except Exception as e:
                    if self._logger:
                        self._logger.debug(f"Method 4 (str(response)) failed: {e}")
            
            # Fallback: Log detailed error and return empty
            if not extracted_text or not extracted_text.strip():
                if self._logger:
                    self._logger.error(f"❌ Gemini response text extraction FAILED")
                    self._logger.error(f"   Response type: {type(response)}")
                    self._logger.error(f"   Response has 'text' attr: {hasattr(response, 'text')}")
                    self._logger.error(f"   Response has 'candidates' attr: {hasattr(response, 'candidates')}")
                    if hasattr(response, 'candidates') and response.candidates:
                        candidate = response.candidates[0]
                        self._logger.error(f"   Candidate type: {type(candidate)}")
                        self._logger.error(f"   Candidate has 'content': {hasattr(candidate, 'content')}")
                        if hasattr(candidate, 'content'):
                            self._logger.error(f"   Content type: {type(candidate.content)}")
                            self._logger.error(f"   Content has 'parts': {hasattr(candidate.content, 'parts') if candidate.content else False}")
                            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                                self._logger.error(f"   Parts type: {type(candidate.content.parts)}")
                                self._logger.error(f"   Parts length: {len(candidate.content.parts) if hasattr(candidate.content.parts, '__len__') else 'N/A'}")
                                if len(candidate.content.parts) > 0:
                                    first_part = candidate.content.parts[0]
                                    self._logger.error(f"   First part type: {type(first_part)}")
                                    self._logger.error(f"   First part has 'text': {hasattr(first_part, 'text')}")
                                    if hasattr(first_part, 'text'):
                                        self._logger.error(f"   First part.text value: {getattr(first_part, 'text', 'N/A')}")
                # Return empty string instead of object representation
                extracted_text = ""
            
            # Log final extracted text preview
            if self._logger:
                if extracted_text:
                    preview = extracted_text[:500] if len(extracted_text) > 500 else extracted_text
                    self._logger.info(f"Gemini final extracted text preview: {preview}")
                else:
                    self._logger.warning(f"⚠️  Gemini extracted text is EMPTY - this may indicate a problem with the response")
                    # Try one more time with direct inspection
                    try:
                        if hasattr(response, 'candidates') and response.candidates:
                            candidate = response.candidates[0]
                            self._logger.warning(f"   Inspecting candidate: {type(candidate)}")
                            if hasattr(candidate, 'content'):
                                self._logger.warning(f"   Candidate content: {type(candidate.content)}")
                                if hasattr(candidate.content, 'parts'):
                                    self._logger.warning(f"   Content parts: {candidate.content.parts}")
                                    if candidate.content.parts:
                                        self._logger.warning(f"   First part: {candidate.content.parts[0]}")
                                        self._logger.warning(f"   First part type: {type(candidate.content.parts[0])}")
                                        self._logger.warning(f"   First part dir: {[x for x in dir(candidate.content.parts[0]) if not x.startswith('_')][:10]}")
                    except Exception as e:
                        self._logger.warning(f"   Error inspecting response: {e}")
            
            # If extracted text is empty, log warning
            if not extracted_text or not extracted_text.strip():
                if self._logger:
                    self._logger.error(f"❌ CRITICAL: Gemini response text is empty after extraction")
                    self._logger.error(f"   This means the LLM call succeeded but returned no text content")
                    self._logger.error(f"   Response finish_reason might be MAX_TOKENS, SAFETY, or other blocking reason")
            
            return extracted_text if extracted_text else ""
            
        except Exception as e:
            error_msg = f"Error generating response from Gemini: {str(e)}"
            if self._logger:
                self._logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
    def template(
        self,
        template_string: str,
        *,
        schema: Optional[Union[Dict[str, Any], str]] = None,
        **fixed_params
    ):
        """
        Create a reusable template (placeholder for future implementation).
        
        Args:
            template_string: Template string with placeholders
            schema: Output schema
            **fixed_params: Fixed parameters for the template
        
        Returns:
            Template object (to be implemented)
        """
        # Template system not yet implemented for Gemini
        raise NotImplementedError("Template system not yet implemented for Gemini")


# === Convenience Functions ===

def create_llm(model_name: str = "gemini-3-pro-preview", **config_overrides) -> GeminiLLM:
    """Create a Gemini LLM instance."""
    return GeminiLLM(model_name, **config_overrides)


def quick_generate(prompt: str, model_name: str = "gemini-3-pro-preview", **kwargs) -> str:
    """Quick one-shot generation."""
    llm = create_llm(model_name, **kwargs)
    return llm.generate(prompt, **kwargs)


# === Aliases for compatibility ===
Gemini = GeminiLLM

