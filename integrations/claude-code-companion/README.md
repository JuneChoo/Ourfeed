# Claude Code companion

Two ways to let Claude Code post to your Ourfeed feed for you, based on what's
actually happening in your conversations, not just when you remember to ask.
Both still go through Ourfeed's normal draft review, nothing publishes without
you confirming it.

They're complementary, not alternatives: the live method catches things right
when they happen with full context; the batch script catches things you talked
about in sessions where the live method wasn't active, or that got missed in
the moment.

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

   Categories: [paste the table from "What gets shared" below]
   Sanitization: hide specific numbers/names/internal details, never include
   credentials, don't invent emotions or hours worked, write in first person.
   ```
4. Reference that file from your `CLAUDE.md` (the same way you'd reference any
   other persistent instruction) so it loads automatically in new sessions,
   instead of you pasting it by hand every time. Check that whatever directory
   holds it is actually gitignored if it's inside a repo you'll push.

This only works if the assistant you're using can actually make HTTP requests
on its own (Claude Code can, since it can run shell commands). If yours can't,
use the no-code path in the main `automation.html` guide instead.

## Method 2: Batch script (catches what the live method misses)

`ourfeed-extract.py` scans your local Claude Code session logs
(`~/.claude/projects/**/*.jsonl`, the standard location) and drafts posts from
what it finds. Two modes:

```bash
cp config.example.env config.env   # fill in OURFEED_URL and OURFEED_TOKEN
python ourfeed-extract.py --session <path/to/session.jsonl>   # one conversation
python ourfeed-extract.py --batch                              # today, combined
python ourfeed-extract.py --batch --date 2026-08-23             # a specific day instead of today
python ourfeed-extract.py --session <path> --dry-run           # preview only
```

Requires the `claude` CLI installed and on your PATH (no other dependencies).
Run it by hand at first. Once you're happy with what it drafts, wire it into
whatever you use for scheduling (cron, Task Scheduler, a launchd job) to run
`--session` after a conversation goes idle and `--batch` once a day.

State (`.ourfeed-extract-state.json`, `.ourfeed-category-map.json`) is kept
locally next to the script so it doesn't reprocess the same session twice, and
so it can look up what happened to drafts it created earlier (published,
still pending, or rejected).

## What gets shared

| Category | What it catches | Trigger |
|---|---|---|
| A | Daily activity digest | 3+ different topics today, or one task followed up on heavily. Batch mode only. |
| B | A shift in understanding | You went from unsure to clear on something, explicitly, in your own words. |
| D | A finished milestone | You said something is done/shipped/decided, and it had real weight. |
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
