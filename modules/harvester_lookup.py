"""Domain footprint through the external tool theHarvester (emails, hosts, IPs).

theHarvester is run as a subprocess using only the passive sources listed in
config.HARVESTER_SOURCES, and the JSON file it writes is parsed. A missing
tool, a timeout or unreadable output is reported as a status inside the
result instead of crashing the run.

Requires theHarvester on PATH (preinstalled on Kali; otherwise
`apt install theharvester` or https://github.com/laramies/theHarvester).
"""

import json
import os
import shutil
import subprocess
import tempfile

import config

_SOURCE = "theHarvester"


def harvest_domain(domain):
    binary = shutil.which("theHarvester") or shutil.which("theharvester")
    if not binary:
        return {
            "source": _SOURCE,
            "status": "not_available",
            "error": "theHarvester is not installed (apt install theharvester).",
        }

    # theHarvester writes <name>.json/.xml; use a throwaway dir so no files
    # are left behind in the working directory.
    with tempfile.TemporaryDirectory() as tmp:
        base = os.path.join(tmp, "harvest")
        cmd = [
            binary, "-d", domain,
            "-b", config.HARVESTER_SOURCES,
            "-l", str(config.HARVESTER_LIMIT),
            "-q", "-f", base,
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True,
                           timeout=config.HARVESTER_TIMEOUT, cwd=tmp)
        except subprocess.TimeoutExpired:
            return {"source": _SOURCE, "status": "error",
                    "error": f"theHarvester exceeded the {config.HARVESTER_TIMEOUT}s timeout."}
        except OSError as exc:
            return {"source": _SOURCE, "status": "error", "error": f"Could not run theHarvester: {exc}"}

        try:
            with open(base + ".json", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return {"source": _SOURCE, "status": "error",
                    "error": "theHarvester produced no readable JSON output."}

    domain = domain.lower()
    emails = sorted({e.lower() for e in data.get("emails") or []})
    # Hosts come as "host:ip"; keep the hostname, drop wildcards and other domains.
    hosts = sorted({
        h.split(":")[0].lower() for h in data.get("hosts") or []
        if not h.startswith("*") and h.split(":")[0].lower().endswith(domain)
    })
    ips = sorted(set(data.get("ips") or []))

    cap = config.MAX_ITEMS_IN_REPORT
    return {
        "source": _SOURCE,
        "status": "ok",
        "domain": domain,
        "sources_used": config.HARVESTER_SOURCES,
        "emails_found": len(emails),
        "emails": emails[:cap],
        "hosts_found": len(hosts),
        "hosts": hosts[:cap],
        "ips_found": len(ips),
        "ips": ips[:cap],
        "truncated": any(len(x) > cap for x in (emails, hosts, ips)),
    }
