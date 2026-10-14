"""Generates Google dork search links for a full name.

This module does not return automated results: full-name searches are too
ambiguous to scrape reliably, so it instead produces ready-to-use links for
manual follow-up investigation. The limitation is reported explicitly so the
final report never implies this data was collected automatically.
"""

from urllib.parse import quote


def generate_dorks(full_name):
    query = quote(f'"{full_name}"')
    return {
        "source": "Dork generator",
        "status": "manual_followup",
        "name": full_name,
        "note": "These are search links for manual investigation, not automated results.",
        "links": {
            "Google": f"https://www.google.com/search?q={query}",
            "Google + LinkedIn": f"https://www.google.com/search?q={query}+site:linkedin.com",
            "Google + social media": (
                f"https://www.google.com/search?q={query}+"
                "(site:twitter.com+OR+site:facebook.com+OR+site:instagram.com)"
            ),
            "Google + documents": f"https://www.google.com/search?q={query}+filetype:pdf",
        },
    }
