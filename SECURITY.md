# Security

Ourfeed is built for a small trusted group (a family, a household, a tiny
team), not as internet-facing software with a large, adversarial user base.
That shapes what's here and what isn't. Read this before exposing an
instance to the public internet, not after.

## What's in place

- **Passwords**: hashed with `hashlib.pbkdf2_hmac` (SHA-256, 200,000
  iterations), salted per-user. Never stored or logged in plaintext.
- **Sessions**: random tokens (`secrets.token_urlsafe(32)`), stored
  server-side, sent via an `HttpOnly`, `SameSite=Lax` cookie. Not JWTs, not
  guessable, not readable from JavaScript.
- **Registration is invite-only** after the first account. A stranger who
  finds your URL can see the login page, nothing else, they can't view any
  content or create an account without a code you generated.
- **API tokens** (for automation) carry the same permissions as the user
  who created them, no more. Revoking one takes effect immediately.
- **Login and registration are rate limited**: 5 failed attempts from an IP
  locks that IP out for 5 minutes, across both login and invite-code
  guessing. This is deliberately simple (in-memory, resets on restart, not
  distributed), it stops casual automated guessing, not a sustained,
  distributed attack.

## What's not in place, on purpose

- **No email verification, OAuth, or 2FA.** The account system is "a lock
  that's good enough for a household or small team," not enterprise IAM.
- **No self-serve password reset.** Forgot your password? The admin resets
  it directly in the database. See the README.
- **No hardening against sustained or distributed attacks.** The rate
  limiter is a basic deterrent, not a defense against someone with real
  resources. If that's your threat model, this isn't the right tool.
- **No TLS built in.** `ourfeed.py` speaks plain HTTP. If your instance is
  reachable from outside your own machine, put TLS in front of it (a
  reverse proxy like Caddy/nginx, Tailscale Funnel, Cloudflare Tunnel), and
  set `cookie_secure: true` in `config.json` once you have. Running an
  invite-only account system over plain HTTP on the open internet means
  session cookies and passwords cross the wire in the clear.

## If you're exposing an instance publicly

This is a legitimate thing to do (a public demo, a family instance reachable
while traveling), but it changes your threat model from "only my home
network can reach this" to "anyone on the internet can hit the login page."
Before you do it:

1. Set `cookie_secure: true` in `config.json` and make sure traffic is
   actually TLS-terminated (Funnel and Cloudflare Tunnel both do this for
   you automatically; a bare reverse proxy needs a real certificate).
2. Don't reuse an instance that already has content you care about staying
   private as your public demo. Registration being invite-gated means a
   random visitor can't read your feed, but "can't currently" and "will
   never" aren't the same guarantee, a config mistake or a bug either of us
   hasn't found yet is still possible. A separate, disposable demo instance
   with sample content is the safer default.
3. Don't hand out invite codes casually. Each one lets someone read
   everything published in whatever channels they land in.

## Reporting a problem

This is a small self-hosted project without a formal disclosure process
yet. Open a GitHub issue, or if it's something you'd rather not post
publicly, say so in the issue and we'll figure out a private channel.
