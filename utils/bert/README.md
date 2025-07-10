# BERT Semantic Similarity Service

A sophisticated semantic similarity engine for medical terminology using SapBERT embeddings. This module provides high-performance similarity calculations between medical terms, understanding synonyms and related concepts across different representations.

## Overview

This module leverages SapBERT (Self-Alignment Pretraining for Biomedical Entity Representations), a specialized BERT model trained on biomedical entity linking across multiple languages. It excels at understanding that "myocardial infarction" and "heart attack" refer to the same condition, despite different terminology.

## Key Features

- **Medical-Specific Embeddings**: Powered by SapBERT, specifically trained on UMLS medical terminology
- **Cross-Language Support**: Understands medical terms across multiple languages
- **Batch Processing**: Efficient similarity calculations for multiple term pairs
- **Smart Caching**: Reuses embeddings for repeated terms
- **Automatic Warm-up**: Prepares endpoints for optimal performance
- **Robust Error Handling**: Graceful degradation with informative feedback

## Installation

```bash
# Install dependencies
pip install python-dotenv requests numpy
```

## Configuration

Create a `.env` file in your project root:

```env
SAPBERT_ENDPOINT_URL=https://your-endpoint-id.huggingface.cloud
HF_TOKEN=hf_your_token_with_permissions
```

**Note**: Requires a Hugging Face API token and access to a SapBERT endpoint.

## Quick Start

```python
from utils.bert import calculate_semantic_similarity, warm_up_endpoint

# Warm up endpoint for optimal performance
if warm_up_endpoint():
    # Calculate similarity between two terms
    result = calculate_semantic_similarity("heart attack", "myocardial infarction")
    print(f"Similarity: {result['heart attack']['myocardial infarction']:.3f}")
```

## API Reference

### Core Functions

#### `warm_up_endpoint() -> bool`

Prepares the Hugging Face endpoint for processing. Essential for batch operations.

```python
if warm_up_endpoint():
    print("Endpoint ready for processing")
```

**Returns**: `True` if successful, `False` otherwise

#### `calculate_semantic_similarity(input_a, input_b) -> Dict`

Calculates semantic similarity between medical terms.

```python
# Single term comparison
result = calculate_semantic_similarity("diabetes", "hyperglycemia")

# One-to-many comparison
result = calculate_semantic_similarity("fever", ["influenza", "covid-19", "cold"])

# Many-to-many comparison
result = calculate_semantic_similarity(
    ["headache", "fatigue"], 
    ["migraine", "exhaustion", "anemia"]
)
```

**Parameters**:
- `input_a`: Single term or list of terms
- `input_b`: Single term or list of terms

**Returns**: Nested dictionary with similarity scores (0.0-1.0) or `None` for errors

## Response Structure

```python
{
    "term_a1": {
        "term_b1": 0.95,  # Similarity score (0.0-1.0)
        "term_b2": 0.32,
        "term_b3": None   # Error in calculation
    },
    "term_a2": {
        "term_b1": 0.28,
        "term_b2": 0.87,
        "term_b3": 0.45
    }
}
```

## Score Interpretation

| Score Range | Interpretation |
|-------------|----------------|
| 0.90+ | Near synonyms |
| 0.75-0.90 | Strong semantic relationship |
| 0.50-0.75 | Moderate relationship |
| 0.30-0.50 | Weak relationship |
| 0.15-0.30 | Minimal relationship |
| <0.15 | No apparent relationship |

## Examples

### Basic Usage

```python
from utils.bert import calculate_semantic_similarity

# Compare medical conditions
result = calculate_semantic_similarity("hypertension", "high blood pressure")
score = result['hypertension']['high blood pressure']
print(f"Similarity: {score:.3f}")  # ~0.95
```

### Batch Processing

