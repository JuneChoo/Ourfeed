# Ourfeed

A self-hosted, invite-only feed for the people you trust: think a small
Twitter/X for a family, a household, or a tiny team. No framework, no build
step, no database server, just Python's standard library and SQLite.

## What makes it different

- **Opt-out review, not opt-in.** New posts land in your drafts by default,
  and doing *nothing* means they get published. You only have to act if you
  want to hold something back (mark it private, or skip this round). This
  flips the usual social-media friction, so sharing is the default and
  silence is never mistaken for holding back.
- **Multi-tag channels.** Every post can carry more than one tag at once
  (e.g. "life" and "work" for someone who's both family and a co-founder to
  you), configurable per deployment, not hardcoded.
- **Zero dependencies.** `python ourfeed.py` and you're running. No `pip
  install`, no Docker required (though it's supported), no external database.
- **Invite-only accounts.** Real username/password accounts, no email or SMTP
  required, since an admin hands out one-time invite codes instead.
- **English and Chinese out of the box.** The whole UI switches languages
  with one click, no server restart needed.

## Quick start

```bash
git clone <this repo>
cd Ourfeed
cp config.example.json config.json   # optional, edit site name / channels
python ourfeed.py
```

Open `http://localhost:8731`. The very first account you create becomes the
admin (no invite code needed). After that, the admin generates invite codes
from `/admin.html` for anyone else who should join.

Requires Python 3.9+. No other dependencies.

Setting this up for family who aren't on your home network? See
[docs/family-setup.md](docs/family-setup.md), it covers connecting devices
across networks (we recommend Tailscale) plus copy you can send them
directly.

## Configuring channels

Edit `config.json`:

```json
{
  "site_name": "Ourfeed",
  "tagline": { "en": "A shared feed for the people you trust", "zh": "一个只属于信任的人的动态流" },
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

Runs anywhere Python 3.9+ runs. For always-on self-hosting, put it behind a
reverse proxy (Caddy/nginx) with TLS, or run it under `systemd` /
`supervisord`. Docker Compose support is planned but not in this release yet,
PRs welcome. See [ROADMAP.md](ROADMAP.md) for what's planned before v1.0.

## Optional integrations

`integrations/` holds examples for wiring Ourfeed into other tools (e.g. an
AI agent that drafts posts on your behalf via the API). These are examples,
not core features, Ourfeed works standalone.

## What this is not

- Not a multi-tenant SaaS, it's meant to be self-hosted per group.
- Not a plugin platform or theme marketplace.
- Not enterprise IAM: the account system is "a lock that's good enough for
  a household or small team," not OAuth/SSO/2FA.

## License

MIT, see [LICENSE](LICENSE).
