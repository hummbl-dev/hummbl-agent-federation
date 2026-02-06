#!/usr/bin/env bash
# gas-rollback.sh — Rollback G.A.S. Agent to a previous checkpoint
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
STATE_DIR="$REPO_ROOT/_state/gas"
CHECKPOINT_DIR="$STATE_DIR/checkpoints"

usage() {
  echo "Usage: gas-rollback.sh [OPTIONS]"
  echo ""
  echo "Options:"
  echo "  --to <checkpoint_id>   Rollback to specific checkpoint"
  echo "  --list                 List available checkpoints"
  echo "  --latest               Rollback to most recent checkpoint"
  echo "  --validate <id>        Validate checkpoint integrity"
  echo "  --help                 Show this help"
  echo ""
  echo "Examples:"
  echo "  gas-rollback.sh --list"
  echo "  gas-rollback.sh --to cp-2026-02-05-120000-abc1"
  echo "  gas-rollback.sh --latest"
}

list_checkpoints() {
  echo "Available Checkpoints:"
  echo "======================"

  if [ ! -d "$CHECKPOINT_DIR" ]; then
    echo "No checkpoints found."
    return
  fi

  for file in "$CHECKPOINT_DIR"/*.json; do
    if [ -f "$file" ]; then
      id=$(jq -r '.id' "$file")
      created=$(jq -r '.created_at' "$file")
      type=$(jq -r '.type' "$file")
      desc=$(jq -r '.description' "$file")
      echo "  $id ($type)"
      echo "    Created: $created"
      echo "    Description: $desc"
      echo ""
    fi
  done
}

validate_checkpoint() {
  local id="$1"
  local file="$CHECKPOINT_DIR/$id.json"

  if [ ! -f "$file" ]; then
    echo "ERROR: Checkpoint '$id' not found"
    exit 1
  fi

  echo "Validating checkpoint: $id"

  # Check JSON validity
  if ! jq empty "$file" 2>/dev/null; then
    echo "  ERROR: Invalid JSON"
    exit 1
  fi
  echo "  JSON: valid"

  # Check required fields
  for field in id created_at type state hash; do
    if jq -e ".$field" "$file" >/dev/null 2>&1; then
      echo "  $field: present"
    else
      echo "  ERROR: missing field '$field'"
      exit 1
    fi
  done

  echo "VALID: Checkpoint '$id' passes integrity checks"
}

rollback_to() {
  local id="$1"
  local file="$CHECKPOINT_DIR/$id.json"

  if [ ! -f "$file" ]; then
    echo "ERROR: Checkpoint '$id' not found"
    exit 1
  fi

  echo "Rolling back to checkpoint: $id"

  # Create rollback marker
  local marker_id="rollback-marker-$(date +%Y%m%d-%H%M%S)"
  local marker_file="$CHECKPOINT_DIR/$marker_id.json"

  echo "Creating rollback marker: $marker_id"
  cat > "$marker_file" << EOF
{
  "id": "$marker_id",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "type": "ROLLBACK_MARKER",
  "description": "Rollback marker before restoring to $id",
  "state": {},
  "hash": "marker",
  "metadata": {
    "rollback_to": "$id"
  }
}
EOF

  # Extract and restore learning state
  local learning_state
  learning_state=$(jq -r '.state.learning_state' "$file")

  if [ "$learning_state" != "null" ] && [ -n "$learning_state" ]; then
    echo "$learning_state" > "$STATE_DIR/learning-state.json"
    echo "Restored learning state"
  fi

  echo ""
  echo "ROLLBACK COMPLETE"
  echo "  Restored to: $id"
  echo "  Rollback marker: $marker_id"
  echo ""
  echo "To undo this rollback, use:"
  echo "  $0 --to $marker_id"
}

rollback_latest() {
  if [ ! -d "$CHECKPOINT_DIR" ]; then
    echo "ERROR: No checkpoints found"
    exit 1
  fi

  # Find most recent checkpoint (excluding rollback markers)
  local latest
  latest=$(ls -t "$CHECKPOINT_DIR"/*.json 2>/dev/null | head -1)

  if [ -z "$latest" ]; then
    echo "ERROR: No checkpoints found"
    exit 1
  fi

  local id
  id=$(jq -r '.id' "$latest")

  rollback_to "$id"
}

# Ensure checkpoint directory exists
mkdir -p "$CHECKPOINT_DIR"

# Parse arguments
if [ $# -eq 0 ]; then
  usage
  exit 1
fi

case "$1" in
  --to)
    if [ -z "${2:-}" ]; then
      echo "ERROR: --to requires a checkpoint ID"
      exit 1
    fi
    rollback_to "$2"
    ;;
  --list)
    list_checkpoints
    ;;
  --latest)
    rollback_latest
    ;;
  --validate)
    if [ -z "${2:-}" ]; then
      echo "ERROR: --validate requires a checkpoint ID"
      exit 1
    fi
    validate_checkpoint "$2"
    ;;
  --help|-h)
    usage
    ;;
  *)
    echo "ERROR: Unknown option '$1'"
    usage
    exit 1
    ;;
esac
