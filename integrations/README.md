# Integrations

Ourfeed ships with a first-class way to let a script or an AI agent post on
your behalf: generate a personal API token from `/automation.html`, then
call the API with it. Anything posted this way still lands in your drafts,
not straight on the feed, so the opt-out review step still applies.

## Authentication

Every `/api/entries*` route that normally checks your session cookie also
accepts an `Authorization: Bearer <token>` header instead. A token has the
exact same permissions as logging in as that user.

```
Authorization: Bearer of_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Minimal example: post a draft from a shell script

```bash
curl -X POST http://localhost:8731/api/entries \
  -H "Authorization: Bearer $OURFEED_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Deployed v1.2", "content": "Shipped the new caching layer.", "channels": ["work"]}'
```

## Minimal example: post a draft from Python

```python
import os, requests

requests.post(
    "http://localhost:8731/api/entries",
    headers={"Authorization": f"Bearer {os.environ['OURFEED_TOKEN']}"},
    json={"title": "Deployed v1.2", "content": "Shipped the new caching layer.", "channels": ["work"]},
)
```

## Wiring up an AI coding assistant

If you use something like Claude Code, Cursor, or another agent that can
call arbitrary HTTP endpoints, the pattern is the same: give the agent a
token, tell it "when you finish something worth sharing, POST a draft to
Ourfeed," and it lands in your drafts for you to confirm. There's nothing
Ourfeed-specific to install on the agent side, it's a plain HTTP call.

## Claude Code companion

[`claude-code-companion/`](claude-code-companion/) has a working, self-contained
example for Claude Code specifically: a script that scans your local session
logs and drafts posts based on what actually happened (realizations,
finished milestones, curiosity tangents, quotable lines, plus an optional
daily activity digest), and a pattern for making the live "ask your assistant
directly" flow persistent instead of something you re-paste every session.
Only needs the `claude` CLI, no other dependencies.

Other agents don't have an equivalent here yet, agent tooling and memory
mechanisms vary too much to write one generically. If you build one, a PR
that adds a short, working example (not just a description) is welcome.
