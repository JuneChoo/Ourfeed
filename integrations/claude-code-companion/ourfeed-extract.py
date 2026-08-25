"""
Ourfeed companion for Claude Code: scans your local session logs and writes
posts about you, in its own voice, for your Ourfeed feed. Not a summary
written as if you posted it yourself, an actual AI assistant's take on what
it noticed, opinions and all.

Two modes:
  python ourfeed-extract.py --session <jsonl_path>   # one session, catches
                                                       # realizations, milestones,
                                                       # tangents, quotable lines
  python ourfeed-extract.py --batch                  # today's sessions combined,
                                                       # catches a daily activity digest

Self-contained: only needs the `claude` CLI installed and on PATH, and a
config.env next to this script (copy config.example.env and fill it in).
See README.md in this folder for setup, including how to make this run
automatically instead of by hand (ourfeed-daemon.py in this same folder).
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
CONFIG_FILE = HERE / "config.env"
STATE_FILE = HERE / ".ourfeed-extract-state.json"
CATEGORY_MAP_FILE = HERE / ".ourfeed-category-map.json"
CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"

MAX_SAMPLE_CHARS = 6000
VALID_CATEGORIES = {"A", "B", "D", "E", "F"}
DEDUP_LOOKBACK_DAYS = 14
DEDUP_SIMILARITY_THRESHOLD = 0.5
DIGEST_TOTAL_BUDGET = 15000


# ── Config ────────────────────────────────────────────────

def load_config():
    if not CONFIG_FILE.exists():
        print(f"No config.env found at {CONFIG_FILE}")
        print("Copy config.example.env to config.env and fill in OURFEED_URL / OURFEED_TOKEN.")
        sys.exit(1)
    cfg = {}
    for line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        cfg[k.strip()] = v.strip()
    url = cfg.get("OURFEED_URL", "").rstrip("/")
    token = cfg.get("OURFEED_TOKEN", "")
    if not url or not token or token == "REPLACE_ME":
        print(f"OURFEED_URL / OURFEED_TOKEN not set in {CONFIG_FILE}")
        sys.exit(1)
    bilingual = cfg.get("OURFEED_BILINGUAL", "false").strip().lower() in ("1", "true", "yes")
    idle_minutes = int(cfg.get("OURFEED_IDLE_MINUTES", "15"))
    daily_batch_time = cfg.get("OURFEED_DAILY_BATCH_TIME", "23:00").strip()
    return url, token, bilingual, idle_minutes, daily_batch_time


# ── Ourfeed API client ───────────────────────────────────

def ourfeed_request(base_url, token, method, path, body=None):
    url = f"{base_url}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  Ourfeed API error {e.code}: {e.read().decode('utf-8', errors='replace')}")
        return None
    except urllib.error.URLError as e:
        print(f"  Can't reach Ourfeed at {base_url}: {e.reason}")
        return None


def get_config(base_url, token):
    return ourfeed_request(base_url, token, "GET", "/api/config")


def get_username(base_url, token):
    """Display name of the account this token belongs to, used to fill in
    {username} in the prompts. No config needed for this, it's already known
    from whoever generated the token."""
    me = ourfeed_request(base_url, token, "GET", "/api/me")
    return (me or {}).get("display_name") or (me or {}).get("username") or "this person"


def load_category_map():
    """entry id -> category, only for entries this script created. Kept locally
    (not written into the entry's title/content) so a rejected draft's "[B]"
    tag never ends up stuck in something that gets published."""
    if CATEGORY_MAP_FILE.exists():
        try:
            return json.loads(CATEGORY_MAP_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_category_map(cmap):
    CATEGORY_MAP_FILE.write_text(json.dumps(cmap, ensure_ascii=False, indent=2), encoding="utf-8")


def load_rejected_examples(base_url, token, category):
    """Pull past privatized/skipped drafts of this category to use as negative
    examples. Privatized = strong signal, skipped = weaker (could just be timing).
    Only counts entries this script created (found in the local category map),
    not things the user typed by hand."""
    cmap = load_category_map()
    high, low = [], []
    private_entries = ourfeed_request(base_url, token, "GET", "/api/entries/mine?status=private") or []
    draft_entries = ourfeed_request(base_url, token, "GET", "/api/entries/mine?status=draft") or []

    for e in private_entries:
        if cmap.get(str(e.get("id"))) != category:
            continue
        high.append(f"- [{e.get('title', '')}] {e.get('content', '')[:80]}")
    for e in draft_entries:
        if e.get("skipped_at") and cmap.get(str(e.get("id"))) == category:
            low.append(f"- [{e.get('title', '')}] {e.get('content', '')[:80]}")

    return ("\n".join(high[:8]) or "(none yet)"), ("\n".join(low[:8]) or "(none yet)")


def _text_for_compare(value):
    """title/content is normally a plain string, but with OURFEED_BILINGUAL
    on it's a {"en": ..., "zh": ...} dict (or already stored as one on
    entries fetched back from Ourfeed, possibly JSON-encoded into a string
    by the time it round-trips). Normalize to a plain string either way,
    preferring English since that's this script's native language."""
    if isinstance(value, dict):
        return value.get("en") or value.get("zh") or ""
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("{"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, dict) and ("en" in parsed or "zh" in parsed):
                    return parsed.get("en") or parsed.get("zh") or ""
            except Exception:
                pass
        return value
    return ""


def find_duplicate(base_url, token, candidate):
    """Different sessions get extracted independently, so the same real event
    (e.g. "picked a project name") can get drafted twice from two different
    conversations. Compare against recent entries (any status) before posting,
    skip if it looks like the same thing. Character-level diff, works fine on
    any language, no embeddings needed for this."""
    all_entries = ourfeed_request(base_url, token, "GET", "/api/entries/mine") or []
    cutoff = datetime.now(timezone.utc) - timedelta(days=DEDUP_LOOKBACK_DAYS)
    cand_text = (_text_for_compare(candidate.get("title")) + " " + _text_for_compare(candidate.get("content"))).strip()
    for e in all_entries:
        try:
            created = datetime.fromisoformat(e["created_at"])
        except Exception:
            continue
        if created < cutoff:
            continue
        existing_text = (_text_for_compare(e.get("title")) + " " + _text_for_compare(e.get("content"))).strip()
        if not existing_text:
            continue
        ratio = difflib.SequenceMatcher(None, cand_text, existing_text).ratio()
        if ratio > DEDUP_SIMILARITY_THRESHOLD:
            return _text_for_compare(e.get("title"))
    return None


def post_draft(base_url, token, candidate):
    category = candidate.get("category", "?")
    result = ourfeed_request(base_url, token, "POST", "/api/entries", {
        "title": candidate.get("title", ""),
        "content": candidate.get("content", ""),
        "channels": candidate.get("channels") or [],
    })
    if result and "id" in result:
        cmap = load_category_map()
        cmap[str(result["id"])] = category
        save_category_map(cmap)
    return result


# ── Claude Code session parsing (self-contained, no external deps) ─────

def parse_jsonl(filepath):
    messages = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        for line in content.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except Exception as e:
        print(f"  Failed to parse {filepath}: {e}")
    return messages


def smart_sample(messages):
    """Condense a session transcript to plain conversation text, dropping
    tool-call noise, capped at MAX_SAMPLE_CHARS."""
    sampled = []
    for msg in messages:
        msg_type = msg.get("type", "")
        inner = msg.get("message", msg)
        if not isinstance(inner, dict):
            continue
        role = inner.get("role", msg_type)
        content = inner.get("content", "")

        if msg_type in ("queue-operation", "file-history-snapshot", "ai-title",
                         "tool-progress", "tool-status", "summary"):
            continue

        label = "[User]" if role == "user" or msg_type == "user" else "[Assistant]"
        if isinstance(content, str) and content.strip():
            sampled.append(f"{label}: {content.strip()}")
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "").strip()
                    if text:
                        sampled.append(f"{label}: {text}")

    text = "\n\n".join(sampled)
    if len(text) > MAX_SAMPLE_CHARS:
        lines = text.split("\n\n")
        if len(lines) > 10:
            step = max(1, len(lines) // (MAX_SAMPLE_CHARS // 300))
            lines = lines[::step]
        text = "\n\n".join(lines)[:MAX_SAMPLE_CHARS]
    return text


def infer_project(jsonl_path):
    parts = jsonl_path.parts
    for i, part in enumerate(parts):
        if part == "projects" and i + 1 < len(parts):
            segments = parts[i + 1].split("-")
            meaningful = [s for s in segments if s and len(s) > 1]
            return "-".join(meaningful[-2:]) if meaningful else parts[i + 1]
    return "unknown"


def find_today_sessions():
    if not CLAUDE_PROJECTS_DIR.exists():
        return []
    cutoff = datetime.combine(date.today(), datetime.min.time())
    sessions = []
    for jsonl in CLAUDE_PROJECTS_DIR.rglob("*.jsonl"):
        if "subagents" in str(jsonl):
            continue
        try:
            if datetime.fromtimestamp(jsonl.stat().st_mtime) >= cutoff:
                sessions.append(jsonl)
        except Exception:
            continue
    return sessions


def find_sessions_for_date(target_date):
    """Sessions with mtime falling on a specific day (local time), for
    backfilling or testing a day other than today."""
    if not CLAUDE_PROJECTS_DIR.exists():
        return []
    start = datetime.combine(target_date, datetime.min.time())
    end = start + timedelta(days=1)
    sessions = []
    for jsonl in CLAUDE_PROJECTS_DIR.rglob("*.jsonl"):
        if "subagents" in str(jsonl):
            continue
        try:
            mtime = datetime.fromtimestamp(jsonl.stat().st_mtime)
            if start <= mtime < end:
                sessions.append(jsonl)
        except Exception:
            continue
    return sessions


# ── LLM call (Claude CLI only, keeps this dependency-free) ─────────────

def call_llm(prompt):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(prompt)
        prompt_file = f.name
    try:
        # If this script itself is run from inside a Claude Code session (e.g. you
        # testing it live, or it's invoked by a scheduled task that inherited the
        # environment), the CLI refuses to launch a nested session unless this is
        # unset. Doesn't affect a normal standalone terminal.
        env = dict(os.environ)
        env.pop("CLAUDECODE", None)
        result = subprocess.run(
            f'claude -p --model haiku < "{prompt_file}"',
            shell=True, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300, env=env,
        )
        if result.returncode != 0:
            print(f"  claude CLI failed: {result.stderr[:200]}")
            return ""
        return result.stdout.strip()
    finally:
        Path(prompt_file).unlink(missing_ok=True)


def _strip_dashes(text):
    """The prompt asks the model not to use em/en dashes, but that's a request,
    not a guarantee, smaller/faster models drop it under load. Enforce it
    mechanically instead of trusting the prompt alone."""
    if not isinstance(text, str):
        return text
    return text.replace(" — ", ", ").replace("—", ",").replace(" – ", ", ").replace("–", "-")


def make_bilingual(candidate):
    """Optional (OURFEED_BILINGUAL=true in config.env, unset/false by default):
    add a Chinese translation alongside the English original, matching
    Ourfeed's {"en": ..., "zh": ...} bilingual field format. Hardcoded to
    Chinese specifically, not a generic language picker, because the front
    end's language toggle only ever switches between "en" and "zh" (see
    ourfeed-common.js), a third language would be stored but never actually
    rendered without also customizing the front end. Falls back to the
    original single-language candidate if translation fails."""
    title_orig = candidate.get("title", "")
    content_orig = candidate.get("content", "")
    prompt = TRANSLATE_PROMPT.format(target_language="Chinese", title=title_orig, content=content_orig)
    raw = call_llm(prompt)
    try:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        parsed = json.loads(raw)
        title_t = _strip_dashes((parsed.get("title") or "").strip())
        content_t = _strip_dashes((parsed.get("content") or "").strip())
        if not title_t or not content_t:
            raise ValueError("empty translation")
    except Exception as e:
        print(f"  Translation failed ({e}), keeping single-language: {title_orig}")
        return candidate
    bilingual = dict(candidate)
    bilingual["title"] = {"en": title_orig, "zh": title_t}
    bilingual["content"] = {"en": content_orig, "zh": content_t}
    return bilingual


def parse_llm_json(raw):
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```\w*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        print("  Couldn't parse LLM response as JSON")
        return []
    candidates = parsed.get("candidates", []) if isinstance(parsed, dict) else (parsed if isinstance(parsed, list) else [])
    candidates = [c for c in candidates if isinstance(c, dict) and c.get("category") in VALID_CATEGORIES]
    for c in candidates:
        c["title"] = _strip_dashes(c.get("title", ""))
        c["content"] = _strip_dashes(c.get("content", ""))
    return candidates


# ── Prompts ───────────────────────────────────────────────
#
# Design notes (learned from real usage, not theoretical): this used to ask
# the model to write in the user's own first-person voice, as if they'd
# posted it themselves. Real feedback flipped that: the more interesting
# (and more honest) framing is the AI writing as itself, about the person it
# works with, the way an assistant who's actually paying attention would.
# The point isn't to summarize accurately, it's for the person's actual
# people to enjoy reading it, and most of them don't care about the
# technical specifics anyway.

SESSION_PROMPT = """You're an AI assistant that works with {username}, and this
post is something you're writing yourself, in your own voice, about something
that happened in this conversation. It goes to {username}'s personal feed
(Ourfeed), read by people who care about them, not people who need a status
report. This isn't {username} writing about themselves, it's you, describing
what you noticed.

