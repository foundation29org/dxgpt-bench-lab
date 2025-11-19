"""
FILE : azure.py
AzureLLM v4 - Clean, powerful wrapper for Azure OpenAI API
"""

import os
import warnings
import json
import yaml
import requests
from typing import Dict, Any, Optional, Union, Callable, List
from dataclasses import dataclass, field
from functools import cached_property
from openai import AzureOpenAI
from .base import BaseLLM


# === Core Data Structures ===

@dataclass(frozen=True)
class LLMConfig:
    """Immutable configuration for Azure OpenAI client."""
    endpoint: str
    api_key: str
    api_version: str = "2024-02-15-preview"
    deployment_name: Optional[str] = None
    temperature: Optional[float] = None
    reasoning_effort: Optional[str] = None  # For O3 models: "low", "medium", "high"
    validate_schema: bool = False
    extra_params: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_env(cls, **overrides) -> 'LLMConfig':
        """Create config from environment variables with optional overrides."""
        # Try importing dotenv for convenience
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
      
        
        endpoint = overrides.get('endpoint') or os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = overrides.get('api_key') or os.getenv("AZURE_OPENAI_API_KEY")

        if not endpoint or not api_key:

            raise ValueError(
                "Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY. "
                "Set them in environment or pass explicitly."
            )
        
        api_version = overrides.get('api_version', os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"))
        
        # Filter out standard keys from overrides - now including reasoning_effort
        filtered_overrides = {k: v for k, v in overrides.items() if k not in ('endpoint', 'api_key', 'api_version')}
        
        config = cls(
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            **filtered_overrides
        )
        
        return config


@dataclass(frozen=True)
class Schema:
    """Immutable schema wrapper with Azure OpenAI optimizations."""
    data: Dict[str, Any]
    
    @classmethod
    def load(cls, source: Union[Dict[str, Any], str]) -> 'Schema':
        """Load schema from dict or YAML file."""
        if isinstance(source, dict):
            data = source.copy()
        else:
            if not os.path.exists(source):
                raise FileNotFoundError(f"Schema file not found: {source}")
            
            with open(source, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        
        return cls(cls._optimize_for_azure(data))
    
    @staticmethod
    def _optimize_for_azure(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Apply Azure OpenAI schema requirements recursively."""
        def optimize_recursive(obj):
            if isinstance(obj, dict):
                optimized = {}
                for key, value in obj.items():
                    optimized[key] = optimize_recursive(value)
                
                # If this is a schema object with type "object"
                if optimized.get("type") == "object":
                    # Azure requires additionalProperties: false for strict mode
                    if "additionalProperties" not in optimized:
                        optimized["additionalProperties"] = False
                    
                    # Azure requires all properties to be required for strict mode
                    if "required" not in optimized and "properties" in optimized:
                        optimized["required"] = list(optimized["properties"].keys())
                
                return optimized
            elif isinstance(obj, list):
                return [optimize_recursive(item) for item in obj]
            else:
                return obj
        
        return optimize_recursive(schema)
    
    def validate_if_enabled(self, enabled: bool) -> None:
        """Validate schema structure if validation is enabled."""
        if not enabled:
            return
            
        try:
            import jsonschema
            jsonschema.Draft7Validator.check_schema(self.data)
        except ImportError:
            warnings.warn("jsonschema not installed. Install for schema validation.", UserWarning)
        except Exception as e:
            raise ValueError(f"Invalid JSON schema: {e}")
    
    @property
    def azure_format(self) -> Dict[str, Any]:
        """Format for Azure OpenAI structured output."""
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "structured_output",
                "schema": self.data,
                "strict": True
            }
        }


# === Batch Processing Support ===

class BatchProcessor:
    """Handles batch item formatting for prompts."""
    
    @staticmethod
    def format_batch_items(batch_items: List[Dict[str, Any]]) -> str:
        """Convert batch items to clean JSON format for prompt inclusion."""
        return json.dumps(batch_items, indent=2, ensure_ascii=False)
    
    @staticmethod
    def wrap_schema_for_batch(original_schema: Optional[Schema]) -> Schema:
        """Wrap a schema to handle batch responses."""
        if original_schema is None:
            # If no schema, create a simple array schema wrapped in object
            batch_schema = {
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["results"],
                "additionalProperties": False
            }
        else:
            # Wrap the original schema in an array inside an object
            batch_schema = {
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": original_schema.data
                    }
                },
                "required": ["results"],
                "additionalProperties": False
            }
        
        return Schema.load(batch_schema)


# === Request Building ===

class RequestBuilder:
    """Builds Azure OpenAI API requests with clean composition."""
    
    def __init__(self, config: LLMConfig, is_o3_model: bool = False):
        self.config = config
        self.batch_processor = BatchProcessor()
        self.is_o3_model = is_o3_model
        # Detect GPT-5 models which require max_completion_tokens
        deployment_name = config.deployment_name or ""
        self.is_gpt5_model = 'gpt-5' in deployment_name.lower() or 'gpt5' in deployment_name.lower()
    
    def build(
        self,
        prompt: str,
        schema: Optional[Schema] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        batch_items: Optional[List[Dict[str, Any]]] = None,
        reasoning_effort: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build complete request parameters."""
        # Handle batch processing
        if batch_items is not None:
            batch_json = self.batch_processor.format_batch_items(batch_items)
            prompt = f"{prompt}\n\nProcess the following items:\n{batch_json}\n\nReturn the results in a JSON object with a 'results' array containing the processed items."
            
            # Wrap schema for batch response
            if schema is not None:
                schema = self.batch_processor.wrap_schema_for_batch(schema)
            else:
                # Even without schema, we need structured output for batch
                schema = self.batch_processor.wrap_schema_for_batch(None)
        
        # Check if it's an o3 model and use special format
        if self.is_o3_model:
            # Use reasoning_effort from parameter, fallback to config, then default to "low"
            final_reasoning_effort = reasoning_effort or self.config.reasoning_effort or "low"
            
            # Build o3-specific request format for chat completions endpoint
            request = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "reasoning_effort": final_reasoning_effort
            }
            
            # Handle schema-based output
            if schema is not None:
                request["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "structured_output",
                        "schema": schema.data,
                        "strict": True
                    }
                }
            else:
                # o3-images specifically requires response_format to be present
                # even when no structured output is desired. Add a minimal text format.
                deployment_name = self.config.deployment_name or ""
                if "images" in deployment_name.lower():
                    request["response_format"] = {"type": "text"}
            
            # Add optional parameters for o3
            if max_tokens is not None:
                # GPT-5 models require max_completion_tokens instead of max_tokens
                if self.is_gpt5_model:
                    request["max_completion_tokens"] = max_tokens
                else:
                    request["max_tokens"] = max_tokens
        else:
            # Standard request format for non-o3 models
            request = {
                "model": self.config.deployment_name,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            # Add optional parameters
            final_temp = temperature if temperature is not None else self.config.temperature
            if final_temp is not None and not self.is_gpt5_model:
                # GPT-5 models only support temperature=1 (default), so we skip it
                request["temperature"] = final_temp
                
            if max_tokens is not None:
                # GPT-5 models require max_completion_tokens instead of max_tokens
                if self.is_gpt5_model:
                    request["max_completion_tokens"] = max_tokens
                else:
                    request["max_tokens"] = max_tokens
                
            if schema is not None:
                request["response_format"] = schema.azure_format
        
        return request


# === Response Processing ===

class ResponseProcessor:
    """Handles response parsing and error recovery."""
    
    @staticmethod
    def process(response, expect_json: bool = False, is_batch: bool = False, logger=None) -> Union[str, Dict[str, Any], List[Any]]:
        """Process API response with graceful JSON parsing."""
        
        content = response.choices[0].message.content
        
        # Extract and log token usage and reasoning details
        usage = getattr(response, 'usage', None)
        finish_reason = response.choices[0].finish_reason
        
        if usage:
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            
            # Extract reasoning tokens if available (GPT-5 specific)
            reasoning_tokens = 0
            if hasattr(usage, 'completion_tokens_details') and usage.completion_tokens_details:
                reasoning_tokens = getattr(usage.completion_tokens_details, 'reasoning_tokens', 0)
            
            # Log token usage info
            token_info = f"TOKENS: prompt={prompt_tokens}, completion={completion_tokens}"
            if reasoning_tokens > 0:
                final_response_tokens = completion_tokens - reasoning_tokens
                token_info += f" (reasoning={reasoning_tokens}, response={final_response_tokens})"
            token_info += f", total={total_tokens}, finish_reason={finish_reason}"
            
            # Log to both console and logger
            print(token_info)
            if logger:
                logger.info(token_info)
            
            # Log reasoning content if available (for debugging)
            if reasoning_tokens > 0 and hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'reasoning'):
                    reasoning_content = getattr(choice.message, 'reasoning', None)
                    if reasoning_content:
                        reasoning_msg = f"REASONING: {reasoning_content[:200]}..." if len(reasoning_content) > 200 else f"REASONING: {reasoning_content}"
                        print(reasoning_msg)
                        if logger:
                            logger.info(reasoning_msg)
        
        # Handle GPT-5 cases where content might be None or empty string
        if content is None or content == '':
            message = response.choices[0].message
            if hasattr(message, 'refusal') and message.refusal:
                refusal_msg = f"WARNING: GPT-5 refused to respond: {message.refusal}"
                print(refusal_msg)
                if logger:
                    logger.warning(refusal_msg)
                return f"[REFUSAL] {message.refusal}"
            else:
                empty_msg = "WARNING: GPT-5 returned empty content - could be safety filters, prompt incompatibility, or token limits"
                print(empty_msg)
                if logger:
                    logger.warning(empty_msg)
                return "[EMPTY_RESPONSE] GPT-5 returned empty content - check prompt format"
        
        if not expect_json:
            return content
            
        try:
            parsed = json.loads(content)
            
            # If it's a batch response, extract the results array
            if is_batch and isinstance(parsed, dict) and "results" in parsed:
                return parsed["results"]
            
            return parsed
        except json.JSONDecodeError:
            warnings.warn(
                "Model returned non-JSON despite schema constraint. Returning raw text.",
                UserWarning
            )
            return content


# === Template System ===

class Template:
    """Callable template with frozen parameters."""
    
    def __init__(
        self,
        template: str,
        llm: 'AzureLLM',
        schema: Optional[Schema] = None,
        **fixed_params
    ):
        self.template = template
        self.llm = llm
        self.schema = schema
        self.fixed_params = fixed_params
    
    def __call__(self, **variables) -> Union[str, Dict[str, Any], List[Any]]:
        """Execute template with provided variables."""
        return self.llm.generate(
            self.template,
            variables=variables,
            schema=self.schema,
            **self.fixed_params
        )


# === Main LLM Interface ===

class AzureLLM(BaseLLM):
    """
    Elegant Azure OpenAI wrapper with genius-level abstractions.
    
    Features:
    - Immutable configuration
    - Clean schema handling
    - Powerful template system
    - Batch processing support
    - Graceful error handling
    - Maximum readability
    
    Usage:
        # Simple usage with environment variables
        llm = AzureLLM("gpt-4o")
        
        # Custom config
        llm = AzureLLM("gpt-4o", temperature=0.7)
        
        # Full control
        config = LLMConfig.from_env(deployment_name="gpt-4o")
        llm = AzureLLM(config=config)
        
        # Batch processing
        items = [{"id": 1, "text": "Hello"}, {"id": 2, "text": "World"}]
        results = llm.generate("Translate to Spanish", batch_items=items)
    """
    
    def __init__(
        self, 
        deployment_name: Optional[str] = None,
        *,
        config: Optional[LLMConfig] = None,
        logger = None,
        **config_overrides
    ):
        """
        Initialize with automatic environment config or custom settings.
        
        Args:
            deployment_name: Azure deployment name (e.g., "gpt-4o")
            config: Custom LLMConfig object (optional)
            **config_overrides: Override specific config values
        """
        
        if config is not None:
            # Use provided config
            self.config = config
        else:
            # Auto-configure from environment with overrides
            overrides = config_overrides.copy()
            
            if deployment_name is not None:
                overrides['deployment_name'] = deployment_name
                
            try:
                self.config = LLMConfig.from_env(**overrides)
            except Exception as e:
                raise
        
        # Store the original deployment name to detect o3 models
        self._original_deployment_name = deployment_name
        self._is_o3_model = deployment_name and 'o3' in deployment_name.lower()
        
        # Store logger for processor
        self._logger = logger
        
        self._request_builder = RequestBuilder(self.config, self._is_o3_model)
        self._processor = ResponseProcessor()
    
    @cached_property
    def client(self) -> AzureOpenAI:
        """Lazy-initialized Azure OpenAI client."""
        return AzureOpenAI(
            api_key=self.config.api_key,
            api_version=self.config.api_version,
            azure_endpoint=self.config.endpoint,
            **self.config.extra_params
        )
    
    def generate(
        self,
        prompt: str,
        *,
        variables: Optional[Dict[str, Any]] = None,
        schema: Optional[Union[Dict[str, Any], str, Schema]] = None,
        batch_items: Optional[List[Dict[str, Any]]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        reasoning_effort: Optional[str] = None,
        # Backward compatibility parameters
        prompt_vars: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Union[Dict[str, Any], str, Schema]] = None
    ) -> Union[str, Dict[str, Any], List[Any]]:
        """
        Generate response with optional structured output and batch processing.
        
        Args:
            prompt: Text with optional {placeholder} variables
            variables: Values to substitute in prompt (or use prompt_vars for backward compatibility)
            schema: Output schema (dict, file path, or Schema object) (or use output_schema for backward compatibility)
            batch_items: List of dicts to process in batch
            max_tokens: Token limit
            temperature: Response randomness
            reasoning_effort: Effort level for O3 models ("low", "medium", "high")
            
        Returns:
            String for text output, dict for structured output, list for batch output
        """
        if self._is_o3_model:
            final_reasoning_effort = reasoning_effort or self.config.reasoning_effort or "low"
        
        # Handle backward compatibility
        if prompt_vars is not None and variables is None:
            variables = prompt_vars
        elif prompt_vars is not None and variables is not None:
            raise ValueError("Cannot specify both 'variables' and 'prompt_vars'. Use 'variables'.")
        
        if output_schema is not None and schema is None:
            schema = output_schema
        elif output_schema is not None and schema is not None:
            raise ValueError("Cannot specify both 'schema' and 'output_schema'. Use 'schema'.")
        
        # Substitute variables in prompt
        if variables:
            try:
                prompt = prompt.format_map(variables)
            except KeyError as e:
                raise KeyError(f"Missing template variable: {e}")
        
        # Handle schema
        schema_obj = None
        if schema is not None:
            schema_obj = schema if isinstance(schema, Schema) else Schema.load(schema)
            schema_obj.validate_if_enabled(self.config.validate_schema)
        
        # Build and execute request
        request = self._request_builder.build(
            prompt, 
            schema_obj, 
            max_tokens, 
            temperature,
            batch_items,
            reasoning_effort
        )
        
        # Different handling for O3 models vs standard models
        if self._is_o3_model:
            
            # Build the full endpoint URL for O3 (use specific API version for O3 models)
            o3_api_version = "2024-12-01-preview"  # O3 models require newer API version
            endpoint_url = f"{self.config.endpoint.rstrip('/')}/openai/deployments/{self.config.deployment_name}/chat/completions?api-version={o3_api_version}"
            
            headers = {
                "Content-Type": "application/json",
                "api-key": self.config.api_key
            }
            
            try:
                http_response = requests.post(
                    endpoint_url, 
                    headers=headers, 
                    json=request,
                    timeout=300  # 5 minutes timeout for O3
                )
                
                # Better error handling for O3 debugging
                if http_response.status_code != 200:
                    error_detail = ""
                    try:
                        error_data = http_response.json()
                        error_detail = f" - Error details: {error_data}"
                    except:
                        error_detail = f" - Response text: {http_response.text}"
                    
                    raise Exception(f"O3 API request failed: {http_response.status_code} {http_response.reason}{error_detail}")
                
                response_data = http_response.json()
                
                # Extract content from O3 response using standard chat completions format
                content = ''
                
                if 'choices' in response_data and len(response_data['choices']) > 0:
                    # Standard chat completions response format
                    choice = response_data['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        content = choice['message']['content']
                else:
                    # Fallback - try to extract from any available content field
                    content = str(response_data)
            
                
            except requests.exceptions.RequestException as e:
                if hasattr(e, 'response') and e.response is not None:
                    error_detail = f"Status: {e.response.status_code}, Response: {e.response.text}"
                    raise Exception(f"O3 API request failed: {error_detail}")
                else:
                    raise Exception(f"O3 API request failed: {str(e)}")
            
            # Process the content for O3
            expect_json = schema_obj is not None or batch_items is not None
            is_batch = batch_items is not None
            
            if not expect_json:
                result = content
            else:
                try:
                    parsed = json.loads(content)
                    if is_batch and isinstance(parsed, dict) and "results" in parsed:
                        result = parsed["results"]
                    else:
                        result = parsed
                except json.JSONDecodeError:
                    warnings.warn("O3 model returned non-JSON despite schema constraint. Returning raw text.", UserWarning)
                    result = content
        else:
            # Standard model handling using SDK
            response = self.client.chat.completions.create(**request)

            # Process response - expect JSON if schema or batch_items provided
            expect_json = schema_obj is not None or batch_items is not None
            is_batch = batch_items is not None
            # Pass logger to processor if available
            logger = getattr(self, '_logger', None)
            result = self._processor.process(response, expect_json=expect_json, is_batch=is_batch, logger=logger)
        
        return result
    
    def template(
        self,
        template_string: str,
        *,
        schema: Optional[Union[Dict[str, Any], str]] = None,
        **fixed_params
    ) -> Template:
        """
        Create reusable template with frozen parameters.
        
        Args:
            template_string: Prompt template with {variable} placeholders
            schema: Output schema for structured responses
            **fixed_params: Fixed parameters (max_tokens, temperature, etc.)
            
        Returns:
            Callable template object
        """
        schema_obj = Schema.load(schema) if schema is not None else None
        return Template(template_string, self, schema_obj, **fixed_params)


# === Convenience Functions ===

def create_llm(deployment_name: Optional[str] = None, **config_overrides) -> AzureLLM:
    """Create LLM instance with environment config and overrides."""
    return AzureLLM(deployment_name, **config_overrides)


def quick_generate(prompt: str, deployment_name: str = "gpt-4o", **kwargs) -> Union[str, Dict[str, Any], List[Any]]:
    """One-shot generation with automatic config."""
    llm = create_llm(deployment_name)
    return llm.generate(prompt, **kwargs)


# === Clean Alias ===

# Clean alias for even more intuitive usage
Azure = AzureLLM
