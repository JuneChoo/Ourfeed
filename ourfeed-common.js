// 全局状态：启动时由 initAuth() 填充
let OURFEED_CONFIG = null;   // { site_name, tagline, channels: [{id,label,icon,color}] }
let ME = null;                // 当前登录用户 { id, username, display_name, avatar_color, role }

const entryCache = {};
function cacheEntry(entry) { entryCache[entry.id] = entry; return entry; }

function channelMeta(id) {
  return (OURFEED_CONFIG.channels || []).find(c => c.id === id) || { id, label: id, icon: "", color: "#888" };
}

function initials(name) {
  return (name || "?").trim().slice(0, 1).toUpperCase();
}

function channelTagsHtml(entry, editable) {
  cacheEntry(entry);
  const allIds = (OURFEED_CONFIG.channels || []).map(c => c.id);
  return allIds.map(id => {
    const meta = channelMeta(id);
    const label = `${meta.icon || ""} ${meta.label}`.trim();
    const on = entry.channels.includes(id);
    const style = `--tag-color:${meta.color}`;
    if (!editable) {
      return on ? `<span class="channel-tag" style="${style}">${label}</span>` : "";
    }
    const cls = on ? "channel-tag toggle" : "channel-tag off toggle";
    return `<span class="${cls}" style="${style}" onclick="toggleEntryChannel(${entry.id}, '${id}', event)">${label}</span>`;
  }).join("");
}

async function toggleEntryChannel(id, channelId, event) {
  event.stopPropagation();
  const entry = entryCache[id];
  if (!entry) return;
  let channels = entry.channels.slice();
  if (channels.includes(channelId)) {
    if (channels.length === 1) { showToast("至少要留一个标签", "⚠️"); return; }
    channels = channels.filter(c => c !== channelId);
  } else {
    channels.push(channelId);
  }
  try {
    await api(`/api/entries/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ channels }),
    });
    if (typeof onEntryChanged === "function") onEntryChanged();
  } catch (e) {
    alert("改标签失败: " + e.message);
  }
}

function avatarHtml(user, sizeClass) {
  return `<div class="${sizeClass}" style="--user-color:${user.avatar_color}">${initials(user.display_name)}</div>`;
}

function renderIdentityHead() {
  const el = document.getElementById("identity-head");
  if (!el || !ME) return;
  el.textContent = initials(ME.display_name);
  el.style.setProperty("--user-color", ME.avatar_color);
}

async function logout() {
  try { await api("/api/logout", { method: "POST" }); } catch (e) {}
  location.href = "login.html";
}

// 需要登录的页面（feed/review/admin）在启动时调用这个：
// 拉 /api/config 和 /api/me，没登录就跳去 login.html。成功后 resolve。
async function initAuth() {
  const cfgRes = await fetch("/api/config");
  OURFEED_CONFIG = await cfgRes.json();
  document.querySelectorAll(".site-name").forEach(el => el.textContent = OURFEED_CONFIG.site_name);

  const meRes = await fetch("/api/me");
  if (meRes.status === 401) {
    location.href = "login.html";
    return null;
  }
  ME = await meRes.json();
  renderIdentityHead();
  const toggle = document.getElementById("identity-toggle");
  if (toggle) toggle.addEventListener("click", logout);
  return ME;
}

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (res.status === 401) {
    location.href = "login.html";
    throw new Error("未登录");
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || ("请求失败 (" + res.status + ")"));
  return data;
}

function showToast(msg, icon) {
  const t = document.getElementById("toast");
  if (!t) return;
  document.getElementById("toast-msg").textContent = msg;
  const iconEl = document.getElementById("toast-icon");
  if (iconEl && icon) iconEl.textContent = icon;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2600);
}

function formatRelativeTime(iso) {
  const then = new Date(iso).getTime();
  const diffSec = Math.floor((Date.now() - then) / 1000);
  if (diffSec < 60) return "刚刚";
  if (diffSec < 3600) return Math.floor(diffSec / 60) + "分钟前";
  if (diffSec < 86400) return Math.floor(diffSec / 3600) + "小时前";
  if (diffSec < 172800) return "昨天";
  return Math.floor(diffSec / 86400) + "天前";
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

// ---- 编辑（草稿/已发布通用） ----
function openEditModal(id) {
  const entry = entryCache[id];
  if (!entry) return;
  document.getElementById("edit-id").value = id;
  document.getElementById("edit-title").value = entry.title || "";
  document.getElementById("edit-content").value = entry.content || "";
  document.getElementById("edit-modal").classList.add("show");
}
function closeEditModal() { document.getElementById("edit-modal").classList.remove("show"); }

async function submitEdit() {
  const id = document.getElementById("edit-id").value;
  const title = document.getElementById("edit-title").value.trim();
  const content = document.getElementById("edit-content").value.trim();
  if (!content) { alert("内容不能为空"); return; }
  try {
    await api(`/api/entries/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, title }),
    });
    closeEditModal();
    showToast("已保存修改", "✏️");
    if (typeof onEntryChanged === "function") onEntryChanged();
  } catch (e) {
    alert("保存失败: " + e.message);
  }
}

// ---- 删除（发布后条目走永久私有，不做硬删除） ----
async function deleteEntry(id) {
  if (!confirm("删除这条？内容不会真的消失，只是从黑板撤下、只有你自己能看，跟审核页的\"永久私有\"是同一件事。")) return;
  try {
    await api(`/api/entries/${id}/privatize`, { method: "POST" });
    showToast("已删除，撤下黑板", "🗑");
    if (typeof onEntryChanged === "function") onEntryChanged();
  } catch (e) {
    alert("删除失败: " + e.message);
  }
}
