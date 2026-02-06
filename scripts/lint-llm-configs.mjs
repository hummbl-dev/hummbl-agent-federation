import { readFileSync } from "node:fs";

function fail(msg) {
  console.error(`[FAIL] ${msg}`);
  process.exit(1);
}

function guard(path) {
  const cfg = JSON.parse(readFileSync(path, "utf8"));
  if (cfg.enabled === true) fail(`${path}: enabled must remain false`);
  if (cfg.dry_run === false) fail(`${path}: dry_run must remain true`);
}

guard("configs/openclaw/llm.anthropic.json");
guard("configs/openclaw/llm.openai.json");

console.log("[OK] committed LLM configs remain disabled + dry_run");
