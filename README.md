# Ourfeed

A self-hosted, invite-only feed for the people who care where you're
headed, inner and outer: think a small Twitter/X for a family, a household,
or a tiny team. No framework, no build step, no database server, just
Python's standard library and SQLite.

## What makes it different

- **Opt-out review, not opt-in.** New posts land in your drafts by default,
  and doing *nothing* means they get published. You only have to act if you
  want to hold something back (mark it private, or skip this round). This
  flips the usual social-media friction, so sharing is the default and
  silence is never mistaken for holding back.
- **Multi-tag channels.** Every post can carry more than one tag at once
  (e.g. "life" and "work" for someone who's both family and a co-founder to
  you), configurable per deployment, not hardcoded.
- **Zero dependencies.** `python ourfeed.py` and you're running, or
  `docker compose up` if you'd rather not touch Python at all. No `pip
  install`, no external database either way.
- **Invite-only accounts.** Real username/password accounts, no email or SMTP
  required, since an admin hands out one-time invite codes instead.
- **Built for AI-assisted posting.** Generate a personal API token from
  `/automation.html` and let a script or an AI agent post drafts on your
  behalf. This is the actual reason the opt-out review model exists: it's
  the safety net for content nobody typed by hand, not just a quirky
  publishing flow. See [docs/architecture.md](docs/architecture.md#automated-posting-api-tokens).
- **English and Chinese out of the box.** The whole UI switches languages
  with one click, no server restart needed.

## Quick start

```bash
git clone <this repo>
cd Ourfeed
cp config.example.json config.json   # optional, edit site name / channels
python ourfeed.py
```

Or with Docker:

```bash
git clone <this repo>
cd Ourfeed
cp config.example.json config.json   # required for the Docker path, see note below
docker compose up
```

Open `http://localhost:8731`. The very first account you create becomes the
admin (no invite code needed). After that, the admin generates invite codes
from `/admin.html` for anyone else who should join.

Requires Python 3.9+ (bare metal) or Docker Compose. No other dependencies.

The Docker Compose file bind-mounts `config.json` from the repo folder, so
it has to exist before you run `docker compose up` (the bare Python path
auto-creates it from the example on first launch, Docker's bind mount can't
do that the same way). The SQLite database lives in a named Docker volume
(`ourfeed-data`), separate from the code, so `docker compose up` after a
rebuild doesn't lose your data.

Setting this up for family who aren't on your home network? See
[docs/family-setup.md](docs/family-setup.md), it covers connecting devices
across networks (we recommend Tailscale) plus copy you can send them
directly.

## Configuring channels

Edit `config.json`:

```json
{
  "site_name": "Ourfeed",
  "tagline": { "en": "A feed for the people who care where you're headed, inner and outer", "zh": "只讲给真正在乎你走到哪儿了的人听，精神和现实都算" },
  "port": 8731,
  "cookie_secure": false,
  "channels": [
    { "id": "life", "label": { "en": "Life", "zh": "生活" }, "icon": "🏠", "color": "#6cad3a" },
    { "id": "work", "label": { "en": "Work", "zh": "工作" }, "icon": "💼", "color": "#4a90d9" }
  ]
}
```

Add as many channels as you want, then restart the server to pick up
changes. `tagline` and each channel's `label` accept either a plain string
(shown regardless of language) or an `{en, zh}` object. Set
`cookie_secure: true` if you're running behind HTTPS (recommended for
anything reachable outside your own machine).

## Account model

- Registration requires an invite code, except for the very first account.
- No email/SMTP dependency by design. Forgot your password? The admin
  resets it directly (`sqlite3 ourfeed.db`, or a small script), there's no
  self-serve reset flow in v1.
- Sessions are plain server-side tokens in a cookie (`HttpOnly`,
  `SameSite=Lax`), not JWTs, since this is a small-scale, self-hosted tool
  and not an IAM system.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the data model and API
surface.

## Deployment

Runs anywhere Python 3.9+ runs, or anywhere Docker runs. See
[ROADMAP.md](ROADMAP.md) for what's still planned before v1.0 (a published
image on GHCR, one-click deploy templates).

**Docker (always-on):** `docker compose up -d` runs it detached with
`restart: unless-stopped`, so it comes back after a reboot or crash as long
as the Docker daemon itself is set to start on boot (the default on most
systems). `docker compose logs -f` to follow logs, `docker compose down` to
stop it.

**Windows (always-on):** run `start-ourfeed.vbs` to launch Ourfeed silently
in the background (no console window). To have it start automatically on
login, put a shortcut to `start-ourfeed.vbs` in your Startup folder
(`Win+R` then `shell:startup`), or add it as a Task Scheduler task set to
run at log on. `stop.bat` stops it. Logs go to `ourfeed.log` in the repo
folder.

**Linux/macOS (always-on):** put it behind a reverse proxy (Caddy/nginx)
with TLS if it needs to be reachable from outside your own machine, and run
the process under `systemd` or `supervisord` so it survives reboots.

## Connecting external tools

`/automation.html` covers letting a script or AI agent post on your behalf
(see "Built for AI-assisted posting" above). `integrations/` holds working
examples (curl, Python) for calling the API with a token.

## What this is not

- Not a multi-tenant SaaS, it's meant to be self-hosted per group.
- Not a plugin platform or theme marketplace.
- Not enterprise IAM: the account system is "a lock that's good enough for
  a household or small team," not OAuth/SSO/2FA.

## License

MIT, see [LICENSE](LICENSE).
