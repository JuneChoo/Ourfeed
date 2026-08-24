"""
Ourfeed companion for Claude Code: scans your local session logs and drafts
posts for you, based on what actually happened in your conversations.

Two modes:
  python ourfeed-extract.py --session <jsonl_path>   # one session, catches
                                                       # realizations, milestones,
                                                       # tangents, quotable lines
  python ourfeed-extract.py --batch                  # today's sessions combined,
                                                       # catches a daily activity digest

Self-contained: only needs the `claude` CLI installed and on PATH, and a
config.env next to this script (copy config.example.env and fill it in).
See README.md in this folder for setup, including how to make this run
automatically instead of by hand.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import date, datetime
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
    return url, token


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

SESSION_PROMPT = """You're helping someone decide if anything in this conversation is
worth sharing to their personal feed (Ourfeed): a short update for people who care
where they're headed, not a work report. Anything you draft lands in their Drafts
first, they confirm before it's visible to anyone, so lean toward generating more
candidates, not fewer. Don't hold back because you're unsure, the review step is
the filter, not you.

## What counts (any of these four, generate one candidate per match, a session can have several)

### B: A shift in understanding
The person moved from uncertain/confused to clearly resolved on something, and it's
the kind of realization they'd likely want to see again later. This has to be
something they said explicitly ("I get it now", "actually I think..."), not just a
conversation that felt deep to you.

### D: A finished milestone
They explicitly said something is done, shipped, or decided, and it has real weight
(more than a couple exchanges, working toward an actual goal, not "I had a coffee").

### E: A curiosity tangent
A topic outside the original task got dug into for several exchanges in a row, with
no direct practical purpose, just genuine sidetrack.

### F: A quotable line
A single line (theirs or yours, correctly attributed) that stands on its own outside
the conversation, still interesting without context. This is the most subjective
category, if you're not genuinely struck by it, skip it rather than force one.

## Sanitization (required, no exceptions)
- Drop specific numbers, client names, internal strategy details, keep the shape of
  what happened
- Never include credentials, tokens, passwords, or account details
- Don't invent emotions or hours worked, only write what was actually said
- No em dashes, no AI-sounding filler phrases ("I believe", "truly meaningful")
- Write content in first person, like the person is posting it themselves

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
Return {{"candidates": []}} if nothing qualifies. JSON only, no other text."""


DIGEST_PROMPT = """You're writing a short "what I did today" post for someone's
personal feed. This is for people who know them, not a status report.

## Whether to write anything
Only write something if today touched 3+ different topics/projects, or one task got
followed up on for a lot of turns (signals real focus). If today was thin or
repetitive, return nothing rather than padding it out.

## Writing requirements
- Give it a sense of shape, not a numbered list of "1. did X 2. did Y"
- Drop specific numbers/client names/internal details, keep the type of thing done
- Don't invent emotions or hours worked
- No em dashes, no AI-sounding filler phrases
- Write in first person

## Past daily digests this person rejected (strong signal, adjust tone accordingly)
{rejected_high}

## Available channels
{channel_ids}

## Today's conversations
{conversation}

## Output format
Return JSON: {{"candidates": [{{"category": "A", "title": "one line", "content": "2-4 sentences", "channels": [...]}}]}}
Return {{"candidates": []}} if nothing qualifies. JSON only, no other text."""


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

def extract_from_session(jsonl_path, base_url, token, channel_ids):
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


def process_session(jsonl_path, state, base_url, token, channel_ids):
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
    candidates = extract_from_session(jsonl_path, base_url, token, channel_ids)
    state["processed"][session_key] = current_sig
    return candidates


def extract_digest(base_url, token, channel_ids):
    sessions = find_today_sessions()
    print(f"Found {len(sessions)} sessions active today")
    if not sessions:
        return []

    parts = []
    for s in sessions:
        messages = parse_jsonl(s)
        if len(messages) < 4:
            continue
        parts.append(f"[{infer_project(s)}]\n{smart_sample(messages)}")

    if not parts:
        print("  Not enough content today, skipping digest")
        return []

    conversation = "\n\n---\n\n".join(parts)[:12000]
    rejected_high, _ = load_rejected_examples(base_url, token, "A")

    prompt = DIGEST_PROMPT.format(
        rejected_high=rejected_high,
        channel_ids=", ".join(channel_ids),
        conversation=conversation,
    )
    print("Calling claude (daily digest)...")
    raw = call_llm(prompt)
    return parse_llm_json(raw)


# ── Main ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", help="Process one session file")
    parser.add_argument("--batch", action="store_true", help="Generate today's activity digest")
    parser.add_argument("--dry-run", action="store_true", help="Print candidates without posting them")
    args = parser.parse_args()

    if not args.session and not args.batch:
        parser.print_help()
        return

    base_url, token = load_config()
    cfg = get_config(base_url, token)
    if cfg is None:
        print("Couldn't reach Ourfeed, check OURFEED_URL and that the server is running")
        sys.exit(1)
    channel_ids = [c["id"] for c in cfg.get("channels", [])]

    if args.session:
        path = Path(args.session)
        if not path.exists():
            print(f"File not found: {path}")
            return
        state = load_state()
        candidates = process_session(path, state, base_url, token, channel_ids)
        save_state(state)
    else:
        candidates = extract_digest(base_url, token, channel_ids)

    if not candidates:
        print("\nNo candidates found")
        return

    print(f"\n{len(candidates)} candidate(s):")
    for c in candidates:
        print(f"  [{c.get('category')}] {c.get('title')}")

    if args.dry_run:
        print("\n[dry-run] not posting")
        return

    posted = sum(1 for c in candidates if post_draft(base_url, token, c))
    print(f"\nPosted {posted}/{len(candidates)} draft(s), review them at your Ourfeed instance's Drafts page")


if __name__ == "__main__":
    main()
