from typing import Dict, Any, Optional
from .http_utils import post_json

def enhance_prompt(
    api_key: str,
    prompt: str,
    **kwargs
) -> str:
    """
    Enhance a prompt using Bria AI's prompt enhancement service.
    
    Args:
        api_key: Bria AI API key
        prompt: Original prompt to enhance
        **kwargs: Additional parameters for the API
    
    Returns:
        Enhanced prompt string
    """
    url = "https://engine.prod.bria-api.com/v1/prompt_enhancer"
    
    headers = {
        'api_token': api_key,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    data = {
        'prompt': prompt,
        **kwargs
    }
    
    try:
        result = post_json(
            url=url,
            headers=headers,
            payload=data,
            operation_name="Prompt enhancement",
            timeout=30
        )
        return result.get("prompt variations", prompt)  # Return original prompt if enhancement fails
    except Exception as e:
        return prompt  # Return original prompt on error 
