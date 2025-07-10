# LLM Utils

A unified Python interface for multiple Large Language Model providers. Seamlessly switch between Azure OpenAI and Hugging Face endpoints with identical code, featuring structured output, templates, and batch processing.

## Overview

This library provides a consistent, provider-agnostic interface for interacting with different LLM services. Whether you're using Azure OpenAI's enterprise-grade models or custom Hugging Face endpoints, your code remains the same.

## Key Features

- **Multi-Provider Support**: Azure OpenAI and Hugging Face with identical APIs
- **Structured Output**: JSON schema validation and enforcement
- **Template System**: Reusable prompts with variable substitution
- **Batch Processing**: Efficient multi-item processing in single calls
- **O3 Model Support**: Special handling for OpenAI O3 models with reasoning effort control
- **Type Safety**: Comprehensive type hints throughout
- **Automatic Configuration**: Zero-config setup from environment variables

## Installation

```bash
# Core dependencies
pip install python-dotenv pyyaml

# For Azure OpenAI
pip install openai

# For Hugging Face
pip install requests

# Optional: For schema validation
pip install jsonschema
```

## Quick Start

### Azure OpenAI

```python
from utils.llm import Azure

# Automatic configuration from environment
llm = Azure("gpt-4o")
response = llm.generate("Explain quantum computing in simple terms")
print(response)
```

### Hugging Face

```python
from utils.llm import HuggingLLM

# Uses JONSNOW_ENDPOINT_URL from environment
llm = HuggingLLM("jonsnow")
response = llm.generate("What are the symptoms of influenza?")
print(response)
```

### Provider-Agnostic Usage

```python
# Switch providers by changing import only
from utils.llm import Azure as LLM  # or HuggingLLM as LLM

llm = LLM("model-name")
response = llm.generate("Your prompt here")
```

## Configuration

### Environment Variables

Create a `.env` file in your project root:

#### Azure OpenAI
```env
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

#### Hugging Face
```env
HF_TOKEN=your-hugging-face-token

# Model endpoints - pattern: {MODEL}_ENDPOINT_URL
JONSNOW_ENDPOINT_URL=https://your-jonsnow-endpoint.hf.space
MISTRAL_ENDPOINT_URL=https://your-mistral-endpoint.hf.space
LLAMA_ENDPOINT_URL=https://your-llama-endpoint.hf.space
```

### Programmatic Configuration

```python
from utils.llm import LLMConfig, AzureLLM

config = LLMConfig(
    endpoint="https://my-resource.openai.azure.com/",
    api_key="my-api-key",
    deployment_name="gpt-4o",
    temperature=0.7
)

