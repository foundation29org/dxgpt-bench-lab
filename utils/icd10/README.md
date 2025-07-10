# ICD-10 Taxonomy API

A high-performance Python API for navigating and analyzing the ICD-10 medical classification system. Provides intuitive access to the complete ICD-10 hierarchy with efficient caching and flexible query capabilities.

## Overview

The ICD-10 (International Classification of Diseases, 10th Revision) is the global standard for diagnostic health information. This API provides programmatic access to the entire ICD-10 taxonomy, enabling:

- Fast lookups by code or name
- Hierarchical navigation (parents, children, siblings)
- Flexible search with type filtering
- Efficient batch operations
- Bidirectional code-name conversion

## Key Features

- **Universal Input**: All methods accept both ICD-10 codes and disease names
- **Case Insensitive**: Works seamlessly with any case combination
- **Lazy Loading**: Data loads only when first accessed
- **Smart Caching**: Optimized for repeated operations
- **Type Safety**: Full hierarchical type awareness
- **Flexible Output**: Support for code, name, or combined formats

## Installation

```python
from utils.icd10 import ICD10Taxonomy

# Initialize the taxonomy
t = ICD10Taxonomy()
```

## Quick Start

```python
from utils.icd10 import ICD10Taxonomy

t = ICD10Taxonomy()

# Look up by code
info = t.get('S62')
# {'code': 'S62', 'name': 'Fracture at wrist and hand level', 'type': 'category', ...}

# Look up by name
info = t.get('cholera')
# {'code': 'A00', 'name': 'Cholera', 'type': 'category', ...}

# Find all fracture codes
fractures = t.match('fracture')
print(f"Found {len(fractures)} fracture-related codes")

# Navigate hierarchy
children = t.children('S62', format='name')
parent = t.parent('S62.3', format='both')
```

## API Reference

### Core Information Methods

#### `get(code_or_name) → dict`

Retrieves complete information for any ICD-10 code or disease name.

```python
>>> t.get('S62')
{'code': 'S62', 'name': 'Fracture at wrist and hand level', 
 'type': 'category', 'full_key': 'S62 Fracture at wrist and hand level'}

>>> t.get('cholera')
{'code': 'A00', 'name': 'Cholera', 'type': 'category', 
 'full_key': 'A00 Cholera'}
```

#### `shift(code_or_name) → str`

Converts between codes and names bidirectionally.

```python
>>> t.shift('S62')  # Code → Name
'Fracture at wrist and hand level'

>>> t.shift('Cholera')  # Name → Code
'A00'
```

#### `type(code_or_name) → str`

Returns the hierarchical type of an entry.

```python
>>> t.type('XIX')
'chapter'

>>> t.type('S60-S69')
'range'

>>> t.type('S62')
'category'
```

### Search Functionality

#### `match(query, exact=False, type=None, format='code') → list`

Searches for codes by name with optional filtering.

```python
# Find all codes containing "fracture"
>>> t.match('fracture')[:5]
['K08.53', 'K08.530', 'K08.531', 'K08.539', 'M48.40XA']

# Find only fracture categories
>>> t.match('fracture', type='category', format='both')[:3]
['S02 Fracture of skull and facial bones',
 'S12 Fracture of cervical vertebra and other parts of neck',
 'S22 Fracture of rib(s), sternum and thoracic spine']

# Exact name match
>>> t.match('cholera', exact=True)
['A00']
```

**Parameters**:
- `query`: Search string (case insensitive)
- `exact`: If True, only exact name matches
- `type`: Filter by hierarchy type ('chapter', 'range', 'category', 'block', 'subblock', 'group', 'subgroup')
- `format`: Output format ('code', 'name', 'both')

### Hierarchy Navigation

#### `children(code_or_name, type=None, format='code') → list`

Gets descendants of a code with flexible filtering.

