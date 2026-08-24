"""
Ourfeed - a self-hosted, invite-only feed for the people you trust.
Start:  python ourfeed.py
Visit:  http://localhost:8731
Config: copy config.example.json to config.json to customize site name / channels.
"""
import hashlib
import http.cookies
import http.server
import json
import os
import re
import secrets
import shutil
import sqlite3
import sys
import urllib.parse
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BOARD_DIR = Path(__file__).parent
DB_FILE = Path(os.environ.get("OURFEED_DB_PATH", str(BOARD_DIR / "ourfeed.db")))
CONFIG_FILE = BOARD_DIR / "config.json"
CONFIG_EXAMPLE = BOARD_DIR / "config.example.json"

ENTRY_STATUSES = {"draft", "shared", "private"}
SESSION_COOKIE_NAME = "ourfeed_session"
SESSION_DAYS = 30
PBKDF2_ITERATIONS = 200_000
AVATAR_PALETTE = ["#e8834a", "#4a8fe8", "#6cad3a", "#c65ce0", "#e6432e", "#2ecc71", "#f8c93a", "#8a6339"]
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_salt TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    avatar_color TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS invite_codes (
    code TEXT PRIMARY KEY,
    created_by INTEGER NOT NULL REFERENCES users(id),
    used_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL,
    used_at TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS api_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    last_used_at TEXT
);

CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    parent_id INTEGER REFERENCES entries(id),
    created_at TEXT NOT NULL,
    shared_at TEXT,
    skipped_at TEXT,
    edited_at TEXT
);

