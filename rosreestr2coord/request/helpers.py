import json
from typing import Dict, Union

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
)

REFERER = "https://nspd.gov.ru/map?thematic=PKK"


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
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9,ru-RU;q=0.8,ru;q=0.7,es;q=0.6",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": REFERER,
        "origin": "https://nspd.gov.ru",
        "user-agent": USER_AGENT,
    }