```python
# Get immediate children
>>> t.children('S62', type=0)
['S62.0', 'S62.1', 'S62.2', 'S62.3', 'S62.4', 'S62.5', 'S62.6', 'S62.8', 'S62.9']

# Get all blocks under S62
>>> t.children('S62', type='block')
['S62.0', 'S62.1', 'S62.2', 'S62.3', 'S62.4', 'S62.5', 'S62.6', 'S62.8', 'S62.9']

# Get all descendants
>>> len(t.children('S62'))
2229
```

**Type Parameter Options**:
- `None`: All descendants (default)
- `int`: Depth level (0=immediate children)
- `str`: Specific hierarchy type

#### `parent(code_or_name, format='code') → str`

Gets the immediate parent of a code.

```python
>>> t.parent('S62.3')
'S62'

>>> t.parent('S62.3', format='both')
'S62 Fracture at wrist and hand level'
```

#### `parents(code_or_name, format='code') → list`

Gets all ancestors up to root (bottom-up order).

```python
>>> t.parents('S62.302A')
['S62.302', 'S62.30', 'S62.3', 'S62', 'S60-S69', 'XIX']
```

#### `path(code_or_name, format='code') → list`

Gets the complete path from root to code (top-down order).

```python
>>> t.path('S62.3', format='name')
['Injury, poisoning and certain other consequences of external causes',
 'Injuries to the wrist and hand',
 'Fracture at wrist and hand level',
 'Fracture of other and unspecified metacarpal bone']
```

#### `siblings(code_or_name, format='code') → list`

Gets all siblings of the same type at the same hierarchical level.

```python
>>> t.siblings('S62', format='name')[:3]
['Superficial injury of wrist, hand and fingers',
 'Open wound of wrist, hand and fingers',
 'Dislocation and sprain of joints and ligaments at wrist and hand level']
```

### Complete Analysis

#### `hierarchy(code_or_name) → dict`

Retrieves comprehensive hierarchical information in a single call.

```python
>>> t.hierarchy('S62.3')
{
    'code': 'S62.3',
    'name': 'Fracture of other and unspecified metacarpal bone',
    'type': 'block',
    'full_key': 'S62.3 Fracture of other and unspecified metacarpal bone',
    'parents': {
        'category': {'code': 'S62', 'name': 'Fracture at wrist and hand level'},
        'range': {'code': 'S60-S69', 'name': 'Injuries to the wrist and hand'},
        'chapter': {'code': 'XIX', 'name': 'Injury, poisoning...'}
    },
    'children': {
        'subblock': 10,
        'group': 10,
        'subgroup': 200
    },
    'n_children': 10,
    'n_siblings': 8,
    'path': ['XIX', 'S60-S69', 'S62', 'S62.3']
}
```

### Type-Specific Lists

Methods to retrieve all codes of a specific hierarchical type:

```python
# Get all chapters
>>> t.chapters()
['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', ...]

# Get chapter names
>>> t.chapters(format='name')[:3]
['Certain infectious and parasitic diseases',
 'Neoplasms',
 'Diseases of the blood and blood-forming organs...']

# Count specific types
>>> len(t.categories())  # All 3-character codes
1630

>>> len(t.blocks())      # All 4-character codes
9916
```

Available methods:
- `chapters(format='code')`
- `ranges(format='code')`
- `categories(format='code')`
- `blocks(format='code')`
- `subblocks(format='code')`
- `groups(format='code')`
- `subgroups(format='code')`

## ICD-10 Hierarchy Structure

The ICD-10 system follows a strict hierarchical structure:

1. **Chapter** - Roman numerals (I-XXII)
   - Example: `XIX` - Injury, poisoning and certain other consequences of external causes
   
2. **Range** - Letter-number ranges (A00-A09)
   - Example: `S60-S69` - Injuries to the wrist and hand
   
3. **Category** - 3-character codes (A00)
   - Example: `S62` - Fracture at wrist and hand level
   
4. **Block** - 4-character codes (A00.0)
   - Example: `S62.3` - Fracture of other and unspecified metacarpal bone
   
5. **Subblock** - 5-character codes (A00.00)
   - Example: `S62.30` - Unspecified fracture of other metacarpal bone
   
