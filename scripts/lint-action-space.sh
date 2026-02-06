#!/usr/bin/env bash
# lint-action-space.sh — Validate ACTION SPACE against CAES constraints
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
ACTION_SPACE="$REPO_ROOT/configs/gas/action-space.json"

echo "Validating ACTION SPACE: $ACTION_SPACE"

if [ ! -f "$ACTION_SPACE" ]; then
  echo "ERROR: action-space.json not found"
  exit 1
fi

# Check JSON validity
if ! jq empty "$ACTION_SPACE" 2>/dev/null; then
  echo "ERROR: Invalid JSON in action-space.json"
  exit 1
fi

echo "  JSON valid"

# Extract constraints
MRCC_MAX_C=$(jq -r '.mrcc.max_classification // "C5"' "$ACTION_SPACE" | sed 's/C//')
MRCC_MAX_S=$(jq -r '.mrcc.max_scope // "S5"' "$ACTION_SPACE" | sed 's/S//')
MRCC_MAX_E=$(jq -r '.mrcc.max_effect // "E5"' "$ACTION_SPACE" | sed 's/E//')

echo "  MRCC limits: C$MRCC_MAX_C, S$MRCC_MAX_S, E$MRCC_MAX_E"

# Validate each action
ERRORS=0
while IFS= read -r action; do
  ID=$(echo "$action" | jq -r '.id')
  CAES=$(echo "$action" | jq -r '.caes')
  STATUS=$(echo "$action" | jq -r '.status // "ALLOWED"')

  # Parse CAES code (portable grep)
  C_LEVEL=$(echo "$CAES" | grep -oE 'C[0-5]' | head -1 | sed 's/C//')
  S_LEVEL=$(echo "$CAES" | grep -oE 'S[0-5]' | head -1 | sed 's/S//')
  E_LEVEL=$(echo "$CAES" | grep -oE 'E[0-5]' | head -1 | sed 's/E//')

  # Check MRCC violations for ALLOWED actions
  if [ "$STATUS" = "ALLOWED" ]; then
    if [ "$C_LEVEL" -gt "$MRCC_MAX_C" ]; then
      echo "  ERROR: Action '$ID' exceeds MRCC classification (C$C_LEVEL > C$MRCC_MAX_C)"
      ERRORS=$((ERRORS + 1))
    fi
    if [ "$S_LEVEL" -gt "$MRCC_MAX_S" ]; then
      echo "  ERROR: Action '$ID' exceeds MRCC scope (S$S_LEVEL > S$MRCC_MAX_S)"
      ERRORS=$((ERRORS + 1))
    fi
    if [ "$E_LEVEL" -gt "$MRCC_MAX_E" ]; then
      echo "  ERROR: Action '$ID' exceeds MRCC effect (E$E_LEVEL > E$MRCC_MAX_E)"
      ERRORS=$((ERRORS + 1))
    fi
  fi

  # Check that forbidden actions have status FORBIDDEN or FORBIDDEN_WITHOUT_OVERRIDE
  if [ "$C_LEVEL" -ge 5 ] && [ "$STATUS" = "ALLOWED" ]; then
    echo "  ERROR: Action '$ID' is C5 but status is ALLOWED (should be FORBIDDEN*)"
    ERRORS=$((ERRORS + 1))
  fi

done < <(jq -c '.actions[]' "$ACTION_SPACE")

# Check forbidden actions list
FORBIDDEN_ACTIONS=$(jq -r '.mrcc.forbidden_actions[]' "$ACTION_SPACE" 2>/dev/null || echo "")
for forbidden in $FORBIDDEN_ACTIONS; do
  STATUS=$(jq -r ".actions[] | select(.id == \"$forbidden\") | .status" "$ACTION_SPACE")
  if [ "$STATUS" = "ALLOWED" ]; then
    echo "  ERROR: Action '$forbidden' is in forbidden list but status is ALLOWED"
    ERRORS=$((ERRORS + 1))
  fi
done

echo "  Checked $(jq '.actions | length' "$ACTION_SPACE") actions"

# Validate monotonic properties
if jq -e '.current_epoch.monotonic_properties' "$ACTION_SPACE" >/dev/null 2>&1; then
  echo "  Epoch monotonic properties defined"
else
  echo "  WARNING: No monotonic properties defined in current_epoch"
fi

if [ "$ERRORS" -gt 0 ]; then
  echo "FAILED: $ERRORS errors found"
  exit 1
fi

echo "PASSED: ACTION SPACE validates against CAES constraints"
