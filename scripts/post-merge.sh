#!/bin/bash
set -e

# Install Node.js workspace dependencies.
# --prod:               skip devDependencies (vitest etc. blocked by Replit firewall)
# --no-frozen-lockfile: allow lockfile updates when settings drift between agents
CI=true pnpm install --prod --no-frozen-lockfile
