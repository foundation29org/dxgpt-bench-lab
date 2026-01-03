"""
__init__

AzureLLM v4 - Wrapper de alto nivel para Azure OpenAI API

Este módulo proporciona una interfaz unificada para trabajar con modelos de Azure OpenAI,
incluyendo soporte para plantillas, esquemas de salida estructurada y simplicidad directa.

Uso típico:
    from utils.llm import Azure
    
    # Configuración automática desde .env
    llm = Azure("gpt-4o")
    response = llm.generate("Hola, ¿cómo estás?")
"""

# Import base class
from .base import BaseLLM

# Import all implementations
from .azure import (
    Azure, 
    AzureLLM,
    LLMConfig,
    Schema,
    create_llm as create_azure_llm,
    quick_generate as quick_generate_azure
)

from .hugging import (
    Hugging,
    HuggingLLM,
    LLMConfig as HuggingLLMConfig,
    Schema as HuggingSchema,
    create_llm as create_hugging_llm,
    quick_generate as quick_generate_hugging
)

# Try importing Gemini (optional dependency)
try:
    from .gemini import (
        Gemini,
        GeminiLLM,
        GeminiLLMConfig,
        create_llm as create_gemini_llm,
        quick_generate as quick_generate_gemini
    )
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    Gemini = None
    GeminiLLM = None
    GeminiLLMConfig = None

# Try importing xAI (optional dependency)
try:
    from .xai import (
        XaiLLM,
        XaiLLMConfig,
        create_llm as create_xai_llm,
        quick_generate as quick_generate_xai
    )
    XAI_AVAILABLE = True
except ImportError:
    XAI_AVAILABLE = False
    XaiLLM = None
    XaiLLMConfig = None

def get_llm(model_name: str, **kwargs) -> BaseLLM:
    """Try each LLM provider until one works."""
    model_lower = model_name.lower()
    
    # Check if model is Grok (xAI)
    is_grok = 'grok' in model_lower
    if is_grok:
        if not XAI_AVAILABLE:
            raise RuntimeError(
                f"Grok model '{model_name}' requires xai-sdk package. "
                "Install it with: pip install xai-sdk"
            )
        try:
            return XaiLLM(model_name, **kwargs)
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize XaiLLM for model '{model_name}': {str(e)}\n"
                "Make sure XAI_API_KEY is set in your .env file."
            ) from e
    
    # Check if model is Gemini
    is_gemini = 'gemini' in model_lower
    if is_gemini:
        # For Gemini models, ONLY try GeminiLLM (no fallback to other providers)
        if not GEMINI_AVAILABLE:
            raise RuntimeError(
                f"Gemini model '{model_name}' requires google-genai package. "
                "Install it with: pip install google-genai"
            )
        try:
            return GeminiLLM(model_name, **kwargs)
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize GeminiLLM for model '{model_name}': {str(e)}\n"
                "Make sure GOOGLE_GENAI_API_KEY or GEMINI_API_KEY is set in your .env file."
            ) from e
    
    # For non-Gemini, non-Grok models, try providers in order
    providers = [HuggingLLM, AzureLLM]
    if GEMINI_AVAILABLE:
        providers.append(GeminiLLM)
    
    for i, provider in enumerate(providers, 1):
        try:
            result = provider(model_name, **kwargs)
            return result
        except Exception as e:
            continue
            
    raise RuntimeError(f"No working LLM provider found for model {model_name}")

# Default implementations
def create_llm(deployment_name: str = None, **config_overrides) -> BaseLLM:
    """Create LLM instance trying different providers."""
    return get_llm(deployment_name or "default", **config_overrides)

def quick_generate(prompt: str, deployment_name: str = "default", **kwargs):
    """Quick one-shot generation."""
    llm = create_llm(deployment_name)
    return llm.generate(prompt, **kwargs)

# Export all
__all__ = [
    # Azure exports
    'Azure',
    'AzureLLM',
    'LLMConfig',
    'Schema',
    
    # Factory functions
    'create_llm',
    'quick_generate',

    # Hugging exports
    'Hugging',
    'HuggingLLM',
    
    # Gemini exports (if available)
    'Gemini',
    'GeminiLLM',
    'GeminiLLMConfig',
    
    # xAI exports (if available)
    'XaiLLM',
    'XaiLLMConfig',
    
    # Base class if available
    'BaseLLM',

    # Get LLM
    'get_llm',
]