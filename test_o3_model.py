#!/usr/bin/env python3
"""
Test script for o3 model integration
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables manually if dotenv not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Manual loading of .env file
    env_path = project_root / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value

# Import our Azure LLM
from utils.llm import AzureLLM

def test_o3_model():
    """Test the o3 model with a simple prompt"""
    
    print("=== Testing o3 Model Integration ===\n")
    
    # Check environment variables
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    print(f"Endpoint: {endpoint}")
    print(f"API Key: {'Present' if api_key else 'Missing'}")
    print()
    
    try:
        # Create LLM instance with o3 model
        print("Creating o3 model instance...")
        llm = AzureLLM(
            deployment_name="o3-images",
            extra_params={
                "reasoning": {"effort": "high"}
            }
        )
        print("✓ Model instance created")
        print()
        
        # Test 1: Simple text generation
        print("Test 1: Simple text generation")
        prompt = "What is 2+2?"
        print(f"Prompt: {prompt}")
        
        response = llm.generate(prompt)
        print(f"Response: {response}")
        print()
        
        # Test 2: JSON generation with schema
        print("Test 2: JSON generation with schema")
        prompt = "List 3 common medical symptoms"
        schema = {
            "type": "object",
            "properties": {
                "symptoms": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["symptoms"]
        }
        
        print(f"Prompt: {prompt}")
        response = llm.generate(prompt, schema=schema)
        print(f"Response: {json.dumps(response, indent=2)}")
        print()
        
        print("✓ All tests passed!")
        
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {str(e)}")
        logger.exception("Detailed error:")
        return False
    
    return True

if __name__ == "__main__":
    success = test_o3_model()
    sys.exit(0 if success else 1)