"""
Always-on version of ourfeed-extract.py: watches your Claude Code session
logs and runs --session on each one once it goes idle, plus runs --batch
once a day. This is the process you keep running in the background (see
README.md for the PM2 setup), it's a thin wrapper around ourfeed-extract.py,
not a reimplementation, all the actual extraction logic still lives there.

Run directly to test: python ourfeed-daemon.py
Stop with Ctrl+C.

Deliberately a polling loop, not a precise scheduler: every tick it just
asks "is a session idle yet" and "has today's digest run yet", so a laptop
going to sleep and waking up hours later doesn't cause a missed trigger the
way a fire-at-an-exact-moment cron job would, the next tick just notices the
digest hasn't run today and runs it then.
"""
import importlib
import json
import sys
import time
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
oe = importlib.import_module("ourfeed-extract")

POLL_SECONDS = 60
# Only track files touched recently, an untouched file from last month isn't
# "just went idle", it's old history process_session's own state file
# already knows whether it's been handled or not.
RECENT_WINDOW_HOURS = 6

DAEMON_STATE_FILE = Path(__file__).parent / ".ourfeed-daemon-state.json"


def load_daemon_state():
    if DAEMON_STATE_FILE.exists():
        try:
            return json.loads(DAEMON_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"stable_since": {}, "last_batch_date": None}


def save_daemon_state(state):
    DAEMON_STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def check_idle_sessions(daemon_state, idle_minutes, base_url, token, channel_ids, username, session_state):
    now = time.time()
    cutoff = now - RECENT_WINDOW_HOURS * 3600
    stable_since = daemon_state["stable_since"]

    if not oe.CLAUDE_PROJECTS_DIR.exists():
        return

    seen_paths = set()
    for jsonl in oe.CLAUDE_PROJECTS_DIR.rglob("*.jsonl"):
        if "subagents" in str(jsonl):
            continue
        try:
            mtime = jsonl.stat().st_mtime
        except Exception:
            continue
        if mtime < cutoff:
            continue
        key = str(jsonl)
        seen_paths.add(key)

        recorded = stable_since.get(key)
        if recorded is None or recorded["mtime"] != mtime:
            stable_since[key] = {"mtime": mtime, "since": now}
            continue

        idle_for = now - recorded["since"]
        if idle_for >= idle_minutes * 60:
            print(f"[{datetime.now().isoformat(timespec='seconds')}] Idle: {jsonl.name}")
            candidates = oe.process_session(jsonl, session_state, base_url, token, channel_ids, username)
            oe.save_state(session_state)
            _post_candidates(candidates, base_url, token)
            # Drop it so we don't re-trigger every tick until it changes again
            del stable_since[key]

    # Forget files that fell out of the recent window, keeps the state file small
    for key in list(stable_since.keys()):
        if key not in seen_paths:
            del stable_since[key]


def check_daily_batch(daemon_state, daily_batch_time, base_url, token, channel_ids, username):
    today = date.today().isoformat()
    if daemon_state.get("last_batch_date") == today:
        return
    now_str = datetime.now().strftime("%H:%M")
    if now_str < daily_batch_time:
        return
    print(f"[{datetime.now().isoformat(timespec='seconds')}] Running daily digest for {today}")
    candidates = oe.extract_digest(base_url, token, channel_ids, username)
    _post_candidates(candidates, base_url, token)
    daemon_state["last_batch_date"] = today


def _post_candidates(candidates, base_url, token):
    if not candidates:
        return
    _, _, bilingual, _, _ = oe.load_config()
    if bilingual:
        candidates = [oe.make_bilingual(c) for c in candidates]
    for c in candidates:
        dup_title = oe.find_duplicate(base_url, token, c)
        if dup_title:
            print(f"  Skipped (duplicate of \"{dup_title}\"): {oe._text_for_compare(c.get('title'))}")
            continue
        result = oe.post_draft(base_url, token, c)
        if result:
            print(f"  Drafted: [{c.get('category')}] {oe._text_for_compare(c.get('title'))}")


def main():
    base_url, token, _bilingual, idle_minutes, daily_batch_time = oe.load_config()
    cfg = oe.get_config(base_url, token)
    if cfg is None:
        print("Couldn't reach Ourfeed, check OURFEED_URL and that the server is running")
        sys.exit(1)
    channel_ids = [c["id"] for c in cfg.get("channels", [])]
    username = oe.get_username(base_url, token)

    print(f"Ourfeed daemon started for {username}, watching {oe.CLAUDE_PROJECTS_DIR}")
    print(f"  idle threshold: {idle_minutes} min, daily digest at {daily_batch_time}")

    daemon_state = load_daemon_state()
    session_state = oe.load_state()

    try:
        while True:
            check_idle_sessions(daemon_state, idle_minutes, base_url, token, channel_ids, username, session_state)
            check_daily_batch(daemon_state, daily_batch_time, base_url, token, channel_ids, username)
            save_daemon_state(daemon_state)
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped")


if __name__ == "__main__":
    main()
