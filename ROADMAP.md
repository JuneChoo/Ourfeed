# Roadmap: from working prototype to a real open-source product

This tracks what's needed between "code that works" and "something a
stranger will actually clone, trust, and keep running." Written with the
plan to launch publicly on X in mind.

## Already true

- Zero-dependency, single-command self-hosting (`python ourfeed.py`, no
  `pip install`, no build step)
- Real multi-user accounts with invite-only registration, not "assume
  everyone on your network is trusted"
- Bilingual UI (English/Chinese, one-click toggle, no restart needed)
- MIT licensed, data model and API documented in `docs/architecture.md`
- A concrete answer to "how does my non-technical family connect,"
  documented in `docs/family-setup.md`
- Built for AI-assisted posting: personal API tokens so a script or agent
  can post drafts, documented as a core feature, not a footnote
- Docker packaging (`Dockerfile` + `docker-compose.yml`), `docker compose up`
  works as a quickstart next to the bare `python ourfeed.py` path. SQLite
  data lives in a named volume, separate from the code, so rebuilds don't
  lose data. **Not yet tested against a real Docker install** (this
  environment doesn't have Docker), so treat it as needing a first real run
  before relying on it, see progress.md.
- Windows autostart (`start.bat` / `stop.bat` / `start-ourfeed.vbs`)

## Before the first public announcement (v0.9 to v1.0)

These are the things that decide whether someone who lands on the repo from
an X post actually tries it, in roughly the order they matter.

1. **A demo people can see in 10 seconds.** A README wall of text won't
   convert. Record a 60 to 90 second screen capture (compose a post, watch
   it move from drafts to the feed, toggle the language) and drop it as a
   GIF at the very top of the README, above the pitch. This is now the
   single highest-leverage thing left on this list.
2. **GitHub repo hygiene**, all cheap, all worth doing before the launch
   post rather than after:
   - Repo description and topics (`self-hosted`, `feed`, `python`,
     `sqlite`) so it surfaces in GitHub's own search
   - A social preview image (1280x640), a real screenshot of the feed, not
     a logo on a white background. This is what shows up when the repo link
     is pasted into X/Slack/Discord.
   - A tagged `v1.0.0` release with short release notes, not just a
     floating `master` branch. People check for tags as a maturity signal.
3. **`SECURITY.md`.** ~~Done~~ (2026-08-24, added along with basic login/
   invite-code rate limiting after actually exposing an instance to the
   public internet via Tailscale Funnel surfaced this as a real gap, not
   just a theoretical one). State the threat model plainly: small trusted
   group, invite-only, rate limited but not hardened against sustained
   attack, TLS via a reverse proxy or Funnel/Tunnel is the deployer's
   responsibility. Self-hosting audiences specifically check for this before
   trusting a
   project with an account system, and writing it honestly (rather than
   overselling security that isn't there) builds more trust, not less.
4. **`CONTRIBUTING.md`**, even a short one: how to run it locally, how to
   file a bug, what kind of PRs are welcome versus out of scope (the "what
   this is not" list in the README is a start). Signals the project is
   maintained and lowers the bar for the first outside contributor.

## Nice to have, not blocking launch

- Docker image published to GHCR so `docker run ghcr.io/...` works without
  cloning first
- CI (GitHub Actions) that at minimum runs `python -m py_compile
  ourfeed.py` and a curl-based smoke test of the API, similar to what was
  done manually before each commit so far
- One-click deploy templates (Railway/Render) for people who'd rather not
  run their own hardware
- GitHub Discussions once there are actual users asking questions (adding
  this before there's anyone to answer just makes the repo look empty)

## Explicitly deferred, not accidentally missing

Already ruled out in `docs/open-source-plan.md` and worth restating so
nobody re-litigates them mid-launch-prep: no plugin system, no theme
marketplace, no multi-tenant/SaaS mode, no task/Kanban board (out of the
"shared feed" scope). Small and boring on purpose.

## Suggested order of operations

1. ~~Docker Compose~~ done, needs a first real test against an actual Docker
   install before trusting it
2. Record the demo GIF using the current Minecraft UI
3. Push to GitHub, tag `v1.0.0`, rebuild the README's opening around the GIF
4. Launch post on X
5. `SECURITY.md` and `CONTRIBUTING.md` can trail the launch by a few days
   without hurting first impressions; CI and the GHCR image can wait for
   actual usage signal

## A note on the launch post itself

The strongest angle isn't "another self-hosted app," it's the opt-out
review mechanism: most social tools make sharing something you opt into,
which means people quietly stop posting. Ourfeed inverts that so silence
gets published by default and holding something back is the one deliberate
action. That's the one sentence worth leading with, everything else
(zero-dependency, self-hosted, bilingual) is supporting detail, not the
hook.