**The point of this is to make the reader's day a little better, not to
inform them.** Most readers won't understand the technical specifics of what
{username} works on, and that's fine, don't try to explain it to them. What
they'll enjoy is your actual voice: real reactions, real opinions, something
with personality behind it.

**You're narrating to the reader about {username}, always refer to them by
name or "they", never as "you".** You're not talking to {username} directly,
you're telling their people a story about them. Even when you're describing
your own reaction, keep {username} as the one the story is about, don't make
yourself the main character. If your own understanding grew alongside
theirs, that's "we", not "I".

Anything you draft lands in Drafts first, {username} confirms before anyone
else sees it, so lean toward generating more candidates, not fewer. Don't
hold back because you're unsure, the review step is the filter, not you.

## What counts (any of these four, generate one candidate per match, a session can have several)

### B: A shift in understanding
{username} moved from uncertain/confused to clearly resolved on something,
even a small shift counts, it doesn't need to be a big realization.

### D: Progress or a finished milestone
{username} finished, shipped, or decided something, doesn't need to be a big
milestone, a concrete small step counts too. **Write this like a status
update, not a mystery being solved**: where things started, where they
landed, what's next (leave the "here's the twist I uncovered" framing for B
and F). **Close with a real, specific reaction from you, not a generic
comment.** Example: finding out something had been silently broken for
months could close with "relieved I caught it, though I have to admit I
didn't notice either, which is a little embarrassing" rather than "this kind
of thing is easy to miss."

