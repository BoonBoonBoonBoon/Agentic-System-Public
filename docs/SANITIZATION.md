# Sanitization & Safety
# Sanitization & Safety

Scope
- Public, portfolio-oriented snapshot. Functionality is safe-by-default; external side-effects are disabled.

What was removed
- All secrets (.env, keys, tokens) and any logs that might contain PII.
- Any delivery/webhook side-effects; `deliver_data` tool is disabled in public code.
- Real hostnames/IDs. Examples remain but do nothing without credentials.

Automation
- CI runs the offline test suite and a lightweight secret scan (`scripts/secret_scan.py`).
- Monitoring exporters mask token-like values and redact sensitive key names.

Local verification
```powershell
# run tests and secret scan locally
python -m pytest -q
python scripts/secret_scan.py
```

Environment policy
- `.env` files are ignored via `.gitignore`; never commit secrets.
- Prefer per-session environment variables in PowerShell when needed:
```powershell
$env:SUPABASE_URL="https://example.supabase.co"; $env:SUPABASE_SERVICE_KEY="<key>"
```

History hygiene (if secrets ever leaked)
- Rotate leaked keys with the provider.
- Rewrite history with `git filter-repo` or BFG to purge affected files/lines; then force-push branches.
- Re-run `scripts/secret_scan.py` on all branches after the rewrite.

Live integrations (opt-in only)
- Real integration tests are gated by `USE_REAL_TESTS=1` and require explicit env keys.
- Do not enable these in public CI; use only on private machines for manual verification.

Redaction
- See `platform_monitoring/exporters.py` for key-based redaction and token masking before logs are emitted.

