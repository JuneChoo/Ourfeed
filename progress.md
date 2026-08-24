# Ourfeed progress

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
  `integrations/README.md` has working curl/Python examples.
- `ROADMAP.md`: what's needed between now and a public v1.0 launch on X
- `start.bat` / `stop.bat` / `start-ourfeed.vbs`: Windows autostart, ported
  from yon-board's pattern but with the install path derived at runtime
  (`WScript.ScriptFullName`) instead of hardcoded, since any stranger can
  clone this to any folder
- Task/Kanban board from yon-board intentionally not ported, it's not part
  of the "shared feed" positioning per open-source-plan.md's scope

## Next steps

Per `ROADMAP.md`, roughly in order:

1. Docker Compose + Dockerfile (highest-leverage gap for the self-hosting
   crowd, most people evaluating a self-hosted project check for this first)
2. Record a short demo GIF for the top of the README
3. Push to GitHub, tag `v1.0.0`
4. Write and post the X launch thread (lead with the opt-out review
   mechanism, not the tech stack, see ROADMAP.md's closing note)
5. `SECURITY.md` and `CONTRIBUTING.md` can trail the launch by a few days

## Known gaps / deliberate v1 limits

- No password self-reset (admin resets manually). Decided 2026-08-23, see
  yon-board's docs/open-source-plan.md section 三点五
- No Docker/systemd yet (Linux still needs a manual reverse-proxy/systemd
  setup, see ROADMAP.md)
- Channel config requires a server restart to take effect (not hot-reloaded)
- No login rate limiting yet (tracked in ROADMAP.md's SECURITY.md item)
- API tokens have no scoping: a token can do anything that user's session
  can do, not just create entries (matches the "good enough lock" bar, not
  enterprise IAM, documented in docs/architecture.md)
