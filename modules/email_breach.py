"""Email breach lookup.

Uses HaveIBeenPwned when an API key is configured (HIBP_API_KEY env var).
HIBP keys are paid, so without one the module falls back to the free
XposedOrNot API, which needs no key. Either way, network or API errors are
reported as a status inside the result instead of crashing the run.
"""

import os

import requests

from .utils import is_valid_email

_HIBP_URL = "https://haveibeenpwned.com/api/v3/breachedaccount/{}"
_XON_URL = "https://api.xposedornot.com/v1/check-email/{}"
_HEADERS = {"user-agent": "oOmysint-osint-tool"}


def check_email(email):
    if not is_valid_email(email):
        return {"source": "Email breach check", "status": "error", "error": "Invalid email format."}

    api_key = os.getenv("HIBP_API_KEY")
    if api_key:
        return _check_hibp(email, api_key)
    return _check_xposedornot(email)


def _check_hibp(email, api_key):
    headers = {**_HEADERS, "hibp-api-key": api_key}
    try:
        response = requests.get(_HIBP_URL.format(email), headers=headers, timeout=10)
    except requests.RequestException as exc:
        return {"source": "HaveIBeenPwned", "status": "error", "error": str(exc)}

    if response.status_code == 404:
        return {"source": "HaveIBeenPwned", "status": "ok", "breaches_found": 0, "breaches": []}
    if response.status_code == 200:
        breaches = [b.get("Name") for b in response.json()]
        return {"source": "HaveIBeenPwned", "status": "ok", "breaches_found": len(breaches), "breaches": breaches}
    if response.status_code == 401:
        return {"source": "HaveIBeenPwned", "status": "error", "error": "Invalid or unauthorized HIBP_API_KEY."}
    return {"source": "HaveIBeenPwned", "status": "error", "error": f"Unexpected HTTP status: {response.status_code}"}


def _check_xposedornot(email):
    try:
        response = requests.get(_XON_URL.format(email), headers=_HEADERS, timeout=10)
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        return {"source": "XposedOrNot", "status": "error", "error": str(exc)}

    # XposedOrNot answers {"Error": "Not found"} when the email is in no known breach.
    if response.status_code == 404 or data.get("Error") == "Not found":
        return {"source": "XposedOrNot", "status": "ok", "breaches_found": 0, "breaches": []}
    if response.status_code == 200 and "breaches" in data:
        # The API wraps the list of breach names in another list: [["A", "B", ...]]
        breaches = data["breaches"][0] if data["breaches"] else []
        return {"source": "XposedOrNot", "status": "ok", "breaches_found": len(breaches), "breaches": breaches}
    return {"source": "XposedOrNot", "status": "error", "error": f"Unexpected HTTP status: {response.status_code}"}
