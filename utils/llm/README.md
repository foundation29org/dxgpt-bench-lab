# LLM Utils v4 🚀

**Powerful multi-provider LLM wrapper with unified interface**

A clean, elegant library for interacting with multiple LLM providers (Azure OpenAI and Hugging Face) using a single, consistent API. Features automatic configuration, structured output with JSON schemas, reusable templates, and efficient batch processing.

## 📋 Table of Contents

- [Features](#-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Core Concepts](#-core-concepts)
- [API Reference](#-api-reference)
- [Examples](#-examples)
- [Provider-Specific Details](#-provider-specific-details)
- [Best Practices](#-best-practices)
- [Troubleshooting](#-troubleshooting)
- [Extending](#-extending)

## 🎯 Features

- ✅ **Multi-Provider Support** - Azure OpenAI and Hugging Face with identical interfaces
- ✅ **Automatic Configuration** - Zero-config setup from environment variables
- ✅ **Structured Output** - JSON schema validation and enforcement
- ✅ **Template System** - Reusable prompt templates with variable substitution
- ✅ **Batch Processing** - Efficient processing of multiple items in single API calls
- ✅ **Type Safety** - Full type hints and return type annotations
- ✅ **Error Handling** - Graceful error recovery and informative messages
- ✅ **Backward Compatibility** - Support for legacy parameter names
- ✅ **Lazy Loading** - Clients initialized only when needed

## 📦 Installation

### For Azure OpenAI
```bash
pip install openai python-dotenv pyyaml
```

### For Hugging Face
```bash
pip install requests python-dotenv pyyaml
```

### Optional Dependencies
```bash
pip install jsonschema  # For schema validation
```

## 🚀 Quick Start

### Azure OpenAI
```python
from utils.llm import Azure

# Automatic configuration from environment
llm = Azure("gpt-4o")
response = llm.generate("Explain artificial intelligence in simple terms")
print(response)
```

### Hugging Face
```python
from utils.llm import HuggingLLM

# Uses JONSNOW_ENDPOINT_URL from environment
llm = HuggingLLM("jonsnow")
response = llm.generate("Analyze these symptoms: fever and cough")
print(response)
```

### One-Liner
```python
from utils.llm import quick_generate

# Quick generation with Azure (default)
response = quick_generate("Translate 'Hello' to Spanish", deployment_name="gpt-4o")
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in your project root:

#### Azure OpenAI
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

#### Hugging Face
```bash
HF_TOKEN=your-hugging-face-token

# Model endpoints - uppercase name becomes the model identifier
JONSNOW_ENDPOINT_URL=https://your-jonsnow-endpoint.hf.space
MISTRAL_ENDPOINT_URL=https://your-mistral-endpoint.hf.space
LLAMA_ENDPOINT_URL=https://your-llama-endpoint.hf.space
```

> **Note**: For Hugging Face, the pattern is `{MODEL}_ENDPOINT_URL` where `{MODEL}` is the uppercase version of the deployment name you'll use (e.g., `JONSNOW_ENDPOINT_URL` → `HuggingLLM("jonsnow")`).

### Programmatic Configuration

```python
from utils.llm import LLMConfig, AzureLLM

# Explicit configuration
config = LLMConfig(
    endpoint="https://my-resource.openai.azure.com/",
    api_key="my-api-key",
    deployment_name="gpt-4o",
    temperature=0.7,
    validate_schema=True
)

llm = AzureLLM(config=config)
```

## 🔑 Core Concepts

### 1. Unified Interface

Both providers share the exact same interface:

```python
# Import either provider
from utils.llm import Azure as LLM        # For Azure
# OR
from utils.llm import HuggingLLM as LLM   # For Hugging Face

# Usage is identical
llm = LLM("model-name")
response = llm.generate("Your prompt here")
```

### 2. Structured Output

Use JSON schemas to ensure consistent output format:

```python
schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "key_points": {
            "type": "array",
            "items": {"type": "string"}
        },
        "sentiment": {
            "type": "string",
            "enum": ["positive", "negative", "neutral"]
        }
    },
    "required": ["summary", "key_points", "sentiment"]
}

response = llm.generate(
    "Analyze this product review...",
    schema=schema
)
# response is a dict matching the schema
```

### 3. Templates

Create reusable prompts with variable substitution:

```python
# Define template
translator = llm.template(
    "Translate '{text}' from {source_lang} to {target_lang}",
    temperature=0.3
)

# Use multiple times
result1 = translator(text="Hello", source_lang="English", target_lang="Spanish")
result2 = translator(text="Bonjour", source_lang="French", target_lang="English")
```

### 4. Batch Processing

Process multiple items efficiently:

```python
items = [
    {"id": 1, "text": "Hello world"},
    {"id": 2, "text": "Good morning"},
    {"id": 3, "text": "How are you?"}
]

# Returns list of results
responses = llm.generate(
    "Translate each text to Spanish",
    batch_items=items
)
```

## 📚 API Reference

### Main Classes

#### `AzureLLM` / `HuggingLLM`

```python
llm = ProviderLLM(
    deployment_name: str,
    *,
    config: Optional[LLMConfig] = None,
    **config_overrides
)
```

**Parameters:**
- `deployment_name`: Model/deployment identifier
  - Azure: Deployment name (e.g., "gpt-4o")
  - Hugging Face: Model name matching environment variable pattern (e.g., "jonsnow")
- `config`: Custom LLMConfig object (optional)
- `**config_overrides`: Override specific configuration values

#### `generate()` Method

```python
response = llm.generate(
    prompt: str,
    *,
    variables: Optional[Dict[str, Any]] = None,
    schema: Optional[Union[Dict[str, Any], str]] = None,
    batch_items: Optional[List[Dict[str, Any]]] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
) -> Union[str, Dict[str, Any], List[Any]]
```

**Parameters:**
- `prompt`: Text prompt (may contain `{variable}` placeholders)
- `variables`: Dictionary of values to substitute in prompt
- `schema`: JSON schema for structured output (dict or file path)
- `batch_items`: List of items for batch processing
- `max_tokens`: Maximum tokens in response
- `temperature`: Creativity level (0.0-1.0)

**Returns:**
- `str`: For plain text output
- `Dict[str, Any]`: For structured output with schema
- `List[Any]`: For batch processing results

#### `template()` Method

```python
template = llm.template(
    template_string: str,
    *,
    schema: Optional[Union[Dict[str, Any], str]] = None,
    **fixed_params
) -> Template
```

Creates a reusable template with fixed parameters.

### Helper Functions

#### `quick_generate()`

```python
response = quick_generate(
    prompt: str,
    deployment_name: str = "gpt-4o",  # or "default" for HF
    **kwargs
)
```

One-shot generation for simple use cases.

#### `create_llm()`

```python
llm = create_llm(
    deployment_name: Optional[str] = None,
    **config_overrides
)
```

Factory function for creating LLM instances.

### Data Classes

#### `LLMConfig`

```python
@dataclass(frozen=True)
class LLMConfig:
    endpoint: str
    api_key: str
    api_version: str = "2024-02-15-preview"  # Azure only
    deployment_name: Optional[str] = None
    temperature: Optional[float] = None
    validate_schema: bool = False
    extra_params: Dict[str, Any] = field(default_factory=dict)
```

#### `Schema`

```python
# Load from dict
schema = Schema.load({
    "type": "object",
    "properties": {"name": {"type": "string"}}
})

# Load from YAML file
schema = Schema.load("schema.yaml")
```

## 📝 Examples

### Basic Generation

```python
from utils.llm import Azure

llm = Azure("gpt-4o")

# Simple generation
response = llm.generate("What is machine learning?")

# With parameters
response = llm.generate(
    "Summarize this text in 3 bullet points",
    temperature=0.2,
    max_tokens=150
)

# With variables
response = llm.generate(
    "Hello {name}, welcome to {place}!",
    variables={"name": "Alice", "place": "Wonderland"}
)
```

### Structured Output

```python
# Define output structure
analysis_schema = {
    "type": "object",
    "properties": {
        "sentiment": {
            "type": "string",
            "enum": ["positive", "negative", "neutral"]
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
        },
        "key_phrases": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 5
        }
    },
    "required": ["sentiment", "confidence", "key_phrases"]
}

# Generate structured response
result = llm.generate(
    "Analyze the sentiment of: 'This product exceeded my expectations!'",
    schema=analysis_schema
)

print(f"Sentiment: {result['sentiment']}")
print(f"Confidence: {result['confidence']:.2%}")
print(f"Key phrases: {', '.join(result['key_phrases'])}")
```

### Templates with Schema

```python
# Create a reusable analyzer
product_analyzer = llm.template(
    """Analyze this product review: "{review}"
    
    Extract sentiment, rating, and main points.""",
    schema={
        "type": "object",
        "properties": {
            "sentiment": {"type": "string"},
            "rating": {"type": "integer", "minimum": 1, "maximum": 5},
            "pros": {"type": "array", "items": {"type": "string"}},
            "cons": {"type": "array", "items": {"type": "string"}}
        }
    },
    temperature=0.3
)

# Analyze multiple reviews
reviews = [
    "Amazing product! Fast shipping and great quality.",
    "Disappointed. Broke after one week of use.",
    "Good value for money, but instructions were unclear."
]

for review in reviews:
    analysis = product_analyzer(review=review)
    print(f"Review: {review}")
    print(f"Rating: {'⭐' * analysis['rating']}")
    print(f"Pros: {', '.join(analysis['pros'])}")
    print(f"Cons: {', '.join(analysis['cons'])}\n")
```

### Batch Processing

```python
# Process multiple medical cases
cases = [
    {
        "id": 1,
        "symptoms": "Fever, cough, fatigue",
        "duration": "3 days"
    },
    {
        "id": 2,
        "symptoms": "Headache, nausea, dizziness",
        "duration": "1 week"
    },
    {
        "id": 3,
        "symptoms": "Chest pain, shortness of breath",
        "duration": "2 hours"
    }
]

# Define schema for diagnosis
diagnosis_schema = {
    "type": "object",
    "properties": {
        "case_id": {"type": "integer"},
        "possible_conditions": {
            "type": "array",
            "items": {"type": "string"}
        },
        "urgency": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"]
        },
        "recommended_action": {"type": "string"}
    }
}

# Process all cases in one call
diagnoses = llm.generate(
    """For each case, provide:
    1. Possible conditions
    2. Urgency level
    3. Recommended action""",
    batch_items=cases,
    schema=diagnosis_schema
)

# Display results
for diagnosis in diagnoses:
    print(f"Case {diagnosis['case_id']}:")
    print(f"  Urgency: {diagnosis['urgency'].upper()}")
    print(f"  Possible: {', '.join(diagnosis['possible_conditions'])}")
    print(f"  Action: {diagnosis['recommended_action']}\n")
```

### Complex Pipeline

```python
from utils.llm import Azure

llm = Azure("gpt-4o")

# Step 1: Extract entities
entity_extractor = llm.template(
    "Extract all people, places, and organizations from: {text}",
    schema={
        "type": "object",
        "properties": {
            "people": {"type": "array", "items": {"type": "string"}},
            "places": {"type": "array", "items": {"type": "string"}},
            "organizations": {"type": "array", "items": {"type": "string"}}
        }
    }
)

# Step 2: Generate summary
summarizer = llm.template(
    "Summarize this text focusing on {focus_area}: {text}",
    max_tokens=150,
    temperature=0.3
)

# Process document
document = """
Apple CEO Tim Cook announced yesterday in Cupertino that the company 
will open a new research facility in London. The facility will focus 
on AI research and will be led by Dr. Sarah Johnson, formerly of MIT.
"""

# Extract entities
entities = entity_extractor(text=document)
print("Entities found:")
print(f"  People: {', '.join(entities['people'])}")
print(f"  Places: {', '.join(entities['places'])}")
print(f"  Organizations: {', '.join(entities['organizations'])}")

# Generate summaries with different focus
for focus in ["technology", "business", "personnel"]:
    summary = summarizer(text=document, focus_area=focus)
    print(f"\n{focus.capitalize()} focus: {summary}")
```

## 🔌 Provider-Specific Details

### Azure OpenAI

- **Optimizations**: Schemas automatically optimized for Azure's strict mode
- **Features**: Full support for all Azure OpenAI features
- **Best for**: Production applications requiring high reliability and SLAs

### Hugging Face

- **Endpoint Pattern**: `{MODEL}_ENDPOINT_URL` environment variable
- **Grammar Support**: Uses TGI grammar constraints for structured output
- **Best for**: Custom models, open-source models, and experimentation

### Migration Between Providers

```python
# Switching providers is as simple as changing the import
# from utils.llm import Azure as LLM
from utils.llm import HuggingLLM as LLM

# All code remains the same
llm = LLM("model-name")
response = llm.generate("prompt", schema=schema)
```

## 💡 Best Practices

### 1. Reuse LLM Instances

```python
# ✅ Good: Create once, use many times
llm = Azure("gpt-4o")
for item in items:
    response = llm.generate(f"Process: {item}")

# ❌ Bad: Creating new instance each time
for item in items:
    llm = Azure("gpt-4o")  # Inefficient
    response = llm.generate(f"Process: {item}")
```

### 2. Use Templates for Repeated Tasks

```python
# ✅ Good: Template for consistency
analyzer = llm.template(
    "Analyze {metric} for {company}",
    temperature=0.2
)

# ❌ Bad: Manual string formatting
prompt = f"Analyze {metric} for {company}"  # Less maintainable
```

### 3. Batch Processing for Efficiency

```python
# ✅ Good: Single API call for multiple items
results = llm.generate(
    "Process each item",
    batch_items=items
)

# ❌ Bad: Multiple individual calls
results = []
for item in items:
    result = llm.generate(f"Process {item}")
    results.append(result)
```

### 4. Control Costs with Parameters

```python
# Use appropriate max_tokens
response = llm.generate(
    "Summarize in 50 words",
    max_tokens=100  # Prevent overly long responses
)

# Lower temperature for consistent output
llm = Azure("gpt-4o", temperature=0.1)
```

### 5. Handle Errors Gracefully

```python
try:
    response = llm.generate("Complex prompt", schema=complex_schema)
except RuntimeError as e:
    # Handle API errors
    logger.error(f"LLM API error: {e}")
    response = {"error": "Service unavailable"}
```

## 🔧 Troubleshooting

### Common Issues

#### Missing Environment Variables
```
ValueError: Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY
```
**Solution**: Ensure `.env` file exists with correct variables or pass config explicitly.

#### Model Not Found (Hugging Face)
```
ValueError: Missing MODELNAME_ENDPOINT_URL or HF_TOKEN
```
**Solution**: Model name must match environment variable pattern (e.g., `jonsnow` → `JONSNOW_ENDPOINT_URL`).

#### Schema Validation Errors
```
ValueError: Invalid JSON schema: ...
```
**Solution**: Ensure schema follows JSON Schema Draft 7 specification.

#### Non-JSON Response with Schema
```
UserWarning: Model returned non-JSON despite schema constraint
```
**Note**: This is handled automatically. The library returns raw text when JSON parsing fails.

### Debugging Tips

```python
# Enable schema validation
llm = Azure("gpt-4o", validate_schema=True)

# Check configuration
print(llm.config.endpoint)
print(llm.config.deployment_name)

# Test with simple prompt first
response = llm.generate("Hello")
print(f"Basic test: {response}")
```

## 🔄 Extending

### Adding New Providers

To add support for a new LLM provider:

1. Create a new file (e.g., `anthropic.py`) in `utils/llm/`
2. Inherit from `BaseLLM` and implement required methods:

```python
from .base import BaseLLM

class AnthropicLLM(BaseLLM):
    def generate(self, prompt, **kwargs):
        # Implementation
        pass
    
    def template(self, template_string, **kwargs):
        # Implementation
        pass

# Maintain interface compatibility
Anthropic = AnthropicLLM
```

3. Update `__init__.py` to export your provider:

```python
from .anthropic import Anthropic, AnthropicLLM
```

### Custom Schema Processing

```python
from utils.llm import Schema

class CustomSchema(Schema):
    @staticmethod
    def _optimize_for_provider(schema: Dict[str, Any]) -> Dict[str, Any]:
        # Custom optimization logic
        return schema
```

## 📄 License

This library is part of the dxgpt-latitude-bench-test project.

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Maintain backward compatibility
- Add tests for new features
- Update documentation
- Follow existing code style

---

For more examples and advanced usage, check the `examples/` directory in the repository.