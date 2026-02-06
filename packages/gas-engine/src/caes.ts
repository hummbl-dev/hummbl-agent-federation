/**
 * CAES Code Parser and Utilities
 */

import type {
  CAESCode,
  ClassificationLevel,
  AuthorityLevel,
  EffectLevel,
  ScopeLevel,
} from './types';

// Parse CAES string (e.g., "C2-A1-E2-S2") into components
export const parseCAES = (caes: string): CAESCode | null => {
  const pattern = /^(C[0-5])-(A[0-5](?:-[A-Z]+)?)-?(E[0-5](?:-[A-Z]+)?)-?(S[0-5](?:-[A-Z]+)?)$/;
  const match = caes.match(pattern);

  if (!match) {
    // Try simplified format: C2-A1-E2-S2
    const simple = /^(C[0-5])-(A[0-5])-(E[0-5])-(S[0-5])$/;
    const simpleMatch = caes.match(simple);
    if (!simpleMatch) return null;

    return {
      classification: simpleMatch[1] as ClassificationLevel,
      authority: `${simpleMatch[2]}-SELF` as AuthorityLevel,
      effect: `${simpleMatch[3]}-PURE` as EffectLevel,
      scope: `${simpleMatch[4]}-SELF` as ScopeLevel,
    };
  }

  return {
    classification: match[1] as ClassificationLevel,
    authority: match[2] as AuthorityLevel,
    effect: match[3] as EffectLevel,
    scope: match[4] as ScopeLevel,
  };
};

// Extract numeric level from CAES component
export const getLevel = (component: string): number => {
  const match = component.match(/[CAES](\d)/);
  return match ? parseInt(match[1], 10) : -1;
};

// Compare two CAES codes
export const compareCAES = (a: CAESCode, b: CAESCode): number => {
  const cDiff = getLevel(a.classification) - getLevel(b.classification);
  if (cDiff !== 0) return cDiff;

  const aDiff = getLevel(a.authority) - getLevel(b.authority);
  if (aDiff !== 0) return aDiff;

  const eDiff = getLevel(a.effect) - getLevel(b.effect);
  if (eDiff !== 0) return eDiff;

  return getLevel(a.scope) - getLevel(b.scope);
};

// Check if action CAES is within constraints
export const isWithinConstraints = (
  actionCAES: CAESCode,
  maxC: ClassificationLevel,
  maxS: ScopeLevel,
  maxE: EffectLevel
): boolean => {
  return (
    getLevel(actionCAES.classification) <= getLevel(maxC) &&
    getLevel(actionCAES.scope) <= getLevel(maxS) &&
    getLevel(actionCAES.effect) <= getLevel(maxE)
  );
};

// Format CAES code to string
export const formatCAES = (caes: CAESCode): string => {
  return `${caes.classification}-${caes.authority}-${caes.effect}-${caes.scope}`;
};

// Get risk description for classification level
export const getRiskDescription = (level: ClassificationLevel): string => {
  const descriptions: Record<ClassificationLevel, string> = {
    C0: 'None - Pure observation',
    C1: 'Low - Reversible changes',
    C2: 'Medium - Significant, reviewable',
    C3: 'High - Enforcement, limited reversal',
    C4: 'Critical - Structural changes',
    C5: 'Restricted - Self-modification',
  };
  return descriptions[level];
};

// Get authority description
export const getAuthorityDescription = (level: AuthorityLevel): string => {
  const descriptions: Record<AuthorityLevel, string> = {
    'A0-SELF': 'Self-authorized',
    'A1-NOTIFY': 'Self + notify owner',
    'A2-REVIEW': 'Requires review',
    'A3-APPROVE': 'Requires explicit approval',
    'A4-MULTI': 'Requires multi-party approval',
    'A5-EMERGENCY': 'Emergency/security only',
  };
  return descriptions[level] ?? 'Unknown authority level';
};
