#!/usr/bin/env bash
# gas-e2e-validate.sh — End-to-end validation for G.A.S. Agent
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "G.A.S. Agent E2E Validation"
echo "========================================"
echo ""

ERRORS=0
WARNINGS=0

# Helper functions
pass() { echo "  [PASS] $1"; }
fail() { echo "  [FAIL] $1"; ERRORS=$((ERRORS + 1)); }
warn() { echo "  [WARN] $1"; WARNINGS=$((WARNINGS + 1)); }
info() { echo "  [INFO] $1"; }

# 1. Agent Definition
echo "1. Agent Definition"
echo "-------------------"
AGENT_FILE="$REPO_ROOT/agents/hummbl-gas-agent.md"
if [ -f "$AGENT_FILE" ]; then
  pass "Agent file exists"

  # Check version
  VERSION=$(grep -E "^version:" "$AGENT_FILE" | head -1 | awk '{print $2}')
  if [ "$VERSION" = "1.0.0" ]; then
    pass "Version is 1.0.0"
  else
    warn "Version is $VERSION (expected 1.0.0)"
  fi

  # Check engine reference
  if grep -q "engine:" "$AGENT_FILE"; then
    pass "Engine reference present"
  else
    fail "Engine reference missing"
  fi
else
  fail "Agent file not found"
fi
echo ""

# 2. GV Domain Skills
echo "2. GV Domain Skills"
echo "-------------------"
GV_DIR="$REPO_ROOT/skills/GV-governance"
if [ -d "$GV_DIR" ]; then
  GV_COUNT=$(find "$GV_DIR" -maxdepth 1 -type d -name "gv*" | wc -l | tr -d ' ')
  if [ "$GV_COUNT" -ge 20 ]; then
    pass "GV domain has $GV_COUNT skills (expected 20)"
  else
    fail "GV domain has only $GV_COUNT skills (expected 20)"
  fi
else
  fail "GV domain directory not found"
fi
echo ""

# 3. Configuration Files
echo "3. Configuration Files"
echo "----------------------"
for config in \
  "configs/gas/governance-policy.json" \
  "configs/gas/action-space.json" \
  "configs/cost-policy.json"; do
  if [ -f "$REPO_ROOT/$config" ]; then
    if jq empty "$REPO_ROOT/$config" 2>/dev/null; then
      pass "$config (valid JSON)"
    else
      fail "$config (invalid JSON)"
    fi
  else
    fail "$config not found"
  fi
done
echo ""

# 4. GAS Engine Package
echo "4. GAS Engine Package"
echo "---------------------"
ENGINE_DIR="$REPO_ROOT/packages/gas-engine"
if [ -d "$ENGINE_DIR" ]; then
  pass "Engine package directory exists"

  # Check modules
  for module in types caes validator violations enforcer audit learning checkpoint; do
    if [ -f "$ENGINE_DIR/src/$module.ts" ]; then
      pass "Module: $module"
    else
      fail "Module missing: $module"
    fi
  done

  # Check tests
  TEST_COUNT=$(find "$ENGINE_DIR/tests" -name "*.test.ts" 2>/dev/null | wc -l | tr -d ' ')
  if [ "$TEST_COUNT" -ge 2 ]; then
    pass "Tests: $TEST_COUNT test files"
  else
    warn "Tests: only $TEST_COUNT test files"
  fi
else
  fail "Engine package not found"
fi
echo ""

# 5. Documentation
echo "5. Documentation"
echo "----------------"
for doc in \
  "docs/specs/ACTION_SPACE.md" \
  "docs/specs/ACTION_SPACE.v1.0.schema.json" \
  "docs/specs/AUDIT_SCHEMA.v1.0.json" \
  "docs/plans/2026-02-05-hummbl-gas-agent-design.md"; do
  if [ -f "$REPO_ROOT/$doc" ]; then
    pass "$doc"
  else
    fail "$doc not found"
  fi
done
echo ""

# 6. Scripts
echo "6. Scripts"
echo "----------"
for script in \
  "scripts/lint-gas-policy.sh" \
  "scripts/lint-action-space.sh" \
  "scripts/gas-rollback.sh"; do
  if [ -x "$REPO_ROOT/$script" ]; then
    pass "$script (executable)"
  elif [ -f "$REPO_ROOT/$script" ]; then
    warn "$script (exists but not executable)"
  else
    fail "$script not found"
  fi
done
echo ""

# 7. State Directory
echo "7. State Directory"
echo "------------------"
STATE_DIR="$REPO_ROOT/_state/gas"
if [ -d "$STATE_DIR" ]; then
  pass "State directory exists"
  for subdir in checkpoints audit learning; do
    if [ -d "$STATE_DIR/$subdir" ]; then
      pass "Subdirectory: $subdir"
    else
      warn "Subdirectory missing: $subdir"
    fi
  done
else
  fail "State directory not found"
fi
echo ""

# 8. Policy Validation
echo "8. Policy Validation"
echo "--------------------"
if [ -x "$SCRIPT_DIR/lint-gas-policy.sh" ]; then
  if "$SCRIPT_DIR/lint-gas-policy.sh" >/dev/null 2>&1; then
    pass "lint-gas-policy.sh passes"
  else
    fail "lint-gas-policy.sh failed"
  fi
else
  warn "lint-gas-policy.sh not executable"
fi
echo ""

# 9. ACTION SPACE Validation
echo "9. ACTION SPACE Validation"
echo "--------------------------"
if [ -x "$SCRIPT_DIR/lint-action-space.sh" ]; then
  if "$SCRIPT_DIR/lint-action-space.sh" >/dev/null 2>&1; then
    pass "lint-action-space.sh passes"
  else
    fail "lint-action-space.sh failed"
  fi
else
  warn "lint-action-space.sh not executable"
fi
echo ""

# 10. Integration Checks
echo "10. Integration Checks"
echo "----------------------"

# Check CAES constraints match between files
MRCC_C=$(jq -r '.mrcc.max_classification' "$REPO_ROOT/configs/gas/action-space.json" 2>/dev/null || echo "unknown")
if [ "$MRCC_C" = "C3" ]; then
  pass "MRCC classification limit: C3"
else
  warn "MRCC classification: $MRCC_C (expected C3)"
fi

# Check epoch is defined
EPOCH_ID=$(jq -r '.current_epoch.id' "$REPO_ROOT/configs/gas/action-space.json" 2>/dev/null || echo "unknown")
if [ "$EPOCH_ID" != "null" ] && [ "$EPOCH_ID" != "unknown" ]; then
  pass "Epoch defined: $EPOCH_ID"
else
  warn "No epoch defined"
fi

# Check forbidden actions
FORBIDDEN_COUNT=$(jq -r '.mrcc.forbidden_actions | length' "$REPO_ROOT/configs/gas/action-space.json" 2>/dev/null || echo "0")
if [ "$FORBIDDEN_COUNT" -ge 3 ]; then
  pass "Forbidden actions: $FORBIDDEN_COUNT defined"
else
  warn "Forbidden actions: only $FORBIDDEN_COUNT (expected >= 3)"
fi

echo ""
echo "========================================"
echo "Summary"
echo "========================================"
echo ""
if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
  echo "All checks passed!"
  echo ""
  echo "G.A.S. Agent v1.0.0 is ready for production."
  exit 0
elif [ "$ERRORS" -eq 0 ]; then
  echo "Passed with $WARNINGS warnings."
  echo ""
  echo "G.A.S. Agent is functional but has minor issues."
  exit 0
else
  echo "Failed with $ERRORS errors and $WARNINGS warnings."
  echo ""
  echo "Please fix errors before deployment."
  exit 1
fi