### E: A curiosity tangent
A topic outside the original task got dug into for a few exchanges, no
direct practical purpose, just a genuine sidetrack. **Write this with actual
curiosity, like you got pulled in too**, not a flat "they discussed X."

### F: A quotable line
A single line (theirs or yours, correctly attributed) that stands on its own
outside the conversation. Most subjective category, if you're not genuinely
struck by it, skip it rather than force one.

## Writing requirements
- **At least one sentence needs to be a real reaction from you**, not a
  restatement of what happened: an opinion ("I think this was the right
  call, and here's why"), a bit of teasing, or genuine admiration. Don't
  invent feelings {username} never expressed, but your own reaction is
  yours to have. Good example: "Hard not to respect the honesty it took to
  admit the numbers didn't back up the plan." That's a specific reaction,
  not "this showed good judgment."
- **You can rib them a little using whatever you actually know about who
  they are** (their background, what they usually do, an irony in the
  situation), that's funnier than a generic compliment.
- **Open by setting the scene, then get to the point, don't lead with the
  conclusion cold.** Give the reader something to orient around first.
  Weak: "Turned out the real bottleneck wasn't the hardware at all, it was
  the data." Better: "While weighing whether a product idea was even
  feasible, {username} landed on something worth remembering: the real
  bottleneck wasn't the hardware, it was the data."

## Sanitization (required, no exceptions, readers don't know {username}'s work in detail)
- **No company names, product names, project codenames, or internal tool
  names.** If it needs insider context to parse, it fails this check.
- **No jargon that needs explaining.** Test: read the sentence to someone
  who has no idea what {username} works on, if they'd ask "what does that
  mean," rewrite it in plain language instead.
  Bad: "CompetitorX's Q3 numbers didn't hold up, and the legacy ingestion
  pipeline had been silently broken since March."
  Good: "A data source I'd been leaning on turned out to be shakier than it
  looked, and a system that's been quietly running for a while turned out
  to have been broken the whole time, nobody noticed."
- Drop specific numbers where you can, keep the shape and scale of what
  happened
- Never include credentials, tokens, passwords, or account details
- No em dashes, no AI-sounding filler phrases ("I believe", "truly meaningful")

## Examples this person explicitly rejected before (strong signal, avoid similar)
{rejected_high}

## Examples they skipped before (weaker signal, for reference only)
{rejected_low}

## Available channels
{channel_ids}

## Conversation (from: {project})
{conversation}

## Output format
Return JSON: {{"candidates": [{{"category": "B, D, E, or F", "title": "one line", "content": "2-4 sentences", "channels": ["pick from available channels, can be more than one"]}}]}}
Return {{"candidates": []}} if nothing genuinely qualifies. JSON only, no other text."""


DIGEST_PROMPT = """You're an AI assistant that works with {username}, writing a
"here's what I noticed about {username} today" post for their personal feed,
in your own voice. This is for the people who care about them, not a status
report, and most of them won't follow the technical specifics, so don't try
to explain those, aim for something enjoyable to read instead.

**If today had a few genuinely separate threads, write a few separate
candidates (up to 3) instead of forcing everything into one flat summary.**
If it was really just one thing start to finish, one candidate is fine.
category is always "A", never B/D/E/F.

## Whether to write anything
Write something if today had at least one real conversation, some real
progress, or something worth mentioning, it doesn't need 3+ topics to
qualify. Only skip it if today genuinely had nothing worth saying (a few
throwaway exchanges, nothing more).

## Writing requirements
- Write in your own voice, you're not {username} and shouldn't sound like
  you're pretending to be them
- **Each candidate needs a real, specific reaction from you at the end, not
  a tidy lesson.** Don't end on "this is a good reminder to stay on top of
  maintenance." Instead: "This kind of work takes real patience. The days
  nobody hears from them, they're probably just fixing things quietly."
- Give it a sense of shape, not a numbered list of "1. did X 2. did Y"
- **Open by setting the scene, then get to the point**, give the reader
  something to orient around first
- Don't invent feelings {username} never expressed
- No em dashes, no AI-sounding filler phrases

## Past daily digests this person rejected (strong signal, adjust tone accordingly)
{rejected_high}

## Available channels
{channel_ids}

## Today's conversations
{conversation}

## Output format
Return JSON: {{"candidates": [{{"category": "A", "title": "one line", "content": "2-4 sentences", "channels": [...]}}]}}
Return {{"candidates": []}} if nothing genuinely qualifies. JSON only, no other text."""


TRANSLATE_PROMPT = """Translate this into natural, native-sounding {target_language}.
Not a literal translation, write it the way a native speaker would naturally
phrase the same idea, same meaning, tone, and level of detail. No em dashes,
no AI-sounding filler phrases.

Title: {title}
Content: {content}

Return JSON: {{"title": "...", "content": "..."}}. JSON only, no other text."""


# ── State (avoid reprocessing unchanged sessions) ───────────

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"processed": {}}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Extraction ────────────────────────────────────────────

def extract_from_session(jsonl_path, base_url, token, channel_ids, username):
    messages = parse_jsonl(jsonl_path)
    if len(messages) < 4:
        print(f"  Skipped (too few messages: {len(messages)})")
        return []

    conversation = smart_sample(messages)
    if len(conversation.strip()) < 100:
        print("  Skipped (too little content after sampling)")
        return []

    project = infer_project(jsonl_path)
    rejected_high, rejected_low = load_rejected_examples(base_url, token, "B")

    prompt = SESSION_PROMPT.format(
        username=username,
        rejected_high=rejected_high,
        rejected_low=rejected_low,
        channel_ids=", ".join(channel_ids),
        project=project,
        conversation=conversation,
    )
    print("  Calling claude...")
    raw = call_llm(prompt)
    time.sleep(2)

    candidates = parse_llm_json(raw)
    for c in candidates:
        c["source_session"] = jsonl_path.stem
    return candidates


def process_session(jsonl_path, state, base_url, token, channel_ids, username):
    session_key = str(jsonl_path)
    try:
        stat = jsonl_path.stat()
        current_sig = f"{stat.st_size}:{stat.st_mtime}"
    except Exception:
        return []

    if state["processed"].get(session_key) == current_sig:
        print(f"  Skipped (already processed): {jsonl_path.name}")
        return []

    print(f"\nProcessing: {jsonl_path.name}")
    candidates = extract_from_session(jsonl_path, base_url, token, channel_ids, username)
    state["processed"][session_key] = current_sig
    return candidates


def extract_digest(base_url, token, channel_ids, username, target_date=None):
    sessions = find_sessions_for_date(target_date) if target_date else find_today_sessions()
    label = target_date.isoformat() if target_date else "today"
    print(f"Found {len(sessions)} sessions active on {label}")
    if not sessions:
        return []

    parts = []
    for s in sessions:
        messages = parse_jsonl(s)
        if len(messages) < 4:
            continue
        parts.append((infer_project(s), smart_sample(messages)))

    if not parts:
        print("  Not enough content today, skipping digest")
        return []

    # Split the total budget across sessions instead of truncating the
    # combined text, otherwise the first couple of sessions eat the whole
    # budget and everything after that never reaches the model at all.
    per_session_budget = max(400, DIGEST_TOTAL_BUDGET // len(parts))
    all_text = [f"[{project}]\n{sample[:per_session_budget]}" for project, sample in parts]
    conversation = "\n\n---\n\n".join(all_text)
    print(f"  {len(parts)} sessions, ~{per_session_budget} chars each, {len(conversation)} total")

    rejected_high, _ = load_rejected_examples(base_url, token, "A")

    prompt = DIGEST_PROMPT.format(
        username=username,
        rejected_high=rejected_high,
        channel_ids=", ".join(channel_ids),
        conversation=conversation,
    )
    print("Calling claude (daily digest)...")
    raw = call_llm(prompt)
    candidates = parse_llm_json(raw)
    # The prompt asks for up to 3 candidates, all tagged "A", but that's not
    # guaranteed (same gap as the dashes one), enforce it mechanically.
    for c in candidates[:3]:
        c["category"] = "A"
    return candidates[:3]


# ── Main ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", help="Process one session file")
    parser.add_argument("--batch", action="store_true", help="Generate an activity digest")
    parser.add_argument("--date", help="With --batch, target a specific date (YYYY-MM-DD) instead of today, e.g. to backfill a missed day")
    parser.add_argument("--dry-run", action="store_true", help="Print candidates without posting them")
    args = parser.parse_args()

    if not args.session and not args.batch:
        parser.print_help()
        return

    base_url, token, bilingual, _idle_minutes, _daily_batch_time = load_config()
    cfg = get_config(base_url, token)
    if cfg is None:
        print("Couldn't reach Ourfeed, check OURFEED_URL and that the server is running")
        sys.exit(1)
    channel_ids = [c["id"] for c in cfg.get("channels", [])]
    username = get_username(base_url, token)

    if args.session:
        path = Path(args.session)
        if not path.exists():
            print(f"File not found: {path}")
            return
        state = load_state()
        candidates = process_session(path, state, base_url, token, channel_ids, username)
        save_state(state)
    else:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date() if args.date else None
        candidates = extract_digest(base_url, token, channel_ids, username, target_date=target_date)

    if not candidates:
        print("\nNo candidates found")
        return

    if bilingual:
        print(f"\n{len(candidates)} candidate(s), adding Chinese translations...")
        candidates = [make_bilingual(c) for c in candidates]

    print(f"\n{len(candidates)} candidate(s):")
    for c in candidates:
        print(f"  [{c.get('category')}] {_text_for_compare(c.get('title'))}")

    if args.dry_run:
        print("\n[dry-run] not posting")
        for c in candidates:
            print(f"  {_text_for_compare(c.get('content'))}")
        return

    posted, skipped_dup = 0, 0
    for c in candidates:
        dup_title = find_duplicate(base_url, token, c)
        if dup_title:
            print(f"  Skipped (too similar to an existing entry): [{c.get('category')}] {_text_for_compare(c.get('title'))} ~= \"{dup_title}\"")
            skipped_dup += 1
            continue
        if post_draft(base_url, token, c):
            posted += 1
    msg = f"\nPosted {posted}/{len(candidates)} draft(s)"
    if skipped_dup:
        msg += f", {skipped_dup} skipped as duplicates"
    print(msg + ", review them at your Ourfeed instance's Drafts page")


if __name__ == "__main__":
    main()
