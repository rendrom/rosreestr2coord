import json
from typing import Dict, Union

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 \
    Safari/537.36"


def is_error_response(url: str, response: bytes) -> Union[bool, str]:
    is_error = False
    try:
        data = json.loads(response)
        error = data.get("error")
        if error:
            message = error.get("message")
            is_error = message if message else "error"
    except Exception:
        pass
    return is_error


def get_rosreestr_headers() -> Dict[str, str]:
    return {
        "pragma": "no-cache",
        "referer": "https://nspd.gov.ru/map",
        "user-agent": USER_AGENT,
        "x-requested-with": "XMLHttpRequest",
    }
