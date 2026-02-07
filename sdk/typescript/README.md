# Federation TypeScript SDK

Official TypeScript/JavaScript SDK for the HUMMBL Agent Federation.

## Installation

```bash
npm install @hummbl/federation-sdk
```

## Quick Start

```typescript
import { FederationClient } from '@hummbl/federation-sdk';

const client = new FederationClient({
  apiKey: 'your-api-key'
});

const response = await client.route({
  prompt: 'Implement a JWT authentication middleware',
  constraints: {
    maxCost: 1.0,
    maxLatency: 5000
  }
});

console.log(`Selected: ${response.provider}`);
console.log(`Cost: $${response.cost}`);
console.log(`Result: ${response.content}`);
```

## Streaming

```typescript
for await (const chunk of client.stream('Write a story...')) {
  process.stdout.write(chunk.content);
}
```
