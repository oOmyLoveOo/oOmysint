"""Shared validators and helpers used by the OSINT modules."""

import re
from datetime import datetime, timezone
from urllib.parse import urlparse

_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})+$"
)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,39}$")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def normalize_domain(raw):
    raw = raw.strip()
    if "://" in raw:
        raw = urlparse(raw).netloc or raw
    return raw.split("/")[0].lower()


def is_valid_domain(domain):
    return bool(_DOMAIN_RE.match(domain))


def is_valid_email(email):
    return bool(_EMAIL_RE.match(email.strip()))


def is_valid_username(username):
    return bool(_USERNAME_RE.match(username.strip()))


def as_text(value):
    """Normalizes python-whois fields (str, list or datetime) into plain text."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return [as_text(v) for v in value if v is not None]
    return str(value)
