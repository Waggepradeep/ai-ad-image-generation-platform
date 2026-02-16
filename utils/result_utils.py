def extract_result_urls(result, limit=None):
    """Normalize Bria API responses into a list of image URLs."""
    if not isinstance(result, dict):
        return []

    urls = []

    if isinstance(result.get("result_url"), str):
        urls.append(result["result_url"])

    if isinstance(result.get("result_urls"), list):
        urls.extend([u for u in result["result_urls"] if isinstance(u, str)])

    if isinstance(result.get("urls"), list):
        urls.extend([u for u in result["urls"] if isinstance(u, str)])

    nested = result.get("result")
    if isinstance(nested, list):
        for item in nested:
            if isinstance(item, dict) and isinstance(item.get("urls"), list):
                urls.extend([u for u in item["urls"] if isinstance(u, str)])
            elif isinstance(item, list):
                urls.extend([u for u in item if isinstance(u, str)])

    deduped = []
    seen = set()
    for url in urls:
        if url and url not in seen:
            deduped.append(url)
            seen.add(url)

    return deduped[:limit] if isinstance(limit, int) and limit > 0 else deduped
