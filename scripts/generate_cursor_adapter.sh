#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="${ROOT_DIR}/.cursor/skills"
DOCS_TARGET_DIR="${ROOT_DIR}/docs/ai/skills"

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "Source directory not found: ${SOURCE_DIR}" >&2
  exit 1
fi

mkdir -p "${DOCS_TARGET_DIR}"

# Keep legacy docs mirror in sync with canonical Cursor source.
rsync -a --delete --exclude "README.md" "${SOURCE_DIR}/" "${DOCS_TARGET_DIR}/"

cat > "${DOCS_TARGET_DIR}/README.md" <<'EOF'
# Agent Skills Docs Mirror (Generated)

This directory is a generated legacy/reference mirror for agent skills.
Do not edit files here manually.

Canonical source of truth:

- .cursor/skills/

To refresh this mirror, run:

- ./scripts/generate_cursor_adapter.sh
EOF

echo "Synced skills:"
echo "  source: ${SOURCE_DIR}"
echo "  target: ${DOCS_TARGET_DIR}"
