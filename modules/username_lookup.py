"""Username lookup across social networks, integrating the external tool Sherlock.

Requires Sherlock to be installed (pip install sherlock-project) and available
on PATH as the `sherlock` command.
"""

import re
import shutil
import subprocess

import config

_FOUND_RE = re.compile(r"^\[\+\]\s*([^:]+):\s*(\S+)")


def check_username(username, timeout=None):
    timeout = timeout or config.SHERLOCK_TIMEOUT
    sherlock_bin = shutil.which("sherlock")
    if not sherlock_bin:
        return {
            "source": "Sherlock",
            "status": "not_available",
            "error": "Sherlock is not installed. Install it with: pip install sherlock-project",
            "profiles": [],
        }

    cmd = [sherlock_bin, username, "--timeout", str(config.SHERLOCK_SITE_TIMEOUT),
           "--print-found", "--no-color"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {
            "source": "Sherlock",
            "status": "error",
            "error": f"Sherlock exceeded the {timeout}s timeout for '{username}'.",
            "profiles": [],
        }
    except OSError as exc:
        return {
            "source": "Sherlock",
            "status": "error",
            "error": f"Could not run Sherlock: {exc}",
            "profiles": [],
        }

    profiles = []
    for line in proc.stdout.splitlines():
        match = _FOUND_RE.match(line.strip())
        if match:
            site, url = match.groups()
            profiles.append({"site": site.strip(), "url": url.strip()})

    return {
        "source": "Sherlock",
        "status": "ok",
        "username": username,
        "profiles_found": len(profiles),
        "profiles": profiles,
    }
