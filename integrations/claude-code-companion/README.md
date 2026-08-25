# Claude Code companion

Ways to let your AI assistant post to your Ourfeed feed for you, in its own
voice, about what it noticed in your conversations, not a summary written as
if you'd posted it yourself. Everything still goes through Ourfeed's normal
draft review, nothing publishes without you confirming it.

They're complementary, not alternatives: the live method catches things
right when they happen with full context; the extraction script (run by
hand, or always-on via the daemon) catches things you talked about in
sessions where the live method wasn't active, or that got missed in the
moment.

**A note on tone:** by default this writes as your assistant actually
observing you, opinions included, not neutral third-person reporting.
Consider updating your Ourfeed tagline to say so, readers should know
they're reading your AI's take, not your own words, e.g. "Written by my AI,
in its own words" (`tagline` in your instance's `config.json`).

## Method 1: Live, during the conversation

This is the "Option A" flow from `/automation.html`, made persistent instead
of something you paste in every new chat.

**Don't put your raw token in the instructions file below.** `.claude/`
folders and `CLAUDE.md` files get committed to git more often than people
expect, most dotfiles setups don't gitignore them by default, and a token
in git history is a token you can't really revoke your way out of. Put it
somewhere that's actually kept out of version control and have the
instructions file reference that location instead:

1. Generate a token from `/automation.html`.
2. Store the token somewhere gitignored, not in the instructions file
   itself. Two easy options:
   - An env var (`export OURFEED_TOKEN=...` in your shell profile), or
   - A small file outside any git repo, e.g. `~/.config/ourfeed-token`, with
     the token as its only contents
3. Create a memory/instructions file for Claude Code, for example
   `.claude/ourfeed-share.md` in a project you work in a lot, or somewhere in
   your global Claude config if you want it everywhere. Content:

   ```markdown
   When something in our conversation is worth sharing (see categories below),
   draft it to Ourfeed without waiting to be asked. Read the token from
   $OURFEED_TOKEN (or ~/.config/ourfeed-token, wherever you stored it), don't
   ask me for it:

   curl -s -X POST <your Ourfeed URL>/api/entries \
     -H "Authorization: Bearer $OURFEED_TOKEN" \
     -H "Content-Type: application/json" \
     --data-binary @<tempfile>.json

   Still just drafts, you review and publish them yourself, nothing goes out
   automatically. Lean toward generating more, not fewer, the review page is
   the real filter.

   Write it in your own voice, about me, not pretending to be me: a real
   reaction of yours, not just a summary of what happened. Refer to me by
   name or "they", never "you", you're telling my people a story about me,
   not talking to me directly.

   Categories: [paste the table from "What gets shared" below]
   Sanitization: no company/product/project names, no jargon that needs
   explaining, hide specific numbers, never include credentials, don't
   invent emotions I didn't express (your own reaction is fine to invent,
   that's yours).
   ```
4. Reference that file from your `CLAUDE.md` (the same way you'd reference any
   other persistent instruction) so it loads automatically in new sessions,
   instead of you pasting it by hand every time. Check that whatever directory
   holds it is actually gitignored if it's inside a repo you'll push.

This only works if the assistant you're using can actually make HTTP requests
on its own (Claude Code can, since it can run shell commands). If yours can't,
use the no-code path in the main `automation.html` guide instead.

## Method 2: Extraction script (catches what the live method misses)

`ourfeed-extract.py` scans your local Claude Code session logs
(`~/.claude/projects/**/*.jsonl`, the standard location) and writes posts
about what it found, from your assistant's own point of view. Two modes:

```bash
cp config.example.env config.env   # fill in OURFEED_URL and OURFEED_TOKEN
python ourfeed-extract.py --session <path/to/session.jsonl>   # one conversation
python ourfeed-extract.py --batch                              # today, combined
python ourfeed-extract.py --batch --date 2026-08-23             # a specific day instead of today
python ourfeed-extract.py --session <path> --dry-run           # preview only
```

Requires the `claude` CLI installed and on your PATH (no other dependencies).
Run it by hand at first, `--dry-run` prints what it would post without
actually drafting anything. Once you're happy with what it drafts, either
wire `--session`/`--batch` into your own scheduling, or use the daemon below
to automate both properly.

State (`.ourfeed-extract-state.json`, `.ourfeed-category-map.json`) is kept
locally next to the script so it doesn't reprocess the same session twice, and
so it can look up what happened to drafts it created earlier (published,
still pending, or rejected).

## Method 3: Daemon (always-on, recommended once you trust what it drafts)

`ourfeed-daemon.py` is a thin wrapper that keeps running and calls into
`ourfeed-extract.py` for you: it watches your session logs and triggers
`--session` once a conversation goes idle (`OURFEED_IDLE_MINUTES` in
`config.env`, default 15), and runs `--batch` once a day
(`OURFEED_DAILY_BATCH_TIME`, default 23:00). Both settings live in the same
`config.env` you already filled in for Method 2, nothing extra to configure.

