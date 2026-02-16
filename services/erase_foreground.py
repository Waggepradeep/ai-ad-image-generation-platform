from typing import Dict, Any, Optional
import base64
from .http_utils import post_json

def erase_foreground(
    api_key: str,
    image_data: bytes = None,
    image_url: str = None,
    content_moderation: bool = False
) -> Dict[str, Any]:
    """
    Erase the foreground from an image and generate the area behind it.
    
    Args:
        api_key: Bria AI API key
        image_data: Image data in bytes (optional if image_url provided)
        image_url: URL of the image (optional if image_data provided)
        content_moderation: Whether to enable content moderation
    """
    url = "https://engine.prod.bria-api.com/v1/erase_foreground"
    
    headers = {
        'api_token': api_key,
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # Prepare request data
    data = {
        'content_moderation': content_moderation
    }
    
    # Add image data
    if image_url:
        data['image_url'] = image_url
    elif image_data:
        data['file'] = base64.b64encode(image_data).decode('utf-8')
    else:
        raise ValueError("Either image_data or image_url must be provided")
    
    return post_json(
        url=url,
        headers=headers,
        payload=data,
        operation_name="Erase foreground",
        timeout=60
    )

# Export the function
__all__ = ['erase_foreground'] 
