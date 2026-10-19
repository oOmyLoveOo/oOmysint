"""Central configuration for oOmysint.

Timeouts, limits and external-tool settings live here so they can be tuned
without touching the modules. API keys are NOT stored here: they come from
environment variables / the .env file (see .env.example).
"""

# --- HTTP / DNS ---
USER_AGENT = "oOmysint-osint-tool"
HTTP_TIMEOUT = 10          # seconds per HTTP request (breach APIs)
DNS_TIMEOUT = 5            # seconds per DNS query
DNS_RECORD_TYPES = ("A", "MX", "NS", "TXT")

# --- Sherlock (external tool, username module) ---
SHERLOCK_TIMEOUT = 120     # whole run; overridable with --sherlock-timeout
SHERLOCK_SITE_TIMEOUT = 5  # per site checked

# --- theHarvester (external tool, domain module) ---
# Only passive sources that need no API key: they query third-party databases,
# never the target itself.
HARVESTER_SOURCES = "crtsh,hackertarget,duckduckgo"
HARVESTER_LIMIT = 200
HARVESTER_TIMEOUT = 180

# --- Report / graph ---
MAX_ITEMS_IN_REPORT = 50   # long lists (hosts, emails) are truncated in the report
MAX_GRAPH_NODES = 20       # max child nodes per source in the relations graph
