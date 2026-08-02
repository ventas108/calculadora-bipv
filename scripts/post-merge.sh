#!/bin/bash
set -e

# Install Node.js workspace dependencies (includes devDependencies for test/build tooling).
# --no-frozen-lockfile: allow lockfile updates when manifest versions drift between agents.
CI=true pnpm install --no-frozen-lockfile
