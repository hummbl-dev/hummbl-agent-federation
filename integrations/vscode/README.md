# Federation for VS Code

Official VS Code extension for the HUMMBL Agent Federation.

## Features

- 🎯 **Smart Model Selection** — Automatically pick the best provider
- 💰 **Cost Tracking** — See real-time spend in the status bar
- 🚀 **One-Click Routing** — Route code tasks to optimal providers
- 📊 **Provider Comparison** — Compare quality, speed, cost

## Usage

### Status Bar

The Federation status bar shows:
- Current provider (e.g., "DeepSeek 🔧")
- Session cost (e.g., "$0.45")
- Quick provider switcher

### Commands

- `Federation: Route Selection` — Send selected code to best provider
- `Federation: Compare Providers` — Benchmark on current file
- `Federation: Switch Provider` — Manual override

### Settings

```json
{
  "federation.apiKey": "your-api-key",
  "federation.defaultConstraints": {
    "maxCost": 1.0,
    "maxLatency": 5000
  }
}
```
