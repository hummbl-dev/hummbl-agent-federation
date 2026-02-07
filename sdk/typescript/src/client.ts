/**
 * Federation SDK client
 */

import type {
  RouteRequest,
  RouteResponse,
  RouteConstraints,
  FederationConfig,
  StreamChunk
} from './types';
import {
  FederationError,
  RoutingError,
  AuthenticationError
} from './errors';

export class FederationClient {
  private apiKey: string;
  private baseUrl: string;
  private timeout: number;

  constructor(config: FederationConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl || 'https://api.federation.hummbl.io/v1';
    this.timeout = config.timeout || 60000;
  }

  /**
   * Route a task to the optimal provider
   */
  async route(request: RouteRequest): Promise<RouteResponse> {
    const payload = {
      prompt: request.prompt,
      system_prompt: request.systemPrompt,
      constraints: request.constraints,
    };

    const response = await fetch(`${this.baseUrl}/route`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (response.status === 401) {
      throw new AuthenticationError('Invalid API key');
    }

    if (!response.ok) {
      const text = await response.text();
      throw new RoutingError(`Routing failed: ${text}`);
    }

    const data = await response.json();

    return {
      provider: data.provider,
      model: data.model,
      content: data.content,
      cost: data.cost,
      latencyMs: data.latency_ms,
      inputTokens: data.input_tokens,
      outputTokens: data.output_tokens,
      confidence: data.confidence,
      reasoning: data.reasoning,
      createdAt: new Date(),
    };
  }

  /**
   * Stream a task response
   */
  async *stream(request: RouteRequest): AsyncGenerator<StreamChunk> {
    const payload = {
      prompt: request.prompt,
      constraints: request.constraints,
      stream: true,
    };

    const response = await fetch(`${this.baseUrl}/route`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new RoutingError(`Streaming failed: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new RoutingError('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            yield { content: '', done: true };
            return;
          }
          try {
            const chunk = JSON.parse(data);
            yield { content: chunk.content || '', done: false };
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  }

  /**
   * Check API health
   */
  async health(): Promise<Record<string, unknown>> {
    const response = await fetch(`${this.baseUrl}/health`, {
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
      },
    });

    return response.json();
  }
}