llm = AzureLLM(config=config)
```

## Core Concepts

### 1. Structured Output

Ensure consistent response formats using JSON schemas:

```python
schema = {
    "type": "object",
    "properties": {
        "diagnosis": {"type": "string"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "symptoms": {
            "type": "array",
            "items": {"type": "string"}
        },
        "severity": {
            "type": "string",
            "enum": ["mild", "moderate", "severe"]
        }
    },
    "required": ["diagnosis", "confidence", "symptoms", "severity"]
}

result = llm.generate(
    "Patient presents with fever, cough, and fatigue for 3 days",
    schema=schema
)

print(f"Diagnosis: {result['diagnosis']} (Confidence: {result['confidence']:.0%})")
print(f"Severity: {result['severity']}")
```

### 2. Templates

Create reusable prompts with variable substitution:

```python
# Define template
medical_analyzer = llm.template(
    """Analyze this patient case:
    Age: {age}
    Symptoms: {symptoms}
    Duration: {duration}
    
    Provide diagnosis and treatment recommendations.""",
    temperature=0.3,
    max_tokens=500
)

# Use multiple times
case1 = medical_analyzer(age=45, symptoms="chest pain", duration="2 hours")
case2 = medical_analyzer(age=22, symptoms="headache", duration="3 days")
```

### 3. Batch Processing

Process multiple items efficiently:

```python
patients = [
    {"id": 1, "symptoms": "fever, cough", "age": 35},
    {"id": 2, "symptoms": "chest pain", "age": 60},
    {"id": 3, "symptoms": "headache, nausea", "age": 28}
]

diagnoses = llm.generate(
    "For each patient, provide a preliminary diagnosis",
    batch_items=patients,
    schema={
        "type": "object",
        "properties": {
            "patient_id": {"type": "integer"},
            "diagnosis": {"type": "string"},
            "urgency": {"type": "string", "enum": ["low", "medium", "high"]}
        }
    }
)

for diagnosis in diagnoses:
    print(f"Patient {diagnosis['patient_id']}: {diagnosis['diagnosis']} ({diagnosis['urgency']} urgency)")
```

### 4. O3 Model Support

Special handling for OpenAI O3 models with reasoning effort control:

```python
# O3 models support reasoning effort parameter
llm = Azure("o3-mini", reasoning_effort="medium")

# Or specify per request
response = llm.generate(
    "Complex medical diagnosis case...",
    reasoning_effort="high"  # low, medium, or high
)
```

## API Reference

### Main Classes

#### `AzureLLM` / `HuggingLLM`

```python
llm = ProviderLLM(
    deployment_name: str,
    *,
    config: Optional[LLMConfig] = None,
    reasoning_effort: Optional[str] = None,  # For O3 models
    **config_overrides
)
```

#### `generate()` Method

```python
response = llm.generate(
    prompt: str,
    *,
    variables: Optional[Dict[str, Any]] = None,
    schema: Optional[Union[Dict[str, Any], str]] = None,
    batch_items: Optional[List[Dict[str, Any]]] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    reasoning_effort: Optional[str] = None  # For O3 models
)
```

**Returns**:
- `str`: Plain text response
- `Dict[str, Any]`: Structured response (with schema)
- `List[Any]`: Batch processing results

#### `template()` Method

```python
template = llm.template(
    template_string: str,
    *,
    schema: Optional[Union[Dict[str, Any], str]] = None,
    **fixed_params
)
```

### Utility Functions

#### `quick_generate()`

One-shot generation without instance creation:

```python
from utils.llm import quick_generate

response = quick_generate(
    "What is diabetes?",
    deployment_name="gpt-4o"
)
```

## Advanced Examples

### Medical Report Analysis

```python
from utils.llm import Azure

llm = Azure("gpt-4o")

# Create specialized analyzer
report_analyzer = llm.template(
    """Analyze this medical report and extract key information:
    
    {report_text}
    
    Focus on diagnoses, medications, and follow-up requirements.""",
    schema={
        "type": "object",
        "properties": {
            "primary_diagnosis": {"type": "string"},
            "secondary_diagnoses": {
                "type": "array",
                "items": {"type": "string"}
            },
            "medications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "dosage": {"type": "string"},
                        "frequency": {"type": "string"}
                    }
                }
            },
            "follow_up": {
                "type": "object",
                "properties": {
                    "required": {"type": "boolean"},
                    "timeframe": {"type": "string"},
                    "specialist": {"type": "string"}
                }
            }
        }
    },
    temperature=0.1  # Low temperature for accuracy
)

# Analyze report
report = """
Patient diagnosed with Type 2 Diabetes Mellitus with peripheral neuropathy.
Started on Metformin 500mg twice daily and Gabapentin 300mg three times daily.
Blood glucose monitoring recommended. Follow-up with endocrinologist in 3 months.
"""

analysis = report_analyzer(report_text=report)

print(f"Primary Diagnosis: {analysis['primary_diagnosis']}")
print(f"Medications:")
for med in analysis['medications']:
    print(f"  - {med['name']}: {med['dosage']} {med['frequency']}")
```

### Differential Diagnosis System

```python
# Create a differential diagnosis engine
differential_dx = llm.template(
    """Given these symptoms: {symptoms}
    Patient demographics: {demographics}
    
    Provide differential diagnoses ranked by likelihood.""",
    schema={
        "type": "object",
        "properties": {
            "diagnoses": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "condition": {"type": "string"},
                        "icd10_code": {"type": "string"},
                        "likelihood": {"type": "number", "minimum": 0, "maximum": 1},
                        "key_indicators": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "tests_needed": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                }
            }
        }
    }
)

# Use for diagnosis
result = differential_dx(
    symptoms="sudden chest pain, shortness of breath, sweating",
    demographics="55-year-old male, smoker, hypertensive"
)

