# Ourfeed architecture

## Visual style

Minecraft-inspired pixel UI: pixel fonts (Press Start 2P for headers,
Silkscreen for UI, Inter for body copy), inset/outset block borders, wood and
cave color palette. This is the one skin Ourfeed ships with; there's no
theme system (v1 keeps it small).

## Data model (SQLite, single file `ourfeed.db`)

### `users`

| field | type | notes |
|---|---|---|
| id | INTEGER PK | |
| username | TEXT UNIQUE | 3-20 chars, `[a-zA-Z0-9_-]` |
| password_salt / password_hash | TEXT | `hashlib.pbkdf2_hmac('sha256', ..., 200_000 iterations)`, stdlib only |
| display_name | TEXT | shown on cards |
| avatar_color | TEXT | auto-assigned from a fixed palette at signup |
| role | TEXT | `admin` / `member` |
| created_at | TIMESTAMP | |

### `invite_codes`

| field | type | notes |
|---|---|---|
| code | TEXT PK | `secrets.token_urlsafe(6)` |
| created_by | INTEGER FK users | must be admin |
| used_by | INTEGER FK users, nullable | set on redemption |
| created_at / used_at | TIMESTAMP | |

### `sessions`

| field | type | notes |
|---|---|---|
| token | TEXT PK | `secrets.token_urlsafe(32)`, stored in an `HttpOnly` cookie |
| user_id | INTEGER FK users | |
| created_at / expires_at | TIMESTAMP | 30-day expiry by default |

### `api_tokens`

| field | type | notes |
|---|---|---|
| id | INTEGER PK | |
| user_id | INTEGER FK users | |
| token | TEXT UNIQUE | `"of_" + secrets.token_urlsafe(32)` |
| label | TEXT | optional, e.g. "my AI agent" |
| created_at / last_used_at | TIMESTAMP | `last_used_at` updates on every authenticated request |

A token has the same permissions as logging in as that user. There's no
scoping beyond that in v1, if a token can create entries, it can also edit
or privatize that user's other entries. Revoking a token from
`/automation.html` deletes the row immediately.

### `entries` (the feed)

| field | type | notes |
|---|---|---|
| id | INTEGER PK | |
| author_id | INTEGER FK users | |
| title | TEXT | |
| content | TEXT | plain text |
| status | TEXT | `draft` / `shared` / `private`, default `draft` |
| parent_id | INTEGER FK entries, nullable | reply/thread link |
| created_at | TIMESTAMP | |
| shared_at | TIMESTAMP, nullable | when it was published |
| skipped_at | TIMESTAMP, nullable | last time it was "skipped" in review |
| edited_at | TIMESTAMP, nullable | set only when title/content changes, not when channels change |

### `entry_channels`

Many-to-many: `(entry_id, channel_id)`. Channel *definitions* (label/icon/
color) live in `config.json`, not the database, so restart the server after
editing them. An entry can carry any number of configured channels at once.

## Auth flow

1. `GET /api/config`: public. Returns `site_name`, `tagline`, `channels`,
   and `bootstrap` (`true` if no user exists yet).
2. `POST /api/register`: `{invite_code?, username, password, display_name?}`.
   If `bootstrap` is true, no invite code is needed and the new user becomes
   `admin`. Otherwise a valid, unused invite code is required and the new
   user is a `member`. Auto-logs in (sets the session cookie) on success.
3. `POST /api/login` / `POST /api/logout`: session cookie set/cleared.
4. `GET /api/me`: current user or `401`.
5. `POST /api/invite-codes` (admin only): mints a one-time code.
   `GET /api/invite-codes` (admin only): lists codes and their usage.

All `/api/entries*` routes require a valid session cookie **or** an
`Authorization: Bearer <token>` header (see "Automated posting" below).
There is no `as`/author field in request bodies anymore, the server derives
the actor from whichever credential was presented, so a client can't spoof
another user's identity.

## Automated posting (API tokens)

Any logged-in user can generate a personal API token from
`/automation.html` (`POST /api/tokens`, `GET /api/tokens` to list their own,
`DELETE /api/tokens/{id}` to revoke). A token authenticates exactly like
that user's session cookie: a script or AI agent that calls `POST
/api/entries` with `Authorization: Bearer <token>` creates a draft under
that user's account, which still has to pass through their own Drafts
review before it's visible to anyone. This is the mechanism the opt-out
review model is really designed for: the friction point in a normal social
app is deciding whether to post at all, but the friction point that matters
here is deciding whether *automatically generated* content should go out
unreviewed, which is exactly what the review step exists to catch. A human
typing directly into the compose box is already making that call, so the
same review step doubles as a safety net for anything posted by automation.

## Feed & review endpoints

- `GET /api/entries?channel={id, optional}`: only `status='shared'` entries,
  newest first. Omit `channel` for everything.
- `POST /api/entries`: new entry, starts as `draft`.
- `POST /api/entries/{id}/respond`: reply to an entry. Publishes
  immediately (skips the draft/review step) because it's typed live by a
  person, not auto-drafted. The review gate exists to catch unreviewed
  automated content, not manual replies. Inherits the parent's channels.
- `GET /api/entries/review?channel={id, optional}`: the current user's own
  drafts, oldest first (so nothing gets buried).
- `GET /api/entries/mine?status={draft|shared|private, optional}`: the
  current user's own entries in any state, newest first. Omit `status` for
  everything. Exists for two reasons: it's the data source for a future
  "private archive" view (deferred in v1, see below), and it's how an
  automation script can check what happened to a draft it created earlier
  (published, still pending, or privatized), which is the basis for any
  taste-learning loop built on top of the API.
- `POST /api/entries/{id}/privatize`: permanently private (`status='private'`).
  Not a delete, content is retained, just no longer visible to anyone but
  the author. The feed's "Delete" button is this same action.
- `POST /api/entries/{id}/skip`: stays a draft, just records `skipped_at`,
  reappears in review next time.
- `POST /api/entries/publish`: `{ids: [...]}`, batch-publishes whatever
  wasn't excluded this round.
- `PATCH /api/entries/{id}`: `{title?, content?, channels?}`. Only the
  author can edit. Editing title/content stamps `edited_at`, changing only
  channels does not.

## What v1 doesn't do

- No hard delete or edit history: "private" is the only removal mechanism.
- No email verification, OAuth, or 2FA.
- No self-serve password reset: the admin resets it directly.
- No multi-tenancy: one Ourfeed instance is for one group.
