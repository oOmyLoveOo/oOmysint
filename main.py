#!/usr/bin/env python3
"""oOmysint — modular OSINT CLI orchestrator.

Usage examples:
    oomysint --username johndoe
    oomysint --domain example.com --email john@example.com
    oomysint --phone "+1 202-555-0178" --name "John Doe" -oA report
"""

import argparse
import os
import sys

from dotenv import load_dotenv

import report
from modules import correlation, domain_lookup, email_breach, name_dorks, phone_lookup, username_lookup
from modules.utils import is_valid_domain, is_valid_email, is_valid_username, normalize_domain


def parse_args():
    parser = argparse.ArgumentParser(
        description="oOmysint: modular OSINT CLI for digital footprint recon.",
    )
    parser.add_argument("-u", "--username", help="Username to search across social networks (via Sherlock)")
    parser.add_argument("-d", "--domain", help="Domain to analyze via WHOIS + DNS")
    parser.add_argument("-p", "--phone", help="Phone number in international format (e.g. +1 202-555-0178)")
    parser.add_argument("-e", "--email", help="Email to check for data breaches (HIBP or XposedOrNot)")
    parser.add_argument("-n", "--name", help="Full name to generate manual-lookup dorks for")

    output = parser.add_argument_group(
        "output (nmap-style; with none of these, results print to the console only)"
    )
    output.add_argument("-oJ", dest="output_json", metavar="FILE", help="Write the JSON report to FILE")
    output.add_argument("-oH", dest="output_html", metavar="FILE", help="Write the HTML report to FILE")
    output.add_argument(
        "-oA",
        dest="output_all",
        metavar="BASENAME",
        help="Write both formats at once, as BASENAME.json and BASENAME.html",
    )

    parser.add_argument(
        "--sherlock-timeout",
        type=int,
        default=120,
        help="Timeout in seconds for the Sherlock subprocess (default: 120)",
    )
    return parser.parse_args()


def _ensure_parent_dir(path):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def main():
    load_dotenv()
    args = parse_args()

    if not any([args.username, args.domain, args.phone, args.email, args.name]):
        print(
            "Error: provide at least one target (--username, --domain, --phone, --email or --name).",
            file=sys.stderr,
        )
        sys.exit(1)

    targets = {}
    results = {}
    errors = []

    if args.username:
        if not is_valid_username(args.username):
            errors.append(f"Invalid username: '{args.username}'")
        else:
            targets["username"] = args.username
            print(f"[*] Running Sherlock for username '{args.username}'...")
            try:
                results["username_lookup"] = username_lookup.check_username(
                    args.username, timeout=args.sherlock_timeout
                )
            except Exception as exc:
                errors.append(f"username_lookup failed: {exc}")

    if args.domain:
        domain = normalize_domain(args.domain)
        if not is_valid_domain(domain):
            errors.append(f"Invalid domain: '{args.domain}'")
        else:
            targets["domain"] = domain
            print(f"[*] Running WHOIS + DNS for domain '{domain}'...")
            try:
                results["domain_lookup"] = domain_lookup.analyze_domain(domain)
            except Exception as exc:
                errors.append(f"domain_lookup failed: {exc}")

    if args.phone:
        targets["phone"] = args.phone
        print(f"[*] Analyzing phone number '{args.phone}'...")
        try:
            results["phone_lookup"] = phone_lookup.analyze_phone(args.phone)
        except Exception as exc:
            errors.append(f"phone_lookup failed: {exc}")

    if args.email:
        if not is_valid_email(args.email):
            errors.append(f"Invalid email: '{args.email}'")
        else:
            targets["email"] = args.email
            print(f"[*] Checking data breaches for '{args.email}'...")
            try:
                results["email_breach"] = email_breach.check_email(args.email)
            except Exception as exc:
                errors.append(f"email_breach failed: {exc}")

    if args.name:
        targets["name"] = args.name
        print(f"[*] Generating lookup dorks for '{args.name}'...")
        try:
            results["name_dorks"] = name_dorks.generate_dorks(args.name)
        except Exception as exc:
            errors.append(f"name_dorks failed: {exc}")

    relations = correlation.find_relations(targets, results)
    report_data = report.build_report(targets, results, relations, errors)

    wrote_file = False
    if args.output_json:
        _ensure_parent_dir(args.output_json)
        report.write_json(report_data, args.output_json)
        print(f"[+] JSON report written to {args.output_json}")
        wrote_file = True

    if args.output_html:
        _ensure_parent_dir(args.output_html)
        report.write_html(report_data, args.output_html)
        print(f"[+] HTML report written to {args.output_html}")
        wrote_file = True

    if args.output_all:
        json_path = f"{args.output_all}.json"
        html_path = f"{args.output_all}.html"
        _ensure_parent_dir(json_path)
        report.write_json(report_data, json_path)
        report.write_html(report_data, html_path)
        print(f"[+] JSON report written to {json_path}")
        print(f"[+] HTML report written to {html_path}")
        wrote_file = True

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