CREATE TABLE IF NOT EXISTS entry_channels (
    entry_id INTEGER NOT NULL REFERENCES entries(id),
    channel_id TEXT NOT NULL,
    PRIMARY KEY (entry_id, channel_id)
);
"""


def _load_config():
    if not CONFIG_FILE.exists():
        shutil.copy(CONFIG_EXAMPLE, CONFIG_FILE)
        print(f"[ourfeed] 没找到 config.json，已用 config.example.json 生成一份默认配置")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    if not cfg.get("channels"):
        raise SystemExit("config.json 里 channels 不能为空，至少配一个标签")
    tagline = cfg.get("tagline", "")
    if isinstance(tagline, str):
        cfg["tagline"] = {"en": tagline, "zh": tagline}
    return cfg


CONFIG = _load_config()
PORT = int(os.environ.get("OURFEED_PORT", CONFIG.get("port", 8731)))
CHANNELS = CONFIG["channels"]
CHANNEL_IDS = {c["id"] for c in CHANNELS}
COOKIE_SECURE = bool(CONFIG.get("cookie_secure", False))


def _now():
    return datetime.now(timezone.utc).isoformat()


def _db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    with closing(_db()) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def _hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS)
    return salt, digest.hex()


def _verify_password(password, salt, expected_hash):
    _, computed = _hash_password(password, salt)
    return secrets.compare_digest(computed, expected_hash)


def _public_user(row):
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "avatar_color": row["avatar_color"],
        "role": row["role"],
    }


class BoardError(Exception):
    """带 HTTP 状态码的业务错误，路由层统一捕获转成 JSON 错误响应。"""
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


class BoardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BOARD_DIR), **kwargs)

    # ---------------- 认证 ----------------

    def _session_token(self):
        raw = self.headers.get("Cookie")
        if not raw:
            return None
        cookie = http.cookies.SimpleCookie()
        cookie.load(raw)
        morsel = cookie.get(SESSION_COOKIE_NAME)
        return morsel.value if morsel else None

    def _bearer_token(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[len("Bearer "):].strip()
        return None

    def _current_user(self, conn):
        api_token = self._bearer_token()
        if api_token:
            row = conn.execute(
                "SELECT t.id AS token_id, u.* FROM api_tokens t JOIN users u ON u.id = t.user_id WHERE t.token = ?",
                (api_token,),
            ).fetchone()
            if not row:
                return None
            conn.execute("UPDATE api_tokens SET last_used_at = ? WHERE id = ?", (_now(), row["token_id"]))
            conn.commit()
            return row

        token = self._session_token()
        if not token:
            return None
        row = conn.execute(
            "SELECT s.expires_at, u.* FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.token = ?",
            (token,),
        ).fetchone()
        if not row:
            return None
        if row["expires_at"] < _now():
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return None
        return row

    def _require_auth(self, conn):
        user = self._current_user(conn)
        if not user:
            raise BoardError(401, "请先登录")
        return user

    def _require_admin(self, conn):
        user = self._require_auth(conn)
        if user["role"] != "admin":
            raise BoardError(403, "只有管理员能做这个操作")
        return user

    def _make_session(self, conn, user_id):
        token = secrets.token_urlsafe(32)
        now = _now()
        expires = (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).isoformat()
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, user_id, now, expires),
        )
        return token

    def _cookie_header(self, token, clear=False):
        parts = [f"{SESSION_COOKIE_NAME}={token if not clear else ''}"]
        parts.append("Path=/")
        parts.append("HttpOnly")
        parts.append("SameSite=Lax")
        if COOKIE_SECURE:
            parts.append("Secure")
        if clear:
            parts.append("Max-Age=0")
        else:
            parts.append(f"Max-Age={SESSION_DAYS * 86400}")
        return "; ".join(parts)

    # ---------------- 路由 ----------------

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        try:
            if path == "/api/config":
                self._get_config()
            elif path == "/api/me":
                self._get_me()
            elif path == "/api/entries":
                self._list_entries(qs.get("channel", [""])[0])
            elif path == "/api/entries/review":
                self._list_review(qs.get("channel", [""])[0])
            elif path == "/api/entries/mine":
                self._list_mine(qs.get("status", [""])[0])
            elif path == "/api/invite-codes":
                self._list_invite_codes()
            elif path == "/api/tokens":
                self._list_tokens()
            elif path == "/":
                self.path = "/feed.html"
                super().do_GET()
            else:
                super().do_GET()
        except BoardError as e:
            self._send_error_json(e.status, e.message)

    def do_POST(self):
        path = self.path
        try:
            if path == "/api/register":
                self._register(self._read_json_body())
                return
            if path == "/api/login":
                self._login(self._read_json_body())
                return
            if path == "/api/logout":
                self._logout()
                return
            if path == "/api/invite-codes":
                self._create_invite_code()
                return
            if path == "/api/tokens":
                self._create_token(self._read_json_body())
                return
            m = re.fullmatch(r"/api/entries/(\d+)/respond", path)
            if m:
                self._respond_entry(int(m.group(1)), self._read_json_body())
                return
            m = re.fullmatch(r"/api/entries/(\d+)/privatize", path)
            if m:
                self._privatize_entry(int(m.group(1)))
                return
            m = re.fullmatch(r"/api/entries/(\d+)/skip", path)
            if m:
                self._skip_entry(int(m.group(1)))
                return
            if path == "/api/entries/publish":
                self._publish_entries(self._read_json_body())
                return
            if path == "/api/entries":
                self._create_entry(self._read_json_body())
                return
            self.send_error(404)
        except BoardError as e:
            self._send_error_json(e.status, e.message)

    def do_PATCH(self):
        path = self.path
        try:
            m = re.fullmatch(r"/api/entries/(\d+)", path)
            if m:
                self._update_entry(int(m.group(1)), self._read_json_body())
                return
            self.send_error(404)
        except BoardError as e:
            self._send_error_json(e.status, e.message)

    def do_DELETE(self):
        path = self.path
        try:
            m = re.fullmatch(r"/api/tokens/(\d+)", path)
            if m:
                self._revoke_token(int(m.group(1)))
                return
            self.send_error(404)
        except BoardError as e:
            self._send_error_json(e.status, e.message)

    # ---------------- 账号系统 ----------------

    def _get_config(self):
        with closing(_db()) as conn:
            has_users = conn.execute("SELECT 1 FROM users LIMIT 1").fetchone() is not None
        self._send_json({
            "site_name": CONFIG.get("site_name", "Ourfeed"),
            "tagline": CONFIG.get("tagline", ""),
            "channels": CHANNELS,
            "bootstrap": not has_users,
        })

    def _get_me(self):
        with closing(_db()) as conn:
            user = self._current_user(conn)
        if not user:
            raise BoardError(401, "未登录")
        self._send_json(_public_user(user))

    def _register(self, body):
        username = (body.get("username") or "").strip()
        password = body.get("password") or ""
        display_name = (body.get("display_name") or "").strip() or username
        invite_code = (body.get("invite_code") or "").strip()

        if not USERNAME_RE.match(username):
            raise BoardError(400, "用户名 3-20 位，只能是字母/数字/下划线/横线")
        if len(password) < 8:
            raise BoardError(400, "密码至少 8 位")

        with closing(_db()) as conn:
            has_users = conn.execute("SELECT 1 FROM users LIMIT 1").fetchone() is not None
            existing = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
            if existing:
                raise BoardError(400, "用户名已被占用")

            invite_row = None
            if has_users:
                if not invite_code:
                    raise BoardError(400, "需要邀请码")
                invite_row = conn.execute(
                    "SELECT * FROM invite_codes WHERE code = ? AND used_by IS NULL", (invite_code,)
                ).fetchone()
                if not invite_row:
                    raise BoardError(400, "邀请码无效或已被使用")

            role = "admin" if not has_users else "member"
            salt, pw_hash = _hash_password(password)
            user_count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
            avatar_color = AVATAR_PALETTE[user_count % len(AVATAR_PALETTE)]
            now = _now()
            cur = conn.execute(
                "INSERT INTO users (username, password_salt, password_hash, display_name, avatar_color, role, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (username, salt, pw_hash, display_name, avatar_color, role, now),
            )
            user_id = cur.lastrowid
            if invite_row:
                conn.execute(
                    "UPDATE invite_codes SET used_by = ?, used_at = ? WHERE code = ?",
                    (user_id, now, invite_code),
                )
            token = self._make_session(conn, user_id)
            conn.commit()
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

        self._send_json(_public_user(row), status=201, set_cookie=self._cookie_header(token))

    def _login(self, body):
        username = (body.get("username") or "").strip()
        password = body.get("password") or ""
        with closing(_db()) as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if not row or not _verify_password(password, row["password_salt"], row["password_hash"]):
                raise BoardError(401, "用户名或密码不对")
            token = self._make_session(conn, row["id"])
            conn.commit()
        self._send_json(_public_user(row), set_cookie=self._cookie_header(token))

    def _logout(self):
        token = self._session_token()
        if token:
            with closing(_db()) as conn:
                conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
        self._send_json({"ok": True}, set_cookie=self._cookie_header("", clear=True))

    def _create_invite_code(self):
        with closing(_db()) as conn:
            admin = self._require_admin(conn)
            code = secrets.token_urlsafe(6)
            conn.execute(
                "INSERT INTO invite_codes (code, created_by, created_at) VALUES (?, ?, ?)",
                (code, admin["id"], _now()),
            )
            conn.commit()
        self._send_json({"code": code}, status=201)

    def _list_invite_codes(self):
        with closing(_db()) as conn:
            self._require_admin(conn)
            rows = conn.execute(
                "SELECT ic.code, ic.created_at, ic.used_at, u.username AS used_by_username "
                "FROM invite_codes ic LEFT JOIN users u ON u.id = ic.used_by "
                "ORDER BY ic.created_at DESC"
            ).fetchall()
        self._send_json([dict(r) for r in rows])

    def _create_token(self, body):
        """API token: 跟登录 session 分开的凭据，给脚本/AI agent 这类不走浏览器的调用方用。
        权限等同本人：拿着 token 调 API 就等于以这个用户身份操作，跟登录态是同一套鉴权。"""
        label = (body.get("label") or "").strip()
        with closing(_db()) as conn:
            user = self._require_auth(conn)
            token = "of_" + secrets.token_urlsafe(32)
            conn.execute(
                "INSERT INTO api_tokens (user_id, token, label, created_at) VALUES (?, ?, ?, ?)",
                (user["id"], token, label, _now()),
            )
            conn.commit()
        self._send_json({"token": token, "label": label}, status=201)

    def _list_tokens(self):
        with closing(_db()) as conn:
            user = self._require_auth(conn)
            rows = conn.execute(
                "SELECT id, label, created_at, last_used_at FROM api_tokens WHERE user_id = ? ORDER BY created_at DESC",
                (user["id"],),
            ).fetchall()
        self._send_json([dict(r) for r in rows])

    def _revoke_token(self, token_id):
        with closing(_db()) as conn:
            user = self._require_auth(conn)
            existing = conn.execute(
                "SELECT id FROM api_tokens WHERE id = ? AND user_id = ?", (token_id, user["id"])
            ).fetchone()
            if not existing:
                raise BoardError(404, "token 不存在")
            conn.execute("DELETE FROM api_tokens WHERE id = ?", (token_id,))
            conn.commit()
        self._send_json({"ok": True})

    # ---------------- entries: 读取 ----------------

    def _fetch_entries(self, conn, where_sql, params):
        rows = conn.execute(
            "SELECT e.*, u.username AS author, u.display_name AS author_display_name, "
            "u.avatar_color AS author_avatar_color "
            "FROM entries e JOIN users u ON u.id = e.author_id "
            f"WHERE {where_sql}",
            params,
        ).fetchall()
        entries = [dict(r) for r in rows]
        if not entries:
            return entries
        ids = [e["id"] for e in entries]
        placeholders = ",".join("?" * len(ids))
        channel_rows = conn.execute(
            f"SELECT entry_id, channel_id FROM entry_channels WHERE entry_id IN ({placeholders})", ids
        ).fetchall()
        by_entry = {}
        for r in channel_rows:
            by_entry.setdefault(r["entry_id"], []).append(r["channel_id"])
        for e in entries:
            e["channels"] = by_entry.get(e["id"], [])
        return entries

    def _fetch_entry(self, conn, entry_id):
        rows = self._fetch_entries(conn, "e.id = ?", (entry_id,))
        return rows[0] if rows else None

    def _list_entries(self, channel_filter):
        """黑板只显示已发布的条目，草稿/私有一律不出现。可选 ?channel= 筛选，命中即显示。"""
        with closing(_db()) as conn:
            self._require_auth(conn)
            where = "e.status = 'shared'"
            params = []
            if channel_filter in CHANNEL_IDS:
                where += " AND e.id IN (SELECT entry_id FROM entry_channels WHERE channel_id = ?)"
                params.append(channel_filter)
            entries = self._fetch_entries(conn, where, params)
        entries.sort(key=lambda e: e.get("shared_at") or "", reverse=True)
        self._send_json(entries)

    def _list_review(self, channel_filter):
        """审核页（草稿箱）：当前登录用户自己的全部草稿，老的排前面。"""
        with closing(_db()) as conn:
            user = self._require_auth(conn)
            where = "e.status = 'draft' AND e.author_id = ?"
            params = [user["id"]]
            if channel_filter in CHANNEL_IDS:
                where += " AND e.id IN (SELECT entry_id FROM entry_channels WHERE channel_id = ?)"
                params.append(channel_filter)
            entries = self._fetch_entries(conn, where, params)
        entries.sort(key=lambda e: e.get("created_at") or "")
        self._send_json(entries)

    def _list_mine(self, status_filter):
        """当前用户自己创建的全部条目，不限状态（draft/shared/private都算）。
        给自动化脚本用来回查"之前存的草稿后来被怎么处理了"，也是"私有档案"这个
        以后要做的view现在就能用的底层数据源。"""
        with closing(_db()) as conn:
            user = self._require_auth(conn)
            where = "e.author_id = ?"
            params = [user["id"]]
            if status_filter in ENTRY_STATUSES:
                where += " AND e.status = ?"
                params.append(status_filter)
            entries = self._fetch_entries(conn, where, params)
        entries.sort(key=lambda e: e.get("created_at") or "", reverse=True)
        self._send_json(entries)

    # ---------------- entries: 写入 ----------------

    def _parse_channels(self, value):
        if not value or not isinstance(value, list) or not set(value).issubset(CHANNEL_IDS):
            raise BoardError(400, f"channels 必须是 {sorted(CHANNEL_IDS)} 的非空子集")
        return list(dict.fromkeys(value))

    def _set_entry_channels(self, conn, entry_id, channel_ids):
        conn.execute("DELETE FROM entry_channels WHERE entry_id = ?", (entry_id,))
        conn.executemany(
            "INSERT INTO entry_channels (entry_id, channel_id) VALUES (?, ?)",
            [(entry_id, c) for c in channel_ids],
        )

    def _create_entry(self, body):
        title = (body.get("title") or "").strip()
        content = (body.get("content") or "").strip()
        if not content:
            raise BoardError(400, "content 不能为空")
        if not title:
            raise BoardError(400, "title 不能为空")
        channels = self._parse_channels(body.get("channels"))
        with closing(_db()) as conn:
            user = self._require_auth(conn)
            cur = conn.execute(
                "INSERT INTO entries (author_id, title, content, status, parent_id, created_at) "
                "VALUES (?, ?, ?, 'draft', NULL, ?)",
                (user["id"], title, content, _now()),
            )
            entry_id = cur.lastrowid
            self._set_entry_channels(conn, entry_id, channels)
            conn.commit()
            row = self._fetch_entry(conn, entry_id)
        self._send_json(row, status=201)

    def _respond_entry(self, parent_id, body):
        """回应是人当场手动打字发出去的，不用再经过审核页那层"防AI乱发"的保护，直接发布。
        channels 自动继承原贴的。"""
        content = (body.get("content") or "").strip()
        if not content:
            raise BoardError(400, "content 不能为空")
        now = _now()
        with closing(_db()) as conn:
            user = self._require_auth(conn)
            parent = conn.execute("SELECT id FROM entries WHERE id = ?", (parent_id,)).fetchone()
            if not parent:
                raise BoardError(404, "被回应的 entry 不存在")
            parent_channels = [r["channel_id"] for r in conn.execute(
                "SELECT channel_id FROM entry_channels WHERE entry_id = ?", (parent_id,)
            ).fetchall()]
            cur = conn.execute(
                "INSERT INTO entries (author_id, title, content, status, parent_id, created_at, shared_at) "
                "VALUES (?, '', ?, 'shared', ?, ?, ?)",
                (user["id"], content, parent_id, now, now),
            )
            entry_id = cur.lastrowid
            self._set_entry_channels(conn, entry_id, parent_channels)
            conn.commit()
            row = self._fetch_entry(conn, entry_id)
        self._send_json(row, status=201)

    def _require_owner(self, conn, entry_id, user):
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if not row:
            raise BoardError(404, "entry 不存在")
        if row["author_id"] != user["id"]:
            raise BoardError(403, "只能操作自己的条目")
        return row

    def _privatize_entry(self, entry_id):
        """永久私有：内容不删除，只是退出审核队列和黑板，以后只有作者自己能看。
        发布后的条目从黑板上点"删除"，走的也是这个动作。"""
        with closing(_db()) as conn:
            user = self._require_auth(conn)
            self._require_owner(conn, entry_id, user)
            conn.execute("UPDATE entries SET status = 'private' WHERE id = ?", (entry_id,))
            conn.commit()
            row = self._fetch_entry(conn, entry_id)
        self._send_json(row)

    def _skip_entry(self, entry_id):
        """这次不发：状态仍是 draft，只记一下跳过时间，下次审核页还会再出现。"""
        with closing(_db()) as conn:
            user = self._require_auth(conn)
            row = self._require_owner(conn, entry_id, user)
            if row["status"] != "draft":
                raise BoardError(400, "只有草稿状态的条目能跳过")
            conn.execute("UPDATE entries SET skipped_at = ? WHERE id = ?", (_now(), entry_id))
            conn.commit()
            row = self._fetch_entry(conn, entry_id)
        self._send_json(row)

    def _publish_entries(self, body):
        """审核页"确认发布本轮"：批量把还留在草稿箱里、没被排除的条目转成共享。"""
        ids = body.get("ids") or []
        if not ids or not all(isinstance(i, int) for i in ids):
            raise BoardError(400, "ids 必须是非空的整数数组")
        now = _now()
        with closing(_db()) as conn:
            user = self._require_auth(conn)
            placeholders = ",".join("?" * len(ids))
            conn.execute(
                f"UPDATE entries SET status = 'shared', shared_at = ? "
                f"WHERE id IN ({placeholders}) AND author_id = ? AND status = 'draft'",
                (now, *ids, user["id"]),
            )
            conn.commit()
            rows = self._fetch_entries(conn, f"e.id IN ({placeholders})", ids)
        self._send_json(rows)

    def _update_entry(self, entry_id, body):
        """编辑自己的条目：标题/正文/频道标签，草稿和已发布的都能改。改标题/正文才盖 edited_at
        时间戳，单纯改频道标签不算"编辑过内容"，不盖戳。"""
        fields, values = [], []
        touched_content = False
        if "title" in body:
            fields.append("title = ?"); values.append((body["title"] or "").strip())
            touched_content = True
        if "content" in body:
            content = (body["content"] or "").strip()
            if not content:
                raise BoardError(400, "content 不能为空")
            fields.append("content = ?"); values.append(content)
            touched_content = True
        if touched_content:
            fields.append("edited_at = ?"); values.append(_now())
        with closing(_db()) as conn:
            user = self._require_auth(conn)
            self._require_owner(conn, entry_id, user)
            if fields:
                values.append(entry_id)
                conn.execute(f"UPDATE entries SET {', '.join(fields)} WHERE id = ?", values)
            if "channels" in body:
                channels = self._parse_channels(body["channels"])
                self._set_entry_channels(conn, entry_id, channels)
            if not fields and "channels" not in body:
                raise BoardError(400, "没有可更新的字段")
            conn.commit()
            row = self._fetch_entry(conn, entry_id)
        self._send_json(row)

    # ---------------- 工具方法 ----------------

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise BoardError(400, "请求体不是合法 JSON")

    def _send_json(self, data, status=200, set_cookie=None):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        if set_cookie:
            self.send_header("Set-Cookie", set_cookie)
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _send_error_json(self, status, message):
        self._send_json({"error": message}, status=status)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    _init_db()
    print("Ourfeed started")
    print(f"  URL: http://localhost:{PORT}")
    print(f"  DB:  {DB_FILE}")
    print(f"  Config: {CONFIG_FILE}")
    print("  Ctrl+C to quit")
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), BoardHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nOurfeed 已关闭")
