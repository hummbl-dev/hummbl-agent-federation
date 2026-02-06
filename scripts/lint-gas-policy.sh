#!/usr/bin/env bash
# lint-gas-policy.sh — Validate G.A.S. governance policy configuration
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
GAS_CONFIG="$REPO_ROOT/configs/gas"

echo "Validating G.A.S. Policy Configuration"
echo "======================================="

ERRORS=0

# Check governance-policy.json
POLICY_FILE="$GAS_CONFIG/governance-policy.json"
if [ -f "$POLICY_FILE" ]; then
  echo "Checking: governance-policy.json"
  if jq empty "$POLICY_FILE" 2>/dev/null; then
    echo "  JSON valid"

    # Check required fields
    for field in version autonomy approval_gates escalation audit; do
      if jq -e ".$field" "$POLICY_FILE" >/dev/null 2>&1; then
        echo "  $field: present"
      else
        echo "  ERROR: missing required field '$field'"
        ERRORS=$((ERRORS + 1))
      fi
    done

    # Check action_space reference
    if jq -e '.action_space' "$POLICY_FILE" >/dev/null 2>&1; then
      echo "  action_space: referenced"
    else
      echo "  WARNING: action_space not referenced"
    fi
  else
    echo "  ERROR: Invalid JSON"
    ERRORS=$((ERRORS + 1))
  fi
else
  echo "ERROR: governance-policy.json not found"
  ERRORS=$((ERRORS + 1))
fi

echo ""

# Check action-space.json
ACTION_FILE="$GAS_CONFIG/action-space.json"
if [ -f "$ACTION_FILE" ]; then
  echo "Checking: action-space.json"
  if jq empty "$ACTION_FILE" 2>/dev/null; then
    echo "  JSON valid"

    # Check required fields
    for field in version actions mrcc ncc; do
      if jq -e ".$field" "$ACTION_FILE" >/dev/null 2>&1; then
        echo "  $field: present"
      else
        echo "  ERROR: missing required field '$field'"
        ERRORS=$((ERRORS + 1))
      fi
    done

    # Count actions
    ACTION_COUNT=$(jq '.actions | length' "$ACTION_FILE")
    echo "  actions: $ACTION_COUNT defined"

    # Validate CAES codes
    echo "  Validating CAES codes..."
    CAES_ERRORS=0
    while IFS= read -r action; do
      ID=$(echo "$action" | jq -r '.id')
      CAES=$(echo "$action" | jq -r '.caes')
      if ! echo "$CAES" | grep -qE '^C[0-5]-A[0-5]-E[0-5]-S[0-5]$'; then
        echo "    ERROR: Invalid CAES code for '$ID': $CAES"
        CAES_ERRORS=$((CAES_ERRORS + 1))
      fi
    done < <(jq -c '.actions[]' "$ACTION_FILE")

    if [ "$CAES_ERRORS" -eq 0 ]; then
      echo "    All CAES codes valid"
    else
      ERRORS=$((ERRORS + CAES_ERRORS))
    fi
  else
    echo "  ERROR: Invalid JSON"
    ERRORS=$((ERRORS + 1))
  fi
else
  echo "ERROR: action-space.json not found"
  ERRORS=$((ERRORS + 1))
fi

echo ""

# Run action-space specific validation
if [ -x "$SCRIPT_DIR/lint-action-space.sh" ]; then
  echo "Running ACTION SPACE validation..."
  if "$SCRIPT_DIR/lint-action-space.sh"; then
    echo "  ACTION SPACE validation passed"
  else
    echo "  ACTION SPACE validation failed"
    ERRORS=$((ERRORS + 1))
  fi
fi

echo ""
echo "======================================="
if [ "$ERRORS" -gt 0 ]; then
  echo "FAILED: $ERRORS errors found"
  exit 1
fi

echo "PASSED: All G.A.S. policy checks passed"