6. **Group** - 6-character codes (A00.001)
   - Example: `S62.301` - Unspecified fracture of second metacarpal bone
   
7. **Subgroup** - 7+ character codes (A00.001A)
   - Example: `S62.301A` - Unspecified fracture of second metacarpal bone, initial encounter

## Usage Examples

### Finding and Analyzing Diseases

```python
from utils.icd10 import ICD10Taxonomy
t = ICD10Taxonomy()

# Search for diabetes codes
diabetes_codes = t.match('diabetes', type='category')
print(f"Found {len(diabetes_codes)} diabetes categories")

# Analyze a specific diabetes code
info = t.hierarchy('E11')  # Type 2 diabetes mellitus
print(f"Type: {info['type']}")
print(f"Parent chapter: {info['parents']['chapter']['name']}")
print(f"Number of complications: {info['n_children']}")
```

### Building Disease Trees

```python
# Get all infectious diseases
infectious_chapter = t.get('I')
infectious_ranges = t.children('I', type='range', format='both')

for range_code in infectious_ranges[:5]:
    print(f"\n{range_code}")
    categories = t.children(range_code.split()[0], type='category', format='name')
    for cat in categories[:3]:
        print(f"  - {cat}")
```

### Cross-Referencing Conditions

```python
# Find all injury codes for a body part
hand_injuries = t.match('hand', type='category', format='both')
print("Hand injury categories:")
for injury in hand_injuries:
    print(f"  {injury}")

# Get related codes
wrist_fracture = t.get('S62')
siblings = t.siblings('S62', format='both')
print(f"\nOther wrist/hand conditions:")
for sibling in siblings:
    print(f"  {sibling}")
```

### Efficient Batch Operations

```python
# Process multiple codes efficiently
codes_to_analyze = ['A00', 'E11', 'I21', 'J45', 'S62']

results = []
for code in codes_to_analyze:
    info = t.get(code)
    if info:
        results.append({
            'code': code,
            'name': info['name'],
            'type': info['type'],
            'children_count': len(t.children(code, type=0))
        })

# Display results
for r in results:
    print(f"{r['code']}: {r['name']} ({r['children_count']} subcategories)")
```

## Performance Considerations

- **Initial Load**: ~1-2 seconds for complete taxonomy
- **Lookups**: Microseconds after initial load
- **Memory Usage**: ~50MB for complete taxonomy
- **Caching**: Automatic result caching for repeated operations

## Best Practices

1. **Reuse Instance**: Create one `ICD10Taxonomy` instance and reuse it
2. **Use Format Parameter**: Avoid manual code/name conversions
3. **Leverage Type Filtering**: More efficient than post-filtering results
4. **Batch Operations**: Process multiple codes in single loops when possible

## Error Handling

All methods return `None` or empty lists for invalid inputs:

```python
>>> t.get('INVALID')
None

>>> t.children('INVALID')
[]

>>> t.parent('A00')  # Top-level category has no parent
None
```

## Data Source

The taxonomy data is loaded from `icd10-taxonomy-complete.json`, containing the complete ICD-10-CM classification system with all hierarchical relationships preserved.

## Technical Details

### Architecture

- **Lazy Loading**: Data loads on first access
- **Dual Indexing**: Separate maps for codes and names
- **Path Tracking**: Maintains full hierarchical paths
- **Type Detection**: Automatic classification based on code patterns

### Code Patterns

The module automatically detects ICD-10 types using these patterns:
- Chapters: Roman numerals (I-XXII)
- Ranges: Letter + 2 digits + hyphen (A00-A09)
- Categories: Letter + 2 digits (A00)
- Blocks: Category + dot + 1 digit (A00.0)
- Further subdivisions follow similar patterns

## Contributing

When extending this module:
1. Maintain backward compatibility
2. Preserve the minimalist API design
3. Ensure all methods support both code and name inputs
4. Add appropriate unit tests
5. Update documentation with examples