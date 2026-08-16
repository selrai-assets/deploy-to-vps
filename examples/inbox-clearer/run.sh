#!/usr/bin/env bash
# One run of the inbox-clearer automation. Exit 0 means the brief was sent.
set -euo pipefail
cd "$(dirname "$0")"

# Credentials that deploy synced land in .credentials/. On the box the gws CLI
# reads its config from there with the file keyring backend. On your own laptop
# the folder is absent and gws uses the sign-in already on the machine.
if [ -d .credentials/gws ]; then
  export GOOGLE_WORKSPACE_CLI_CONFIG_DIR="$PWD/.credentials/gws"
  export GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file
fi

# Optional: .credentials/env holds KEY=value lines, loaded for every run.
if [ -f .credentials/env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.credentials/env
  set +a
fi

exec python3 -u clear_inbox.py "$@"
