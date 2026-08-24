# Ourfeed

Open-source spin-off of `yon-board` (June's private instance, separate repo).
Positioning: a self-hosted "family/small-team Twitter/X" with opt-out review
and multi-tag channels. See [README.md](README.md) for the pitch and
[docs/architecture.md](docs/architecture.md) for the data model/API.

## Rules

- Zero dependencies is a hard constraint: stdlib + SQLite only, no pip
  installs, no build step. This is the product's main differentiator for
  self-hosters.
- Identities and channels must stay configurable, never hardcoded to a
  specific person or team's vocabulary. This repo is meant for strangers to
  deploy for themselves.
- Minecraft visual skin is the only skin (decided, not up for redesign
  without asking June first).
- UI ships bilingual (English/Chinese, toggle in the header) since June
  plans to launch this publicly on X. All new user-facing strings go through
  the `I18N` dict in `ourfeed-common.js`, never hardcoded text in HTML.
- No em dashes or en dashes anywhere (README, docs, code comments, commit
  messages). Use commas, periods, colons, or parentheses instead.
- Roadmap to a public v1.0 launch lives in [ROADMAP.md](ROADMAP.md).

## Progress

See [progress.md](progress.md).
