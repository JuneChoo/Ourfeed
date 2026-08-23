# Ourfeed

Open-source spin-off of `yon-board` (June's private instance, separate repo).
Positioning: a self-hosted "family/small-team Twitter/X" with opt-out review
and multi-tag channels. See [README.md](README.md) for the pitch and
[docs/architecture.md](docs/architecture.md) for the data model/API.

## Rules

- Zero dependencies is a hard constraint — stdlib + SQLite only, no pip
  installs, no build step. This is the product's main differentiator for
  self-hosters.
- Identities and channels must stay configurable, never hardcoded to a
  specific person or team's vocabulary — this repo is meant for strangers to
  deploy for themselves.
- Minecraft visual skin is the only skin (decided, not up for redesign
  without asking June first).
- English-first for all user-facing copy (this is the open-source public
  repo — `yon-board` stays Chinese/internal).

## Progress

See [progress.md](progress.md).
