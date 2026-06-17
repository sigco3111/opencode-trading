# Security Policy

## Supported versions

| Version | Supported          |
|---------|--------------------|
| 0.4.x   | :white_check_mark: |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

The latest minor release receives security fixes. Older minors are
supported on a best-effort basis for 90 days after the next minor ships.

## Reporting a vulnerability

**Please do not file a public issue for security problems.**

Report privately via one of:

1. **GitHub Security Advisories** (preferred):
   <https://github.com/sigco3111/opencode-trading/security/advisories/new>
2. **Email**: open an issue first asking for the maintainer's contact
   address; we will respond within 72 hours with a private channel.

Please include:

- A description of the vulnerability and its impact
- Reproduction steps (minimal command or snippet)
- Affected version(s) and commit SHA(s)
- Your assessment of severity (CVSS if available)

## Response timeline

- **Initial acknowledgement**: within 72 hours of the report
- **Triage and severity assignment**: within 7 days
- **Patch release for CRITICAL/HIGH**: within 30 days
- **Patch release for MEDIUM/LOW**: bundled into the next minor release
- **Public disclosure**: coordinated with the reporter, no earlier than
  30 days after the patch ships

## Scope

This project is an **adapter** with zero runtime dependencies. The
threat model is limited to:

- Malicious input workspaces passed to `convert_workspace()` /
  `attach_workspace()` — we never `shell` / `os.system` / `eval` user
  paths, and the bundled YAML/TOML parsers are strict (no pickle, no
  dynamic import).
- The bundled TCX v0.2.0 templates are inert; treat any future bump to
  a newer TCX version as a supply-chain change requiring review.

Vulnerabilities in the upstream
[monarchjuno/tradingcodex](https://github.com/monarchjuno/tradingcodex)
should be reported to that project, not this one.

## Recognition

We follow a [coordinated disclosure](https://en.wikipedia.org/wiki/Coordinated_vulnerability_disclosure)
model. Reporters who follow this policy will be credited in the release
notes (unless they prefer anonymity).
