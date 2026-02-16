import requests


def post_json(url, headers, payload, operation_name, timeout=60):
    """POST JSON and raise a consistent, user-readable exception on failure."""
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "unknown"
        details = ""
        if e.response is not None:
            try:
                body = e.response.json()
                details = body.get("message") or body.get("error") or str(body)
            except Exception:
                details = e.response.text or ""
        if details:
            raise Exception(f"{operation_name} failed (status={status_code}): {details}") from e
        raise Exception(f"{operation_name} failed (status={status_code})") from e
    except requests.exceptions.RequestException as e:
        raise Exception(f"{operation_name} failed: network error ({str(e)})") from e
