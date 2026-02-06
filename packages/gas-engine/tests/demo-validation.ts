/**
 * Live Validation Demo
 * Runs validation against production action-space.json
 */

import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import {
  validateAction,
  validateActions,
  getAllowedActions,
  parseCAES,
  getLevel,
  isWithinConstraints,
  enforceAction,
  getViolationStats,
  clearViolations,
} from '../src/index';
import type { ActionSpace } from '../src/types';

// ESM compatibility
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Load production action space
const actionSpacePath = resolve(__dirname, '../../../configs/gas/action-space.json');
const actionSpace: ActionSpace = JSON.parse(readFileSync(actionSpacePath, 'utf-8'));

console.log('='.repeat(60));
console.log('HUMMBL G.A.S. Engine - Live Validation Demo');
console.log('='.repeat(60));
console.log();

// 1. Display action space summary
console.log('1. ACTION SPACE SUMMARY');
console.log('-'.repeat(40));
console.log(`   Version: ${actionSpace.version}`);
console.log(`   Total Actions: ${actionSpace.actions.length}`);
console.log(`   MRCC Limits: C${getLevel(actionSpace.mrcc.max_classification!)}, S${getLevel(actionSpace.mrcc.max_scope!)}, E${getLevel(actionSpace.mrcc.max_effect!)}`);
console.log(`   Forbidden: ${actionSpace.mrcc.forbidden_actions?.join(', ')}`);
console.log();

// 2. Get allowed actions
console.log('2. ALLOWED ACTIONS (within MRCC)');
console.log('-'.repeat(40));
const allowed = getAllowedActions(actionSpace);
console.log(`   Found ${allowed.length} allowed actions:`);
allowed.forEach((a) => {
  console.log(`   - ${a.id} (${a.caes})`);
});
console.log();

// 3. Validate specific actions
console.log('3. VALIDATION TESTS');
console.log('-'.repeat(40));

const testActions = [
  'read_policy',
  'flag_violation',
  'block_action',
  'expand_autonomy',
  'modify_own_boundaries',
  'unknown_action',
];

testActions.forEach((actionId) => {
  const result = validateAction(actionId, actionSpace, { actor: 'demo' });
  const status = result.valid ? '✓ VALID' : '✗ INVALID';
  console.log(`   ${status}: ${actionId}`);
  if (!result.valid && result.violations.length > 0) {
    result.violations.forEach((v) => {
      console.log(`      └─ ${v.violation_type} (${v.severity})`);
    });
  }
  if (result.recommendations) {
    result.recommendations.forEach((r) => {
      console.log(`      └─ Recommendation: ${r}`);
    });
  }
});
console.log();

// 4. Enforcement demo
console.log('4. ENFORCEMENT DEMO');
console.log('-'.repeat(40));
clearViolations();

const enforceTests = ['read_policy', 'flag_violation', 'expand_autonomy'];
enforceTests.forEach((actionId) => {
  const result = enforceAction(
    actionId,
    {
      actionSpace,
      policyRefs: ['gas-policy-v1'],
      base120Refs: ['IN1', 'DE3'],
    },
    { actor: 'demo-agent' }
  );
  console.log(`   ${actionId}: ${result.outcome}`);
  if (result.checkpoint_required) {
    console.log(`      └─ Checkpoint required: Yes`);
  }
  if (result.requires_approval) {
    console.log(`      └─ Requires approval: ${result.requires_approval.join(', ')}`);
  }
});
console.log();

// 5. Violation stats
console.log('5. VIOLATION STATISTICS');
console.log('-'.repeat(40));
const stats = getViolationStats();
console.log(`   Total violations: ${stats.total}`);
console.log(`   By severity:`);
Object.entries(stats.by_severity).forEach(([sev, count]) => {
  if (count > 0) console.log(`      - ${sev}: ${count}`);
});
console.log(`   By type:`);
Object.entries(stats.by_type).forEach(([type, count]) => {
  if (count > 0) console.log(`      - ${type}: ${count}`);
});
console.log();

// 6. CAES parsing demo
console.log('6. CAES PARSING');
console.log('-'.repeat(40));
const testCodes = ['C0-A0-E0-S1', 'C3-A2-E3-S3', 'C5-A4-E5-S4'];
testCodes.forEach((code) => {
  const parsed = parseCAES(code);
  if (parsed) {
    const withinMRCC = isWithinConstraints(
      parsed,
      actionSpace.mrcc.max_classification!,
      actionSpace.mrcc.max_scope!,
      actionSpace.mrcc.max_effect!
    );
    console.log(`   ${code}: ${withinMRCC ? 'Within MRCC' : 'EXCEEDS MRCC'}`);
  }
});
console.log();

// 7. Epoch info
console.log('7. EPOCH INFORMATION');
console.log('-'.repeat(40));
if (actionSpace.current_epoch) {
  console.log(`   ID: ${actionSpace.current_epoch.id}`);
  console.log(`   Started: ${actionSpace.current_epoch.started}`);
  console.log(`   Monotonic Properties:`);
  actionSpace.current_epoch.monotonic_properties.forEach((prop) => {
    console.log(`      - ${prop}`);
  });
}
console.log();

console.log('='.repeat(60));
console.log('Demo complete. All validations performed against production config.');
console.log('='.repeat(60));
