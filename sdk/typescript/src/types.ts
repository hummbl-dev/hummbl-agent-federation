/**
 * Type definitions for Federation SDK
 */

export interface RouteConstraints {
  maxCost?: number;
  maxLatency?: number;
  dataResidency?: 'us' | 'eu' | 'apac' | 'local';
  gdprRequired?: boolean;
  soc2Required?: boolean;
  hipaaRequired?: boolean;
  providerPreference?: string;
}

export interface RouteRequest {
  prompt: string;
  systemPrompt?: string;
  constraints?: RouteConstraints;
  stream?: boolean;
}

export interface RouteResponse {
  provider: string;
  model: string;
  content: string;
  cost: number;
  latencyMs: number;
  inputTokens: number;
  outputTokens: number;
  confidence: number;
  reasoning: string;
  createdAt: Date;
}

export interface FederationConfig {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
}

export interface StreamChunk {
  content: string;
  done: boolean;
}
