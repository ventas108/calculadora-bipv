#!/bin/bash
set -e

# Install Node.js workspace dependencies.
# Non-fatal: this project is primarily Python (BIPV Streamlit).
# pnpm install can fail transiently due to Replit package-firewall auth
# (ERR_PNPM_FETCH_403) without affecting the Python app.
CI=true pnpm install --no-frozen-lockfile || echo "⚠️  pnpm install failed (non-fatal — Python app unaffected)"
