# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 1.1.x   | ✅ |
| < 1.1   | ❌ |

## Reporting a Vulnerability

- Please open a private security advisory (GitHub → Security → Report a vulnerability) or contact the maintainer directly.
- Include: affected version, reproduction steps, expected vs actual behavior.
- Expect a response within 7 days; fixes will land as a patch release with a CHANGELOG entry.

## Scope Notes

doc-claims is an offline, stdlib-only CLI. The security-relevant surface is deliberately small but real:

- **It executes shell commands** (`truth.cmd` from claims.json) — treat claims.json like a build script; do not commit or run configs from untrusted sources.
- Input docs are read as text and matched with regex; they are never executed.
- `--strict` and explicit skip-printing exist to prevent silent degradation, which is itself a correctness/trust property.
