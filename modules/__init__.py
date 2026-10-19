"""OSINT modules for oOmysint and the registry that wires them to the inputs.

main.py runs every registered module whose input type was provided, so adding
a new source only takes two steps:
  1. create modules/my_source.py with one function that receives the input
     value and returns a dict with at least "source" and "status" keys;
  2. add one line to MODULES below.
The report and the console output render any new module automatically.
"""

from . import (
    domain_lookup,
    email_breach,
    harvester_lookup,
    name_dorks,
    phone_lookup,
    username_lookup,
)

# (result key, input type, lookup function, progress message)
MODULES = [
    ("username_lookup", "username", username_lookup.check_username, "Running Sherlock for username"),
    ("email_breach", "email", email_breach.check_email, "Checking data breaches for"),
    ("domain_lookup", "domain", domain_lookup.analyze_domain, "Running WHOIS + DNS for"),
    ("harvester_lookup", "domain", harvester_lookup.harvest_domain, "Running theHarvester for"),
    ("phone_lookup", "phone", phone_lookup.analyze_phone, "Analyzing phone number"),
    ("name_dorks", "name", name_dorks.generate_dorks, "Generating lookup dorks for"),
]
