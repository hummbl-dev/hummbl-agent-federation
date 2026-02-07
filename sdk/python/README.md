# Federation Python SDK

Official Python SDK for the HUMMBL Agent Federation.

## Installation

```bash
pip install federation-sdk
```

## Quick Start

```python
from federation import FederationClient

# Initialize client
client = FederationClient(api_key="your-api-key")

# Route a task
response = client.route(
    prompt="Implement a JWT authentication middleware",
    constraints={"max_cost": 1.0, "max_latency": "5s"}
)

print(f"Selected: {response.provider}")
print(f"Cost: ${response.cost}")
print(f"Result: {response.content}")
```
