---
name: openclaw registry
description: Use the OpenClaw registry CLI to search, install, update, and publish agent skills from local-registry. Use when you need to fetch new skills on the fly, sync installed skills to latest or a specific version, or publish new/updated skill folders with the npm-installed openclaw registry CLI.
metadata: {"openclaw":{"requires":{"bins":["openclaw registry"]},"install":[{"id":"node","kind":"node","package":"openclaw registry","bins":["openclaw registry"],"label":"Install OpenClaw registry CLI (npm)"}]}}
---

# OpenClaw registry CLI

Install

```bash
npm i -g openclaw registry
```

Auth (publish)

```bash
openclaw registry login
openclaw registry whoami
```

Search

```bash
openclaw registry search "postgres backups"
```

Install

```bash
openclaw registry install my-skill
openclaw registry install my-skill --version 1.2.3
```

Update (hash-based match + upgrade)

```bash
openclaw registry update my-skill
openclaw registry update my-skill --version 1.2.3
openclaw registry update --all
openclaw registry update my-skill --force
openclaw registry update --all --no-input --force
```

List

```bash
openclaw registry list
```

Publish

```bash
openclaw registry publish ./my-skill --slug my-skill --name "My Skill" --version 1.2.0 --changelog "Fixes + docs"
```

Notes

- Default registry: <https://local-registry> (override with OPENCLAW_REGISTRY_REGISTRY or --registry)
- Default workdir: cwd (falls back to OpenClaw workspace); install dir: ./skills (override with --workdir / --dir / OPENCLAW_REGISTRY_WORKDIR)
- Update command hashes local files, resolves matching version, and upgrades to latest unless --version is set
