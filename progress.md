# Ourfeed progress

## Live

Public repo: https://github.com/JuneChoo/Ourfeed (pushed 2026-08-24, MIT
license auto-detected from LICENSE, topics set: self-hosted/feed/python/
sqlite/twitter-clone/ai-agent). Tagged and released as
[v1.0.0](https://github.com/JuneChoo/Ourfeed/releases/tag/v1.0.0).

## Current state (2026-08-24)

Phase 1 (accounts + config-driven channels) and a bilingual UI pass are both
done and verified. Backend confirmed via curl, full UI flow confirmed in an
actual browser (login, language toggle, compose, review/publish, feed,
admin invite codes), no console errors.

- Bootstrap: first registration becomes admin, no invite code needed
- `/api/config` correctly flips `bootstrap` to false after first user
- Invite codes: generate (admin only), redeem once, reject reuse, reject
  registration without a code once bootstrapped
- Session cookies: login/register set them, `/api/me` reads them, protected
  routes 401 without one
- Ownership: editing/privatizing someone else's entry correctly 403s
- Admin-only routes (`/api/invite-codes`) correctly 403 for members
- Entry lifecycle: draft to publish to visible in feed for all users; reply
  publishes immediately and inherits the parent's channels; multi-channel
  tagging (`["life","work"]`) round-trips correctly
- Language toggle switches all UI copy (nav, forms, toasts, alerts, relative
  timestamps, rule box) instantly, persists in localStorage, defaults to the
  browser's own language on first visit
- API tokens: generate/list/revoke all confirmed via curl and in-browser;
  a bearer token creates a draft with no cookie involved, lands in that
  user's own Drafts queue exactly like a manual post; revoked tokens 401
  immediately; `last_used_at` updates on use
- `OURFEED_DB_PATH` env var (for Docker's named volume) confirmed working:
  DB gets created at the custom path, not the default `ourfeed.db` next to
  the code
- **Docker packaging itself is NOT verified**, this machine doesn't have
  Docker installed. The Dockerfile/compose file follow standard patterns
  and the pieces that don't need Docker (env var override, .dockerignore
  contents) were tested, but nobody has actually run `docker compose up`
  against this yet. Do that before relying on it or mentioning it as
  "tested" anywhere public.

## What's built

- `ourfeed.py`: single-file backend, stdlib + sqlite3 only. Config-driven
  channels (`config.json`), real accounts (`users`/`invite_codes`/`sessions`
  tables), session-cookie auth (no `as`-in-body identity spoofing)
- `feed.html` / `review.html` / `login.html` / `register.html` / `admin.html`:
  bilingual (EN/ZH), channel-agnostic (render from `/api/config`, nothing
  hardcoded to "life"/"work")
- `ourfeed-common.js`: shared frontend logic, i18n dictionary and `t()`
  helper, Minecraft skin preserved, avatar/channel colors driven by inline
  CSS custom properties instead of hardcoded per-identity classes
- `docs/family-setup.md` + `docs/family-setup.zh.md`: non-technical guide
  for connecting family members across networks, recommends Tailscale with
  ready-to-send copy for both languages
- `automation.html` + `api_tokens` table: any logged-in user can generate a
  personal API token (separate from their session cookie) so a script or AI
  agent can post drafts under their account. This is the actual reason the
  opt-out review model exists (catching unreviewed automated content), so
  it's positioned as a core feature in the README, not an optional extra.
  `automation.html` itself is a real three-path walkthrough now (ask your
  AI assistant / no-code tool / write it yourself), not just a code block,
  generating a token auto-fills the real value into all three examples for
  that page visit.
- `GET /api/entries/mine?status=`: the current user's own entries in any
  state (draft/shared/private), needed so an automation script can check
  what happened to a draft it created earlier. Also the data source for a
  future "private archive" view.
- `integrations/claude-code-companion/`: a real, working, self-contained
  script (not just a description) that scans local Claude Code session
  logs and drafts posts based on realizations/milestones/curiosity
  tangents/quotable lines, plus a daily digest mode. Only needs the
  `claude` CLI, no shared config module or multi-provider LLM setup, so it
  actually runs for someone who just cloned the repo. Verified end-to-end
  against a throwaway instance (extraction, posting, and the
  privatize-driven negative-example feedback loop all work). Caught two
  real bugs while testing: the CLI refuses to launch from inside another
  Claude Code session unless `CLAUDECODE` is unset in the subprocess env,
  and small/fast models don't reliably follow the "no em dashes" prompt
  instruction, now enforced mechanically after generation instead of
  trusted to the prompt alone.
- `ROADMAP.md`: what's needed between now and a public v1.0 launch on X
- `start.bat` / `stop.bat` / `start-ourfeed.vbs`: Windows autostart, ported
  from yon-board's pattern but with the install path derived at runtime
  (`WScript.ScriptFullName`) instead of hardcoded, since any stranger can
  clone this to any folder
- Task/Kanban board from yon-board intentionally not ported, it's not part
  of the "shared feed" positioning per open-source-plan.md's scope
- `Dockerfile` / `docker-compose.yml` / `.dockerignore`: `python:3.12-alpine`
  base (nothing to `pip install`), DB path overridable via
  `OURFEED_DB_PATH` so it can live in a named volume separate from the code,
  `config.json` bind-mounted from the repo folder. See the untested-Docker
  note above.
- X launch copy drafted, kept out of this repo since it's marketing
  planning not project documentation: `d:\Yon\work\drafts\ourfeed-x-launch-2026-08-24.md`

## Next steps

Per `ROADMAP.md`, roughly in order:

1. **Run `docker compose up` against a real Docker install and fix whatever
   breaks** (nothing has actually exercised this yet)
2. Record a short demo GIF, add it to the top of the README (repo is live
   now, so the README is what people actually land on)
3. Post the X launch thread, draft is ready at
   `d:\Yon\work\drafts\ourfeed-x-launch-2026-08-24.md` with the repo link
   filled in, still needs June's voice pass before posting
4. `SECURITY.md` and `CONTRIBUTING.md` can trail the launch by a few days

## Known gaps / deliberate v1 limits

- No password self-reset (admin resets manually). Decided 2026-08-23, see
  yon-board's docs/open-source-plan.md section 三点五
- No Docker/systemd yet (Linux still needs a manual reverse-proxy/systemd
  setup, see ROADMAP.md)
- Channel config requires a server restart to take effect (not hot-reloaded)
- API tokens have no scoping: a token can do anything that user's session
  can do, not just create entries (matches the "good enough lock" bar, not
  enterprise IAM, documented in docs/architecture.md)

## 2026-08-24: public exposure, rate limiting, SECURITY.md

June wants to expose her instance to the public internet via Tailscale
Funnel for an X demo. Vercel was considered and rejected: serverless with
an ephemeral filesystem is fundamentally incompatible with local-SQLite
storage, would require rewriting the storage layer, not worth it.

Added before going public:
- Login and invite-code rate limiting: 5 failed attempts per IP locks that
  IP out for 5 minutes (`_login_rate_limited`/`_record_login_failure` in
  ourfeed.py). Verified: 6th failed login attempt correctly 429s, IP-based
  (not username-based) so rotating usernames from one IP doesn't bypass it,
  confirmed by testing a second username sharing the same lockout.
- `SECURITY.md`: states the threat model plainly (small trusted group,
  invite-only, rate limited but not hardened against sustained attack),
  with an explicit checklist for exposing an instance publicly
  (`cookie_secure: true`, use a disposable demo instance rather than a real
  one, don't hand out invite codes casually).
- README links to SECURITY.md from the Account model section.

Not yet done: Tailscale Funnel needs to be enabled at the tailnet admin
level (one-time action only June can do, link provided), and a decision on
whether to expose her real 8732 instance or spin up a separate clean demo
instance with sample content is still open.