```python
from utils.bert import warm_up_endpoint, calculate_semantic_similarity

# Essential: warm up before batch processing
if not warm_up_endpoint():
    print("Warning: Endpoint may be slow")

# Process multiple symptom-disease relationships
symptom_disease_pairs = [
    ("chest pain", ["myocardial infarction", "angina", "pneumonia"]),
    ("shortness of breath", ["asthma", "COPD", "heart failure"]),
    ("abdominal pain", ["appendicitis", "gastritis", "kidney stones"])
]

for symptom, diseases in symptom_disease_pairs:
    result = calculate_semantic_similarity(symptom, diseases)
    print(f"\n{symptom}:")
    for disease, score in result[symptom].items():
        if score is not None:
            print(f"  → {disease}: {score:.3f}")
```

### Creating Similarity Matrices

```python
# Build similarity matrix for differential diagnosis
symptoms = ["fever", "cough", "fatigue", "headache"]
conditions = ["influenza", "COVID-19", "common cold", "pneumonia"]

similarity_matrix = calculate_semantic_similarity(symptoms, conditions)

# Display results
for symptom in symptoms:
    print(f"\n{symptom}:")
    for condition in conditions:
        score = similarity_matrix[symptom][condition]
        if score is not None:
            print(f"  {condition}: {score:.3f}")
```

## Error Handling

```python
# Always check warm-up status for batch operations
if not warm_up_endpoint():
    print("Warning: Endpoint unavailable")
    # Implement fallback strategy

result = calculate_semantic_similarity("term1", "term2")

# Check for errors before using scores
score = result.get("term1", {}).get("term2")
if score is None:
    print("Error: Could not calculate similarity")
    # Possible causes:
    # - Endpoint not warmed up
    # - Network connectivity issues
    # - Invalid API credentials
    # - Rate limit exceeded
else:
    print(f"Similarity: {score:.3f}")
```

## Performance Optimization

### Best Practices

1. **Always warm up for batch processing**: Prevents cold start delays
2. **Batch similar operations**: Process multiple comparisons in single calls
3. **Check for None values**: Always validate results before use
4. **Monitor rate limits**: Implement appropriate delays for large batches

### Performance Characteristics

- **Cold start**: 30-60 seconds (without warm-up)
- **Warm endpoint**: 2-3 seconds per request
- **Batch efficiency**: Linear scaling with number of unique terms

## Technical Details

### Architecture

The module consists of several key components:

- **EmbeddingClient**: Manages communication with the SapBERT endpoint
- **EmbeddingProcessor**: Handles CLS token extraction and normalization
- **SimilarityCalculator**: Computes cosine similarity with optimization
- **RequestBuilder**: Formats requests for the Hugging Face API

### Embedding Process

1. Text is tokenized and processed by SapBERT
2. CLS token embeddings are extracted (768-dimensional vectors)
3. Vectors are L2-normalized for cosine similarity
4. Similarity scores are computed via dot product

### Configuration Requirements

- **Environment Variables**:
  - `SAPBERT_ENDPOINT_URL`: Updated from `SAPBERT_API_URL`
  - `HF_TOKEN`: Hugging Face API token
- **Network**: Requires internet access to Hugging Face endpoints
- **Memory**: Minimal (~100MB for typical usage)

## Use Cases

- **Clinical Decision Support**: Find similar conditions for differential diagnosis
- **Medical Coding**: Map between different coding systems (ICD-10, SNOMED)
- **Literature Search**: Find papers about related medical concepts
- **Patient Record Analysis**: Identify similar cases or conditions
- **Drug Discovery**: Find related compounds or conditions

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Endpoint unavailable (503)" | Run `warm_up_endpoint()` first |
| "Network error" | Check internet connection and firewall |
| "Invalid API credentials" | Verify `HF_TOKEN` in `.env` file |
| "Timeout after 120s" | Reduce batch size or increase timeout |

### Debug Output

The module uses concise emoji indicators:
- 🔄 Processing
- ✅ Success
- ⚠️ Warning
- ❌ Error
- ⏱️ Timeout
- 🌐 Network error 