# Ourfeed progress

## Current state (2026-08-23)

Phase 1 core is built and smoke-tested via curl (not yet verified in an
actual browser — chrome-devtools MCP couldn't attach, existing Chrome
profile was locked by another process). Backend logic confirmed working:

- Bootstrap: first registration becomes admin, no invite code needed
- `/api/config` correctly flips `bootstrap` to false after first user
- Invite codes: generate (admin-only), redeem once, reject reuse, reject
  registration without a code once bootstrapped
- Session cookies: login/register set them, `/api/me` reads them, protected
  routes 401 without one
- Ownership: editing/privatizing someone else's entry correctly 403s
- Admin-only routes (`/api/invite-codes`) correctly 403 for members
- Entry lifecycle: draft → publish → visible in feed to all users; reply
  publishes immediately and inherits parent's channels; multi-channel
  tagging (`["life","work"]`) round-trips correctly

## What's built

- `ourfeed.py` — single-file backend, stdlib + sqlite3 only. Config-driven
  channels (`config.json`), real accounts (`users`/`invite_codes`/`sessions`
  tables), session-cookie auth replacing the old `as`-in-body identity model
- `feed.html` / `review.html` / `login.html` / `register.html` / `admin.html`
  — all English-language, all channel-agnostic (render from `/api/config`,
  no hardcoded "life"/"work")
- `ourfeed-common.js` / `ourfeed-common.css` — shared frontend logic/visual
  system, Minecraft skin preserved, avatar/channel colors now driven by
  inline CSS custom properties instead of hardcoded per-identity classes
- Task/Kanban board from yon-board intentionally **not** ported — it's not
  part of the "shared feed" positioning per open-source-plan.md's scope
  (see docs/architecture.md for what's in/out)

## Next steps

1. **Browser verification** — retry chrome-devtools MCP (or manual browser
   test) once the profile lock clears: full click-through of
   register → login → post → review → publish → feed → reply → logout
2. **git init + first commit**, then decide: push to GitHub now or after
   browser verification passes
3. Phase 2 (deferred, per open-source-plan.md): Docker Compose, systemd
   unit, cross-platform deploy docs
4. Phase 3: polish README with actual screenshots once there's real UI to
   show

## Known gaps / deliberate v1 limits

- No password self-reset (admin resets manually) — decided 2026-08-23, see
  yon-board's docs/open-source-plan.md section 三点五
- No Docker/systemd yet (Phase 2)
- Channel config requires a server restart to take effect (not hot-reloaded)
