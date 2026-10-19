"""WHOIS and DNS lookup for a domain: registrar, dates, nameservers and core records."""

import whois
import dns.resolver

import config
from .utils import as_text


def analyze_domain(domain):
    result = {"source": "WHOIS + DNS", "status": "ok", "domain": domain}

    try:
        w = whois.whois(domain)
        result["whois"] = {
            "registrar": as_text(w.registrar),
            "creation_date": as_text(w.creation_date),
            "expiration_date": as_text(w.expiration_date),
            "name_servers": as_text(w.name_servers),
            "emails": as_text(w.emails),
        }
    except Exception as exc:
        result["whois"] = None
        result["whois_error"] = str(exc)

    dns_records = {}
    for record_type in config.DNS_RECORD_TYPES:
        try:
            answers = dns.resolver.resolve(domain, record_type, lifetime=config.DNS_TIMEOUT)
            dns_records[record_type] = [r.to_text() for r in answers]
        except Exception:
            dns_records[record_type] = []
    result["dns"] = dns_records

    whois_failed = result.get("whois") is None
    dns_empty = not any(dns_records.values())
    if whois_failed and dns_empty:
        result["status"] = "error"
        result["error"] = result.get("whois_error", "Could not retrieve information for this domain.")

    return result
