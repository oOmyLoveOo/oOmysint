# oOmysint

A small, modular OSINT CLI that collects publicly available information about a
target (username, email, domain, phone number or full name) from several
independent sources, correlates the results and compiles everything into a
single report (console, JSON and/or HTML).

Built as a coursework project. **For educational and authorized OSINT use
only** — only investigate targets you own or have explicit permission to
research.

![Demo report](examples/demo.png)

## What it does

| Input        | Module                        | Source |
|--------------|-------------------------------|--------|
| `--username` | `modules/username_lookup.py`  | **Sherlock** (external tool, run as a subprocess and its output parsed) — checks 400+ sites |
| `--email`    | `modules/email_breach.py`     | HaveIBeenPwned API if `HIBP_API_KEY` is set, otherwise the free **XposedOrNot** API |
| `--domain`   | `modules/domain_lookup.py`    | WHOIS + DNS (A / MX / NS / TXT records) |
| `--phone`    | `modules/phone_lookup.py`     | `phonenumbers` library — country, carrier, line type |
| `--name`     | `modules/name_dorks.py`       | Google dork links for manual follow-up |
| *(all)*      | `modules/correlation.py`      | Finds relations between the results (e.g. email ↔ domain, email ↔ username) |

Several inputs can be combined in one run; all results go into a single report.

Every input is validated, and every module fails gracefully: an invalid input,
a missing tool, a missing API key or a network error is reported as a status
inside the report instead of stopping the whole run.

## Installation

```bash
git clone https://github.com/<your-user>/oOmysint.git
cd oOmysint
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install sherlock-project      # external tool used by --username
```

This installs the `oomysint` command inside the virtualenv
(`python main.py ...` works too).

Optional: to use HaveIBeenPwned instead of XposedOrNot, copy `.env.example`
to `.env` and set `HIBP_API_KEY` (paid key from https://haveibeenpwned.com/API/Key).

## Usage

```bash
oomysint -u johndoe                       # username on social networks (Sherlock)
oomysint -e johndoe@example.com           # data breaches
oomysint -d example.com                   # WHOIS + DNS
oomysint -p '+34 612345678'               # phone number info
oomysint -n 'John Doe'                    # search links for a full name

# combine everything and save both reports
oomysint -u johndoe -e johndoe@example.com -d example.com \
         -p '+34 612345678' -n 'John Doe' -oA output/report
```

> zsh tip: use single quotes for values containing `!` or spaces.

Options:

```
-u, --username USER     Username to search across social networks (Sherlock)
-e, --email EMAIL       Email to check for data breaches
-d, --domain DOMAIN     Domain to analyze via WHOIS + DNS
-p, --phone PHONE       Phone number in international format (+34 ...)
-n, --name NAME         Full name to generate search links for
-oJ FILE                Write the JSON report to FILE
-oH FILE                Write the HTML report to FILE
-oA BASENAME            Write both BASENAME.json and BASENAME.html
--sherlock-timeout N    Timeout for Sherlock in seconds (default: 120)
```

Without any `-o` option the report is printed to the console only.

## Example run (fictitious data)

`johndoe` / `example.com` are placeholder values. The full output of this run
is in [`examples/`](examples/): [`demo.html`](examples/demo.html),
[`demo.json`](examples/demo.json) and the screenshot above.

```
$ oomysint -u johndoe -e johndoe@example.com -d example.com -p '+34 612345678' -n 'John Doe' -oA examples/demo
[*] Running Sherlock for username 'johndoe'...
[*] Running WHOIS + DNS for domain 'example.com'...
[*] Analyzing phone number '+34 612345678'...
[*] Checking data breaches for 'johndoe@example.com'...
[*] Generating lookup dorks for 'John Doe'...
[+] JSON report written to examples/demo.json
[+] HTML report written to examples/demo.html
```

Invalid input does not stop the run:

```
$ oomysint -u 'bad user!' -d not_a_domain -p 123
[*] Analyzing phone number '123'...
...
== phonenumbers == [ERROR]
  error: Invalid phone number (...). Use international format with '+', e.g. +34 612345678.

Errors:
  - Invalid username: 'bad user!'
  - Invalid domain: 'not_a_domain'
```

## Report structure

Both the HTML and JSON reports contain:

- **targets** — the inputs investigated
- **relations** — correlations found between the results
- **results** — one block per module, with a `source` and a `status`
  (`ok`, `error`, `not_configured`, `not_available`, `manual_followup`)
- **errors** — invalid inputs or modules that failed
- **limitations** (HTML) — what the tool cannot guarantee

## Project structure

```
oOmysint/
├── main.py                    # CLI entry point: parses args, runs modules
├── report.py                  # Console / JSON / HTML report output
├── modules/
│   ├── utils.py               # Shared validators and helpers
│   ├── username_lookup.py     # Sherlock integration (external tool)
│   ├── email_breach.py        # HaveIBeenPwned / XposedOrNot
│   ├── domain_lookup.py       # WHOIS + DNS
│   ├── phone_lookup.py        # phonenumbers
│   ├── name_dorks.py          # Search-link generator
│   └── correlation.py         # Relations between results
├── examples/                  # Demo report (fictitious data)
├── .env.example               # Optional API key config
├── pyproject.toml / requirements.txt
└── output/                    # Your reports (gitignored)
```

### Adding a new source

1. Create `modules/my_source.py` with one function that returns a dict with at
   least `source` and `status` keys.
2. Call it from `main.py` and store the result in `results["my_source"]`.

The report renders any new module automatically.

## Limitations

- Sherlock can give false positives/negatives depending on each site at run time.
- Breach data only covers publicly disclosed breaches (HIBP / XposedOrNot).
- WHOIS data varies by registrar and is often redacted for privacy (GDPR).
- `--name` only produces search links; full names are too ambiguous to resolve automatically.
- Relations are simple matches (hints), not proof that accounts belong to the same person.
- This is a learning project, not a production security tool.
