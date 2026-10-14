"""Builds the JSON and HTML report from the collected OSINT results."""

import html
import json

from modules.utils import now_iso

_STATUS_LABELS = {
    "ok": ("OK", "#2e7d32"),
    "error": ("ERROR", "#c62828"),
    "not_configured": ("NOT CONFIGURED", "#757575"),
    "not_available": ("NOT AVAILABLE", "#757575"),
    "manual_followup": ("MANUAL FOLLOW-UP", "#1565c0"),
}

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_STATUS_ANSI = {
    "ok": "\033[32m",
    "error": "\033[31m",
    "not_configured": "\033[90m",
    "not_available": "\033[90m",
    "manual_followup": "\033[34m",
}


def build_report(targets, results, relations, errors):
    return {
        "generated_at": now_iso(),
        "targets": targets,
        "results": results,
        "relations": relations,
        "errors": errors,
    }


def write_json(report_data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)


def write_html(report_data, path):
    with open(path, "w", encoding="utf-8") as f:
        f.write(_render_html(report_data))


def print_console(report_data):
    """Human-readable, nmap-style summary printed when no -o flag is given."""
    print(f"{_BOLD}oOmysint OSINT report{_RESET}  ({report_data['generated_at']})")

    targets = report_data["targets"]
    if targets:
        summary = ", ".join(f"{k}={v}" for k, v in targets.items())
        print(f"{_DIM}Targets: {summary}{_RESET}")
    print()

    for key, data in report_data["results"].items():
        status = data.get("status", "unknown")
        label, _ = _STATUS_LABELS.get(status, (status.upper(), None))
        color = _STATUS_ANSI.get(status, "")
        source = data.get("source", key)
        print(f"{_BOLD}== {source} =={_RESET} [{color}{label}{_RESET}]")
        _print_fields(data, indent=2, skip={"source", "status"})
        print()

    print(f"{_BOLD}== Relations =={_RESET}")
    for relation in report_data["relations"] or ["No relations found between the targets."]:
        print(f"  - {relation}")
    print()

    if report_data["errors"]:
        print(f"{_BOLD}Errors:{_RESET}")
        for error in report_data["errors"]:
            print(f"  - {error}")
        print()


def _print_fields(data, indent, skip):
    pad = " " * indent
    for key, value in data.items():
        if key in skip:
            continue
        if isinstance(value, dict):
            print(f"{pad}{key}:")
            _print_fields(value, indent + 2, skip=set())
        elif isinstance(value, (list, tuple)):
            if not value:
                print(f"{pad}{key}: (none)")
            else:
                print(f"{pad}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        rendered = ", ".join(f"{k}={v}" for k, v in item.items())
                        print(f"{pad}  - {rendered}")
                    else:
                        print(f"{pad}  - {item}")
        else:
            print(f"{pad}{key}: {value}")


def _render_value(value):
    if value is None:
        return '<span class="muted">&mdash;</span>'
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        safe = html.escape(value)
        return f'<a href="{safe}" target="_blank" rel="noopener">{safe}</a>'
    if isinstance(value, (list, tuple)):
        if not value:
            return '<span class="muted">none</span>'
        items = "".join(f"<li>{_render_value(v)}</li>" for v in value)
        return f"<ul>{items}</ul>"
    if isinstance(value, dict) and set(value) == {"site", "url"}:
        # Sherlock profile: show it compactly as one clickable line.
        return f"{html.escape(value['site'])} &rarr; {_render_value(value['url'])}"
    if isinstance(value, dict):
        rows = "".join(
            f"<tr><th>{html.escape(str(k))}</th><td>{_render_value(v)}</td></tr>"
            for k, v in value.items()
        )
        return f'<table class="nested">{rows}</table>'
    return html.escape(str(value))


def _render_module(key, data):
    status = data.get("status", "unknown")
    label, color = _STATUS_LABELS.get(status, (str(status).upper(), "#757575"))
    source = html.escape(str(data.get("source", key)))
    body_rows = "".join(
        f"<tr><th>{html.escape(str(k))}</th><td>{_render_value(v)}</td></tr>"
        for k, v in data.items()
        if k not in ("source", "status")
    )
    return f"""
    <section class="module">
      <h2>{source} <span class="badge" style="background:{color}">{label}</span></h2>
      <table>{body_rows}</table>
    </section>
    """


def _render_html(report_data):
    targets = report_data["targets"]
    target_items = "".join(
        f"<li><strong>{html.escape(k)}:</strong> {html.escape(str(v))}</li>"
        for k, v in targets.items()
        if v
    )
    modules_html = "".join(_render_module(k, v) for k, v in report_data["results"].items())

    relation_items = "".join(f"<li>{html.escape(r)}</li>" for r in report_data["relations"])
    if not relation_items:
        relation_items = '<li class="muted">No relations found between the targets.</li>'
    relations_html = f'<section class="module"><h2>Relations found</h2><ul>{relation_items}</ul></section>'

    errors_html = ""
    if report_data["errors"]:
        error_items = "".join(f"<li>{html.escape(str(e))}</li>" for e in report_data["errors"])
        errors_html = f'<section class="module"><h2>Execution errors</h2><ul>{error_items}</ul></section>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>oOmysint OSINT report</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0f1115; color: #e6e6e6; margin: 0; padding: 2rem; }}
  h1 {{ margin-bottom: 0.2rem; }}
  .meta {{ color: #9aa0a6; margin-bottom: 1.5rem; }}
  .module {{ background: #1a1d24; border: 1px solid #2a2d35; border-radius: 8px; padding: 1rem 1.2rem; margin-bottom: 1.2rem; }}
  .module h2 {{ margin-top: 0; font-size: 1.1rem; display: flex; align-items: center; gap: 0.6rem; }}
  .badge {{ font-size: 0.65rem; padding: 0.15rem 0.5rem; border-radius: 4px; color: #fff; font-weight: 600; letter-spacing: 0.03em; }}
  table {{ border-collapse: collapse; width: 100%; }}
  table.nested {{ margin: 0.2rem 0; }}
  th, td {{ text-align: left; padding: 0.3rem 0.6rem; vertical-align: top; border-bottom: 1px solid #2a2d35; }}
  th {{ color: #9aa0a6; width: 220px; font-weight: 500; }}
  a {{ color: #8ab4f8; }}
  ul {{ margin: 0.2rem 0 0.2rem 1.1rem; }}
  .muted {{ color: #6b7280; }}
  .limitations {{ font-size: 0.9rem; color: #c8c8c8; }}
</style>
</head>
<body>
  <h1>oOmysint &mdash; OSINT report</h1>
  <div class="meta">Generated: {html.escape(report_data["generated_at"])}</div>
  <section class="module">
    <h2>Targets investigated</h2>
    <ul>{target_items}</ul>
  </section>
  {relations_html}
  {modules_html}
  {errors_html}
  <section class="module limitations">
    <h2>Limitations</h2>
    <ul>
      <li>Sherlock results depend on the sites it checks at run time and may include false negatives/positives.</li>
      <li>Email breaches come from HaveIBeenPwned if a key is configured, otherwise from the free XposedOrNot API; both only know publicly disclosed breaches.</li>
      <li>Relations are simple string matches (hints), not proof that accounts belong to the same person.</li>
      <li>WHOIS data availability varies by registrar and may be partially redacted (GDPR/privacy proxies).</li>
      <li>Full-name search only produces manual-lookup links; it is not an automated data source.</li>
      <li>This tool is intended for educational and authorized OSINT use only.</li>
    </ul>
  </section>
</body>
</html>"""
