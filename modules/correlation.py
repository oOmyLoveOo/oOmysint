"""Correlates the collected results to find simple relations between targets.

Each check compares two pieces of data (e.g. the email's domain and the
domain target) and, when they match, adds a human-readable relation. These
are hints for the analyst, not proof that two accounts belong to one person.
"""


def find_relations(targets, results):
    relations = []
    username = targets.get("username")
    email = targets.get("email")
    domain = targets.get("domain")

    if email:
        local_part, _, email_domain = email.lower().partition("@")

        if domain and email_domain == domain.lower():
            relations.append(f"The email '{email}' belongs to the investigated domain '{domain}'.")

        if username and local_part == username.lower():
            relations.append(f"The email local part matches the username '{username}' (likely same person).")

        whois_emails = (results.get("domain_lookup", {}).get("whois") or {}).get("emails") or []
        if isinstance(whois_emails, str):
            whois_emails = [whois_emails]
        if email.lower() in (e.lower() for e in whois_emails):
            relations.append(f"The email '{email}' appears as a contact in the WHOIS record of '{domain}'.")

    # theHarvester: public emails found for the domain, compared with the
    # email and username targets.
    harvested = results.get("harvester_lookup", {}).get("emails") or []
    if email and email.lower() in harvested:
        relations.append(f"The email '{email}' is publicly exposed (found by theHarvester for '{domain}').")
    if username:
        matches = [e for e in harvested if e.partition("@")[0] == username.lower()]
        for match in matches:
            if match != (email or "").lower():
                relations.append(
                    f"theHarvester found '{match}', whose local part matches the username '{username}' "
                    "(possible additional email of the same person)."
                )

    profiles = results.get("username_lookup", {}).get("profiles") or []
    if len(profiles) > 1:
        sites = ", ".join(p["site"] for p in profiles[:5])
        more = f" and {len(profiles) - 5} more" if len(profiles) > 5 else ""
        relations.append(
            f"The username '{username}' exists on {len(profiles)} sites ({sites}{more}); "
            "these may be the same person across networks."
        )

    breaches = results.get("email_breach", {}).get("breaches") or []
    if breaches:
        relations.append(f"The email '{email}' appears in {len(breaches)} known data breaches.")

    return relations
