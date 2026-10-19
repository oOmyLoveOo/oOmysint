"""Relations graph: exports the investigated entities and their findings as a
Graphviz DOT file, and renders it to PNG when the `dot` binary is installed
(apt install graphviz). The .dot file can also be opened in other tools.

Layout: a central "profile" node links every input (username, email, domain,
phone, name); each input links to what was found for it (profiles, breaches,
hosts...). Correlations found between inputs are drawn as dashed red edges.
"""

import shutil
import subprocess

import config

# Node colours per entity type.
_COLORS = {
    "profile": "#455a64",
    "username": "#1565c0",
    "email": "#6a1b9a",
    "domain": "#2e7d32",
    "phone": "#ef6c00",
    "name": "#00838f",
    "finding": "#424242",
    "breach": "#c62828",
}


def _q(text):
    """Quotes a string for DOT (escapes \\ and \", newlines become \\n)."""
    escaped = str(text).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


class _Dot:
    def __init__(self):
        self.lines = []
        self.ids = {}

    def node(self, key, label, kind):
        if key not in self.ids:
            node_id = f"n{len(self.ids)}"
            self.ids[key] = node_id
            self.lines.append(
                f'  {node_id} [label={_q(label)}, fillcolor="{_COLORS[kind]}"];'
            )
        return self.ids[key]

    def edge(self, a, b, label=None, related=False):
        attrs = []
        if label:
            attrs.append(f"label={_q(label)}")
        if related:
            attrs.append('style=dashed, color="#e53935", fontcolor="#e53935"')
        suffix = f" [{', '.join(attrs)}]" if attrs else ""
        self.lines.append(f"  {a} -> {b}{suffix};")

    def children(self, parent, items, kind, prefix, edge_label=None, total=None):
        """Adds up to MAX_GRAPH_NODES child nodes, plus a '+N more' node.

        `total` is the real number of findings when `items` was already
        truncated by the module (e.g. theHarvester hosts).
        """
        limit = config.MAX_GRAPH_NODES
        total = max(total or 0, len(items))
        for item in items[:limit]:
            self.edge(parent, self.node(f"{prefix}:{item}", item, kind), edge_label)
        if total > limit:
            more = self.node(f"{prefix}:more", f"+{total - limit} more", "finding")
            self.edge(parent, more, edge_label)


def build_dot(report_data):
    targets = report_data["targets"]
    results = report_data["results"]
    g = _Dot()

    profile = g.node("profile", "Investigated profile", "profile")
    target_ids = {}
    for kind, value in targets.items():
        target_ids[kind] = g.node(f"target:{kind}", f"{kind}\n{value}", kind)
        g.edge(profile, target_ids[kind])

    if "username" in target_ids:
        sites = [p["site"] for p in results.get("username_lookup", {}).get("profiles") or []]
        g.children(target_ids["username"], sites, "finding", "site", "account on")

    if "email" in target_ids:
        breaches = results.get("email_breach", {}).get("breaches") or []
        g.children(target_ids["email"], breaches, "breach", "breach", "leaked in")

    if "domain" in target_ids:
        harvest = results.get("harvester_lookup", {})
        g.children(target_ids["domain"], harvest.get("emails") or [], "email", "hemail", "email",
                   total=harvest.get("emails_found"))
        g.children(target_ids["domain"], harvest.get("hosts") or [], "finding", "host", "host",
                   total=harvest.get("hosts_found"))
        registrar = (results.get("domain_lookup", {}).get("whois") or {}).get("registrar")
        if registrar:
            g.edge(target_ids["domain"], g.node("registrar", registrar, "finding"), "registrar")

    if "phone" in target_ids:
        phone = results.get("phone_lookup", {})
        for field in ("country", "carrier", "line_type"):
            if phone.get(field) and phone[field] != "Unknown":
                g.edge(target_ids["phone"], g.node(f"phone:{field}", phone[field], "finding"), field)

    # Correlations between inputs (same logic as modules/correlation.py).
    email, username, domain = targets.get("email"), targets.get("username"), targets.get("domain")
    if email and domain and email.partition("@")[2] == domain:
        g.edge(target_ids["email"], target_ids["domain"], "belongs to", related=True)
    if email and username and email.partition("@")[0] == username.lower():
        g.edge(target_ids["username"], target_ids["email"], "same person?", related=True)
    if email and email in (results.get("harvester_lookup", {}).get("emails") or []):
        g.edge(target_ids["domain"], target_ids["email"], "exposed by theHarvester", related=True)

    header = [
        "digraph oOmysint {",
        "  rankdir=LR;",
        '  graph [bgcolor="#0f1115", fontcolor="#e6e6e6", fontname="Helvetica"];',
        '  node [shape=box, style="rounded,filled", fontcolor="white", fontname="Helvetica", color="#2a2d35"];',
        '  edge [color="#9aa0a6", fontcolor="#9aa0a6", fontname="Helvetica", fontsize=9];',
    ]
    return "\n".join(header + g.lines + ["}"]) + "\n"


def write_graph(report_data, basename):
    """Writes BASENAME.dot and, if Graphviz is installed, BASENAME.png.

    Returns (dot_path, png_path_or_None, error_or_None).
    """
    dot_path = f"{basename}.dot"
    with open(dot_path, "w", encoding="utf-8") as f:
        f.write(build_dot(report_data))

    dot_bin = shutil.which("dot")
    if not dot_bin:
        return dot_path, None, "Graphviz not installed: only the .dot file was written (apt install graphviz)."

    png_path = f"{basename}.png"
    try:
        subprocess.run([dot_bin, "-Tpng", dot_path, "-o", png_path],
                       check=True, capture_output=True, timeout=60)
    except (subprocess.SubprocessError, OSError) as exc:
        return dot_path, None, f"Graphviz could not render the graph: {exc}"
    return dot_path, png_path, None