for dx in result['diagnoses']:
    print(f"\n{dx['condition']} (ICD-10: {dx['icd10_code']})")
    print(f"Likelihood: {dx['likelihood']:.0%}")
    print(f"Key indicators: {', '.join(dx['key_indicators'])}")
    print(f"Tests needed: {', '.join(dx['tests_needed'])}")
```

### Batch Medical Coding

```python
# Process multiple medical records for coding
records = [
    {
        "id": "R001",
        "text": "Patient treated for acute bronchitis with antibiotics"
    },
    {
        "id": "R002",
        "text": "Type 2 diabetes with diabetic retinopathy"
    },
    {
        "id": "R003",
        "text": "Hypertension, well-controlled on medication"
    }
]

coding_schema = {
    "type": "object",
    "properties": {
        "record_id": {"type": "string"},
        "primary_code": {"type": "string"},
        "additional_codes": {
            "type": "array",
            "items": {"type": "string"}
        },
        "procedure_codes": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}

coded_records = llm.generate(
    "Assign appropriate ICD-10 codes to each medical record",
    batch_items=records,
    schema=coding_schema
)

for record in coded_records:
    print(f"\nRecord {record['record_id']}:")
    print(f"  Primary: {record['primary_code']}")
    if record['additional_codes']:
        print(f"  Additional: {', '.join(record['additional_codes'])}")
```

## Provider-Specific Features

### Azure OpenAI

- **Strict Mode**: Schemas automatically optimized for Azure's requirements
- **O3 Models**: Special support for reasoning effort parameter
- **API Versions**: Configurable API version for compatibility

### Hugging Face

- **TGI Grammar**: Uses Text Generation Inference grammar constraints
- **Endpoint Pattern**: `{MODEL}_ENDPOINT_URL` environment variable convention
- **Custom Models**: Support for any TGI-compatible endpoint

## Best Practices

1. **Instance Reuse**: Create LLM instances once and reuse them
2. **Template Usage**: Use templates for repeated tasks with consistent formatting
3. **Batch Processing**: Process multiple items together for efficiency
4. **Schema Validation**: Enable validation during development
5. **Error Handling**: Always handle potential API errors gracefully
6. **Cost Control**: Use appropriate `max_tokens` and `temperature` settings

## Error Handling

```python
try:
    response = llm.generate("Complex medical query", schema=complex_schema)
except ValueError as e:
    # Configuration or input errors
    print(f"Configuration error: {e}")
except RuntimeError as e:
    # API errors
    print(f"API error: {e}")
except Exception as e:
    # Unexpected errors
    print(f"Unexpected error: {e}")
```

## Performance Optimization

- **Connection Pooling**: Clients reuse connections automatically
- **Lazy Loading**: Resources initialized only when needed
- **Response Caching**: Templates can implement custom caching
- **Batch Efficiency**: Single API call for multiple items

## Extending the Library

To add a new provider:

1. Create a new module in `utils/llm/`
2. Inherit from `BaseLLM`
3. Implement `generate()` and `template()` methods
4. Update `__init__.py` exports

Example:
```python
from .base import BaseLLM

class CustomLLM(BaseLLM):
    def generate(self, prompt, **kwargs):
        # Implementation
        pass
    
    def template(self, template_string, **kwargs):
        # Implementation
        pass
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Missing environment variables | Check `.env` file and variable names |
| Schema validation errors | Ensure JSON Schema Draft 7 compliance |
| Timeout errors | Increase timeout or reduce batch size |
| Non-JSON responses | Check schema constraints and model capabilities |

### Debug Mode

```python
# Enable schema validation
llm = Azure("gpt-4o", validate_schema=True)

# Check configuration
print(f"Endpoint: {llm.config.endpoint}")
print(f"Model: {llm.config.deployment_name}")
```

## Migration Guide

### From Provider-Specific Code

```python
# Old Azure-specific code
from openai import AzureOpenAI
client = AzureOpenAI(...)
response = client.chat.completions.create(...)

# New unified code
from utils.llm import Azure
llm = Azure("gpt-4o")
response = llm.generate("prompt")
```

### Between Providers

```python
# Simply change the import
# from utils.llm import Azure as LLM
from utils.llm import HuggingLLM as LLM

# All other code remains the same
llm = LLM("model-name")
```

## Contributing

When contributing:
1. Maintain backward compatibility
2. Add comprehensive tests
3. Update documentation
4. Follow existing code patterns
5. Ensure provider parity