"""Shared validators and helpers used by main.py and the OSINT modules."""

import re
from datetime import datetime, timezone
from urllib.parse import urlparse

import phonenumbers

_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})+$"
)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,39}$")
# Words made of letters (any language) separated by spaces, dots, ' or -.
_NAME_RE = re.compile(r"^[^\W\d_]+(?:[ .'\-]+[^\W\d_]+)*\.?$")


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


def is_valid_phone(phone):
    try:
        return phonenumbers.is_valid_number(phonenumbers.parse(phone, None))
    except phonenumbers.NumberParseException:
        return False


def is_valid_name(name):
    return 2 <= len(name) <= 100 and bool(_NAME_RE.match(name))


# Input types accepted on the command line, in processing order:
# input type -> (normalizer, validator, hint shown when validation fails)
INPUT_TYPES = {
    "username": (str.strip, is_valid_username, "letters, digits, '_', '.', '-' (max 39)"),
    "email": (lambda v: v.strip().lower(), is_valid_email, "e.g. john@example.com"),
    "domain": (normalize_domain, is_valid_domain, "e.g. example.com"),
    "phone": (str.strip, is_valid_phone, "international format with '+', e.g. +34 612345678"),
    "name": (lambda v: " ".join(v.split()), is_valid_name, "letters and spaces, e.g. John Doe"),
}


def as_text(value):
    """Normalizes python-whois fields (str, list or datetime) into plain text."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return [as_text(v) for v in value if v is not None]
    return str(value)
