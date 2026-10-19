#!/usr/bin/env python3
"""oOmysint — modular OSINT CLI orchestrator.

Usage examples:
    oomysint --username johndoe
    oomysint --domain example.com --email john@example.com
    oomysint --phone "+1 202-555-0178" --name "John Doe" -oA report

Flow: validate inputs -> run every registered module for the given inputs
(modules.MODULES) -> correlate results -> write console / JSON / HTML / graph.
"""

import argparse
import os
import sys

from dotenv import load_dotenv

import config
import graph
import report
from modules import MODULES, correlation
from modules.utils import INPUT_TYPES


def parse_args():
    parser = argparse.ArgumentParser(
        description="oOmysint: modular OSINT CLI for digital footprint recon.",
    )
    parser.add_argument("-u", "--username", help="Username to search across social networks (via Sherlock)")
    parser.add_argument("-d", "--domain", help="Domain to analyze via WHOIS + DNS and theHarvester")
    parser.add_argument("-p", "--phone", help="Phone number in international format (e.g. +1 202-555-0178)")
    parser.add_argument("-e", "--email", help="Email to check for data breaches (HIBP or XposedOrNot)")
    parser.add_argument("-n", "--name", help="Full name to generate manual-lookup dorks for")

    output = parser.add_argument_group(
        "output (nmap-style; with none of these, results print to the console only)"
    )
    output.add_argument("-oJ", dest="output_json", metavar="FILE", help="Write the JSON report to FILE")
    output.add_argument("-oH", dest="output_html", metavar="FILE", help="Write the HTML report to FILE")
    output.add_argument("-oG", dest="output_graph", metavar="BASENAME",
                        help="Write the relations graph as BASENAME.dot (+ BASENAME.png with Graphviz)")
    output.add_argument(
        "-oA",
        dest="output_all",
        metavar="BASENAME",
        help="Write everything at once: BASENAME.json, BASENAME.html and the graph",
    )

    parser.add_argument(
        "--sherlock-timeout",
        type=int,
        default=config.SHERLOCK_TIMEOUT,
        help=f"Timeout in seconds for the Sherlock subprocess (default: {config.SHERLOCK_TIMEOUT})",
    )
    return parser.parse_args()


def _ensure_parent_dir(path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def collect_targets(args, errors):
    """Normalizes and validates every input given on the command line.

    Invalid inputs are recorded in `errors` and skipped, so the other
    modules still run.
    """
    targets = {}
    for kind, (normalize, validate, hint) in INPUT_TYPES.items():
        raw = getattr(args, kind)
        if raw is None:
            continue
        value = normalize(raw)
        if validate(value):
            targets[kind] = value
        else:
            errors.append(f"Invalid {kind}: '{raw}' ({hint})")
    return targets


def run_modules(targets, errors):
    """Runs every registered module whose input type is among the targets."""
    results = {}
    for result_key, input_kind, lookup, message in MODULES:
        value = targets.get(input_kind)
        if value is None:
            continue
        print(f"[*] {message} '{value}'...")
        try:
            results[result_key] = lookup(value)
        except Exception as exc:  # a broken module must not stop the others
            errors.append(f"{result_key} failed: {exc}")
    return results


def main():
    load_dotenv()
    args = parse_args()
    config.SHERLOCK_TIMEOUT = args.sherlock_timeout

    if not any(getattr(args, kind) for kind in INPUT_TYPES):
        print(
            "Error: provide at least one target (--username, --domain, --phone, --email or --name).",
            file=sys.stderr,
        )
        sys.exit(1)

    errors = []
    targets = collect_targets(args, errors)
    results = run_modules(targets, errors)
    relations = correlation.find_relations(targets, results)
    report_data = report.build_report(targets, results, relations, errors)

    json_path = args.output_json or (f"{args.output_all}.json" if args.output_all else None)
    html_path = args.output_html or (f"{args.output_all}.html" if args.output_all else None)
    graph_base = args.output_graph or args.output_all

    # The graph goes first so the HTML report can embed its PNG.
    if graph_base:
        _ensure_parent_dir(graph_base)
        dot_path, png_path, graph_error = graph.write_graph(report_data, graph_base)
        print(f"[+] Relations graph written to {dot_path}" + (f" and {png_path}" if png_path else ""))
        if graph_error:
            errors.append(graph_error)
        report_data["graph"] = png_path

    if json_path:
        _ensure_parent_dir(json_path)
        report.write_json(report_data, json_path)
        print(f"[+] JSON report written to {json_path}")

    if html_path:
        _ensure_parent_dir(html_path)
        report.write_html(report_data, html_path)
        print(f"[+] HTML report written to {html_path}")

    wrote_file = bool(json_path or html_path or graph_base)
    if not wrote_file:
        print()
        report.print_console(report_data)

    # The console report already lists errors; only repeat them when writing to files.
    if errors and wrote_file:
        print("\n[!] Some issues occurred during this run:")
        for error in errors:
            print(f"    - {error}")


if __name__ == "__main__":
    main()