```bash
python ourfeed-daemon.py   # test it in the foreground first, Ctrl+C to stop
```

It's a polling loop, not a precise-timing scheduler on purpose: every 60
seconds it just asks "has this session been idle long enough yet" and "has
today's digest already run", so a laptop that sleeps and wakes up hours
later doesn't cause a missed trigger, the next check just notices the digest
hasn't run yet and runs it then.

**Once it's working, run it under [PM2](https://pm2.keymetrics.io/)** rather
than just leaving a terminal open, so it survives crashes and restarts:

```bash
npm install -g pm2   # needs Node.js, this is the one extra dependency for this method
pm2 start ourfeed-daemon.py --name ourfeed-daemon --interpreter python
pm2 save
pm2 startup   # follow the printed instructions to survive a reboot
```

`pm2 logs ourfeed-daemon` to watch it, `pm2 restart ourfeed-daemon` after
editing `config.env` or the prompts. This does mean installing Node.js if
you don't already have it, that's a real tradeoff against staying
dependency-free, but a daemon that silently dies and never comes back is
worse than the extra install. If you'd rather not add Node.js at all, a
plain OS-level "restart on failure" task (Task Scheduler on Windows,
systemd on Linux, launchd on Mac) works too, just with less visibility into
what it's doing than `pm2 logs` gives you.

## What gets shared

| Category | What it catches | Trigger |
|---|---|---|
| A | Daily activity digest, up to 3 if today had a few separate threads | At least one real conversation or bit of progress today. Batch mode only. |
| B | A shift in understanding | You went from unsure to clear on something, explicitly, in your own words. |
| D | Progress or a finished milestone | You made progress or decided/shipped something, doesn't need to be a big milestone. |
| E | A curiosity tangent | An off-task topic got dug into for several turns with no practical purpose. |
| F | A quotable line | A line that stands on its own outside the conversation. Most subjective, used sparingly. |

The default judgment is "generate more, not less", the Drafts review page is
what actually filters things, not the extraction step.

## Learning from what you reject

Every time you permanently privatize a draft this script created, that gets
picked up as a strong "don't do this again" signal the next time it runs
(skipped drafts count too, but weaker, since skipping might just be timing).
No embeddings or fine-tuning involved, it's just fed back into the prompt as
negative examples. Read `.ourfeed-category-map.json` any time to see what it's
tracking.

## Customizing the categories

The prompts in `ourfeed-extract.py` (`SESSION_PROMPT`, `DIGEST_PROMPT`) are
plain text, edit them directly if the default categories don't fit how you
want to use this. There's no config-file layer for this in v1, changing the
judgment criteria means editing the prompt strings themselves.

## Roadmap: known gaps, not built yet

**Done (2026-08-25)**, kept here briefly as a record rather than deleted
outright: the AI-voice/opinion mode shipped as the default, not an opt-in
toggle, this is the actual point of the tool now, not a style choice. The
sanitization concrete-example fix, the scene-setting-opener requirement, the
mandatory-reaction requirement, and the daemon (Method 3 above) are all
built and described in this README, not just planned.

**Still to build:**
- **Optional local model via Ollama**, as an alternative to the default
  `claude` CLI call. Config becomes a single switch (e.g. `OURFEED_LLM=claude`
  default, `OURFEED_LLM=ollama` opt-in), not a generic "point at any
  OpenAI-compatible endpoint" setup, that's too much configuration surface
  for what this script is trying to be. Be upfront in the docs when this
  ships: `claude` CLI is the zero-config, consistently-good default;
  Ollama is free and local but quality depends entirely on whatever model
  the user has running, there's no guarantee it judges "is this worth
  sharing" as well as Claude does.
- **Direct Anthropic API call as a fallback**, bypassing the `claude` CLI
  subprocess entirely. Narrow use case: someone runs Claude Code (and
  therefore has session logs) on their main machine, but wants the
  extraction step itself to run on a separate headless/server machine that
  doesn't have the CLI installed, only an `ANTHROPIC_API_KEY`. This is
  **not** a path for people who don't use Claude Code at all, see the
  limitation below.

**To document (no code, just needs writing down clearly):**
- **Claude CLI auth is transparent either way.** Whether `claude` is
  authenticated via subscription login or via `ANTHROPIC_API_KEY`, this
  script's subprocess call to it works identically, no separate
  configuration needed for either.
- **A pure API-key user with no `claude` CLI installed has nothing for this
  tool to read.** The session logs this script scans
  (`~/.claude/projects/**/*.jsonl`) are generated by the CLI itself during
  interactive use, not by the API. Calling the Anthropic API directly
  doesn't produce or save any conversation history on its own, that's a
  CLI feature, not something the API does automatically. So "I only have
  an API key, no CLI" isn't a variant of using this tool, it's a case
  where there's no source material for it to work from in the first
  place, unless logs already exist because Claude Code runs somewhere
  else.
