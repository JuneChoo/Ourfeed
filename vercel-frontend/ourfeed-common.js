// ---- i18n ----
const I18N = {
  en: {
    nav_feed: "📗 Feed", nav_drafts: "🗃️ Drafts", nav_admin: "🛠️ Admin", nav_automation: "🤖 Automation",
    logout_title: "Log out",
    btn_cancel: "Cancel", btn_save: "Save", btn_post: "Post",
    edit_modal_title: "Edit", edit_label_title: "Title", edit_label_content: "Content",
    err_prefix: "Can't reach the server: ", err_suffix: "Check that ourfeed.py is running.",
    just_now: "just now", minutes_ago: "{n}m ago", hours_ago: "{n}h ago",
    yesterday: "yesterday", days_ago: "{n}d ago",
    confirm_delete: "Delete this? The content isn't actually removed, it just comes off the feed and only you can see it. Same as \"Keep private\" in Drafts.",
    toast_deleted: "Deleted, off the feed", alert_delete_failed: "Delete failed: ",
    err_keep_one_tag: "Keep at least one tag", alert_tag_failed: "Failed to change tag: ",
    alert_content_required: "Content can't be empty", toast_saved_edit: "Saved",
    alert_save_failed: "Save failed: ", err_not_logged_in: "Not logged in", err_request_failed: "Request failed ({status})",

    feed_section_title: "Feed", feed_section_sub: "Picked and narrated by your own agent, opinions included",
    tab_all: "All", stat_shared: "{n} shared",
    empty_feed_title: "Nothing here yet", empty_feed_body: "Tap “+” to share the first thing",
    composer_title: "Share something", composer_channel_label: "Tag it (pick at least one)",
    composer_title_label: "Title", composer_title_placeholder: "One line title",
    composer_content_label: "Content", composer_content_placeholder: "Future you (or them) will thank you for the detail",
    composer_hint: "This goes into your drafts first. Publish it from “Drafts” when you're ready.",
    btn_save_draft: "Save draft",
    reply_title: "Reply", reply_content_label: "Your reply",
    reply_content_placeholder: "Add on, dig deeper, or push back",
    reply_hint: "Replies are written live, so they publish immediately (no draft review).",
    toast_draft_saved_title: "DRAFT SAVED", toast_draft_saved_msg: "Saved to drafts",
    reply_suffix: " · reply", edited_tag: "edited", new_tag: "NEW",
    btn_edit: "✏️ Edit", btn_delete: "🗑 Delete", btn_reply: "💬 Reply",
    alert_title_content_required: "Title and content are both required",
    alert_pick_tag: "Pick at least one tag",
    toast_draft_saved2: "Saved to drafts, publish it from Drafts",
    alert_save_failed2: "Save failed: ",
    alert_write_something: "Write something first",
    toast_reply_posted: "Reply posted", alert_post_failed: "Post failed: ",

    offline_banner: "They're not at their desk right now, these are their existing posts",
    public_reply_prompt: "Log in with an invite code to reply",

    drafts_section_title: "Drafts", drafts_section_sub: "Opt-out review: leave it alone and it gets published",
    rule1: "<b>Keep private</b>: the content isn't deleted, you're just deciding this one isn't for sharing. It leaves the queue and only you can see it.",
    rule2: "<b>Skip for now</b>: stays a draft, comes back next time you open this page.",
    rule3: "Everything you don't exclude gets published when you hit “Publish this round” below.",
    stat_drafts: "Drafts: {n}", empty_drafts_title: "Drafts are empty",
    empty_drafts_body: "Go to <a href=\"feed.html\">Feed</a> and write something",
    publish_count: "{n} pending", btn_publish: "✓ Publish this round",
    btn_keep_private: "🔒 Keep private", btn_skip: "⏭ Skip for now",
    toast_privatized: "Marked private, out of the queue",
    toast_skipped: "Skipped, it'll ask again next time",
    toast_published: "{n} published to the feed",
    alert_failed: "Failed: ", alert_publish_failed: "Publish failed: ",
    toast_title_achievement: "ACHIEVEMENT GET!", toast_published_default: "Published",

    login_title: "Log in", label_username: "Username", label_password: "Password",
    btn_login: "Log in", no_account: "No account?", register_link: "Register with an invite code",
    err_enter_both: "Enter username and password", err_login_failed: "Login failed",

    label_invite: "Invite code", label_display_name: "Display name",
    display_name_placeholder: "Optional, defaults to username",
    username_placeholder: "3-20 letters/numbers/_/-", password_placeholder: "At least 8 characters",
    btn_create_account: "Create account", already_have: "Already have an account?", login_link: "Log in",
    register_bootstrap_hint: "No account exists yet, you'll become the admin.",
    err_required: "Username and password are required", err_invite_required: "Invite code is required",
    err_register_failed: "Registration failed",

    admin_section_title: "Invite codes",
    admin_section_sub: "Generate a code so new people can register. You choose how many people each code can be used by.",
    btn_generate: "+ Generate invite code", empty_invites: "No invite codes yet",
    used_by: "used by {name}", unused: "unused", admin_only: "Only admins can see this page.",
    prompt_new_code: "New invite code (copy it and send to the person you're inviting):",
    prompt_max_uses: "How many people can use this code? (1 = normal one-time invite)",
    err_max_uses_invalid: "Enter a whole number, 1 or more",
    uses_count: "{used}/{max} used",

    automation_section_title: "Automation",
    automation_section_sub: "Let a script or AI agent post drafts on your behalf, using your own account.",
    automation_explainer: "Anything posted with a token still lands in Drafts, not straight on the feed. You still confirm it from there before anyone else sees it. The review step doesn't get skipped just because a machine wrote it.",
    btn_generate_token: "+ Generate API token",
    label_token_name: "Label (optional, e.g. \"my AI agent\")",
    empty_tokens: "No API tokens yet",
    last_used_never: "never used",
    last_used_label: "last used {time}",
    btn_revoke: "Revoke",
    confirm_revoke_token: "Revoke this token? Anything using it will stop working immediately.",
    prompt_new_token: "New API token, copy it now, you won't be able to see it again:",
    automation_howto_title: "How to connect something",
    automation_howto_body: "Pick whichever of these three matches what you've got. Generate a token above first, the boxes below fill in automatically with the real value for the rest of this visit (reload the page and they go back to a placeholder, for safety).",
    automation_token_placeholder_note: "Showing a placeholder until you generate a token above.",
    automation_token_filled_note: "Filled in with your real token. Reload this page and it goes back to a placeholder.",
    copy_btn: "Copy",
    copied_label: "Copied",

    path_a_title: "Option A: Ask your AI assistant",
    path_a_intro: "If you already talk to an AI assistant that can make web requests (Claude Code, ChatGPT with tools/actions enabled, or similar), this is the easiest path. No coding required, you're just giving it instructions in plain English. The message below tells it to draft things on its own judgment rather than wait to be asked, anything it writes still lands in your Drafts for review first.",
    path_a_step1: "Generate a token above and copy it.",
    path_a_step2: "Open a conversation with your AI assistant.",
    path_a_step3: "Paste the message below into the chat.",
    path_a_note: "This only works if your assistant can actually send HTTP requests on its own. If it can't, or you're not sure, use Option B instead.",

    path_b_title: "Option B: A no-code automation tool",
    path_b_intro: "Works with Zapier, Make, n8n, IFTTT, or anything with a generic \"HTTP Request\" or \"Webhook\" action step.",
    path_b_step1: "Generate a token above and copy it.",
    path_b_step2: "In your automation tool, add a step called \"HTTP Request\" or \"Webhook\" (the exact name depends on the tool).",
    path_b_step3: "Fill in these fields exactly:",
    path_b_step4: "Run it once, then check your Drafts page, the test post should be waiting there.",
    field_method: "Method", field_url: "URL", field_headers: "Headers", field_body: "Body (JSON)",

    path_c_title: "Option C: Write it yourself",
    path_c_intro: "For developers, or to hand to someone you're asking to build this for you.",

    path_a_message: "I want you to help me keep a record on my Ourfeed feed. When you notice something worth sharing in our conversation, something I finished, decided, or figured out, don't wait for me to ask, just send an HTTP POST request to {origin}/api/entries with these headers: Authorization: Bearer {token}, and Content-Type: application/json. The request body should be JSON like: {title: '...', content: '...', channels: ['work']}. Valid channels are: {channelIds}. It lands in my Drafts for me to review before anything goes public, so use your own judgment. Confirm you understand.",
  },
  zh: {
    nav_feed: "📗 动态", nav_drafts: "🗃️ 草稿箱", nav_admin: "🛠️ 管理", nav_automation: "🤖 自动化",
    logout_title: "退出登录",
    btn_cancel: "取消", btn_save: "保存", btn_post: "发布",
    edit_modal_title: "编辑", edit_label_title: "标题", edit_label_content: "内容",
    err_prefix: "连接不上服务器：", err_suffix: "确认 ourfeed.py 是不是在跑。",
    just_now: "刚刚", minutes_ago: "{n}分钟前", hours_ago: "{n}小时前",
    yesterday: "昨天", days_ago: "{n}天前",
    confirm_delete: "删除这条？内容不会真的消失，只是从动态撤下、只有你自己能看，跟草稿箱的“永久私有”是同一件事。",
    toast_deleted: "已删除，撤下动态", alert_delete_failed: "删除失败：",
    err_keep_one_tag: "至少要留一个标签", alert_tag_failed: "改标签失败：",
    alert_content_required: "内容不能为空", toast_saved_edit: "已保存修改",
    alert_save_failed: "保存失败：", err_not_logged_in: "未登录", err_request_failed: "请求失败（{status}）",

    feed_section_title: "动态", feed_section_sub: "由你的AI挑选、用它自己的话讲出来的，可能会吐槽你哦",
    tab_all: "全部", stat_shared: "已分享 {n} 条",
    empty_feed_title: "这里还空着", empty_feed_body: "点右下角“+”分享第一条",
    composer_title: "写点新动态", composer_channel_label: "打标签（至少选一个）",
    composer_title_label: "标题", composer_title_placeholder: "一句话标题",
    composer_content_label: "内容", composer_content_placeholder: "写清楚点，未来的自己/对方会感谢你",
    composer_hint: "会先进草稿箱，去“草稿箱”确认发布才会出现在动态里。",
    btn_save_draft: "存草稿",
    reply_title: "写个回应", reply_content_label: "回应内容",
    reply_content_placeholder: "补充、深化，或反驳一下",
    reply_hint: "回应是当场手写的，直接发布，不用再审核。",
    toast_draft_saved_title: "已存草稿", toast_draft_saved_msg: "已存草稿",
    reply_suffix: " · 回应", edited_tag: "已编辑", new_tag: "新",
    btn_edit: "✏️ 编辑", btn_delete: "🗑 删除", btn_reply: "💬 回应",
    alert_title_content_required: "标题和内容都要写",
    alert_pick_tag: "至少选一个标签",
    toast_draft_saved2: "已存草稿，去草稿箱发布",
    alert_save_failed2: "保存失败：",
    alert_write_something: "写点什么再提交",
    toast_reply_posted: "回应已发布", alert_post_failed: "发布失败：",

    offline_banner: "TA现在不在电脑前，这些是已经发过的内容",
    public_reply_prompt: "用邀请码登录才能回应",

    drafts_section_title: "草稿箱", drafts_section_sub: "反选式：不动它 = 会被发布",
    rule1: "<b>永久私有</b>：内容不会消失，只是这条你决定以后也不打算分享了，退出这里，以后只有你自己能看。",
    rule2: "<b>这次不发</b>：留在草稿箱，这一轮不发，下次打开这里还会再问你一次。",
    rule3: "剩下没被排除的，点下面“确认发布本轮”，一次性全部发布。",
    stat_drafts: "草稿 {n} 条", empty_drafts_title: "草稿箱空的",
    empty_drafts_body: "去<a href=\"feed.html\">动态</a>写点什么吧",
    publish_count: "{n} 条待发布", btn_publish: "✓ 确认发布本轮",
    btn_keep_private: "🔒 永久私有", btn_skip: "⏭ 这次不发",
    toast_privatized: "已设为永久私有，退出草稿箱",
    toast_skipped: "这次不发，留着下次再问你",
    toast_published: "{n} 条已发布到动态",
    alert_failed: "操作失败：", alert_publish_failed: "发布失败：",
    toast_title_achievement: "成就达成！", toast_published_default: "已发布",

    login_title: "登录", label_username: "用户名", label_password: "密码",
    btn_login: "登录", no_account: "还没有账号？", register_link: "用邀请码注册",
    err_enter_both: "请输入用户名和密码", err_login_failed: "登录失败",

    label_invite: "邀请码", label_display_name: "昵称",
    display_name_placeholder: "选填，默认用用户名",
    username_placeholder: "3-20位字母/数字/_/-", password_placeholder: "至少8位",
    btn_create_account: "创建账号", already_have: "已经有账号了？", login_link: "登录",
    register_bootstrap_hint: "还没有任何账号，你将成为管理员。",
    err_required: "用户名和密码都要填", err_invite_required: "邀请码不能为空",
    err_register_failed: "注册失败",

    admin_section_title: "邀请码",
    admin_section_sub: "生成邀请码给新成员注册，每个码能被多少人用由你决定。",
    btn_generate: "+ 生成邀请码", empty_invites: "还没有邀请码",
    used_by: "已被 {name} 使用", unused: "未使用", admin_only: "只有管理员能看这个页面。",
    prompt_new_code: "新邀请码（复制发给你要邀请的人）：",
    prompt_max_uses: "这个码最多允许几个人用？（填1就是普通的一次性邀请码）",
    err_max_uses_invalid: "请填一个大于等于1的整数",
    uses_count: "已用 {used}/{max}",

    automation_section_title: "自动化",
    automation_section_sub: "让脚本或AI用你自己的账号帮你存草稿。",
    automation_explainer: "用令牌发的内容一样先进草稿箱，不会直接上动态。你还是要去草稿箱确认才会被别人看到，机器写的也不例外，审核这一步不会因为是自动发的就被跳过。",
    btn_generate_token: "+ 生成API令牌",
    label_token_name: "备注（选填，比如“我的AI助手”）",
    empty_tokens: "还没有API令牌",
    last_used_never: "从未使用过",
    last_used_label: "上次使用：{time}",
    btn_revoke: "撤销",
    confirm_revoke_token: "撤销这个令牌？正在用它的脚本/AI会立刻失效。",
    prompt_new_token: "新API令牌，现在就复制，之后就看不到了：",
    automation_howto_title: "怎么接进去",
    automation_howto_body: "看下面三种方式，哪个符合你的情况就用哪个。先在上面生成一个token，下面的框会自动填上真实的token值（仅限这次打开这个页面期间，刷新页面就变回占位符，这是为了安全）。",
    automation_token_placeholder_note: "在你上面生成token之前，这里先显示占位符。",
    automation_token_filled_note: "已经帮你填上真实token了，刷新这个页面会变回占位符。",
    copy_btn: "复制",
    copied_label: "已复制",

    path_a_title: "方式A：直接让你的AI助手做",
    path_a_intro: "如果你已经在跟一个能发网络请求的AI助手对话（比如Claude Code、开了工具/actions能力的ChatGPT等），这是最简单的路，不用写代码，就是拿人话跟它说清楚要干什么。下面这段话是让它按自己判断主动写，不用等你开口，写的东西照样要先过你的草稿箱审核。",
    path_a_step1: "在上面生成一个token并复制。",
    path_a_step2: "打开跟你的AI助手的对话。",
    path_a_step3: "把下面这段话贴进对话框。",
    path_a_note: "这只在你的助手真的能自己发HTTP请求时有效。如果做不到或者不确定，改用方式B。",

    path_b_title: "方式B：免代码自动化工具",
    path_b_intro: "适用于 Zapier、Make、n8n、IFTTT，或者任何带通用“HTTP请求”/“Webhook”动作的工具。",
    path_b_step1: "在上面生成一个token并复制。",
    path_b_step2: "在你的自动化工具里加一步“HTTP Request”或“Webhook”（具体叫法看工具而定）。",
    path_b_step3: "按下面这些字段原样填：",
    path_b_step4: "跑一次试试，然后去草稿箱页面看，测试帖应该已经在那里等着了。",
    field_method: "方法（Method）", field_url: "地址（URL）", field_headers: "请求头（Headers）", field_body: "请求体（Body，JSON）",

    path_c_title: "方式C：自己写代码",
    path_c_intro: "给开发者看的，或者你要找人帮你做这个的时候直接给他看这段。",

    path_a_message: "我想让你帮我在Ourfeed上记点东西。你在对话里注意到什么值得记的，比如我做完的事、想明白的事、学到的东西，不用等我开口，直接往 {origin}/api/entries 发一个HTTP POST请求，带上这两个请求头：Authorization: Bearer {token}，以及 Content-Type: application/json。请求体用JSON格式，像这样：{title: '...', content: '...', channels: ['work']}。可用的channel有：{channelIds}。它会先进我的草稿箱，发不发出去我说了算，所以你放心按自己的判断来。确认你明白了。",
  },
};

function getLang() {
  const saved = localStorage.getItem("of_lang");
  if (saved) return saved;
  return "en";
}
let LANG = getLang();

function t(key, vars) {
  let s = (I18N[LANG] && I18N[LANG][key]) || I18N.en[key] || key;
  if (vars) Object.keys(vars).forEach(k => { s = s.replace(`{${k}}`, vars[k]); });
  return s;
}

function applyI18n(scope) {
  scope = scope || document;
  scope.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.getAttribute("data-i18n")); });
  scope.querySelectorAll("[data-i18n-html]").forEach(el => { el.innerHTML = t(el.getAttribute("data-i18n-html")); });
  scope.querySelectorAll("[data-i18n-placeholder]").forEach(el => { el.placeholder = t(el.getAttribute("data-i18n-placeholder")); });
  scope.querySelectorAll("[data-i18n-title]").forEach(el => { el.title = t(el.getAttribute("data-i18n-title")); });
}

function renderLangToggle() {
  document.querySelectorAll(".lang-toggle").forEach(el => { el.textContent = LANG === "zh" ? "EN" : "中文"; });
}

function renderTagline() {
  if (!OURFEED_CONFIG) return;
  const tagline = OURFEED_CONFIG.tagline;
  const text = typeof tagline === "string" ? tagline : ((tagline && (tagline[LANG] || tagline.en)) || "");
  document.querySelectorAll(".tagline").forEach(el => { el.textContent = text; });
}

// Optional per-instance override for the feed page's subtitle (config.json's
// feed_section_sub, same {en,zh}-or-plain-string shape as tagline). Falls
// back to the built-in I18N default (already applied by applyI18n()) if the
// instance hasn't set one, so this only touches the DOM when there's
// actually a custom value.
function renderFeedSectionSub() {
  if (!OURFEED_CONFIG) return;
  const sub = OURFEED_CONFIG.feed_section_sub;
  const text = typeof sub === "string" ? sub : ((sub && (sub[LANG] || sub.en)) || "");
  if (!text) return;
  document.querySelectorAll('[data-i18n="feed_section_sub"]').forEach(el => { el.textContent = text; });
}

function setLang(lang) {
  LANG = lang;
  localStorage.setItem("of_lang", lang);
  document.documentElement.lang = lang;
  applyI18n();
  renderLangToggle();
  renderTagline();
  renderFeedSectionSub();
  if (typeof onLangChanged === "function") onLangChanged();
}

function toggleLang() { setLang(LANG === "zh" ? "en" : "zh"); }

function initI18n() {
  document.documentElement.lang = LANG;
  applyI18n();
  renderLangToggle();
  document.querySelectorAll(".lang-toggle").forEach(el => el.addEventListener("click", toggleLang));
}

async function copyText(elementId, btn) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const text = el.textContent;
  try {
    await navigator.clipboard.writeText(text);
  } catch (e) {
    const range = document.createRange();
    range.selectNodeContents(el);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  }
  if (btn) {
    const original = btn.textContent;
    btn.textContent = t("copied_label");
    setTimeout(() => { btn.textContent = original; }, 1500);
  }
}

// ---- 全局状态：启动时由 initAuth() 填充 ----
let OURFEED_CONFIG = null;   // { site_name, tagline: {en,zh}, channels: [{id,label,icon,color}] }
let ME = null;                // 当前登录用户 { id, username, display_name, avatar_color, role }

const entryCache = {};
function cacheEntry(entry) { entryCache[entry.id] = entry; return entry; }

function channelMeta(id) {
  return (OURFEED_CONFIG.channels || []).find(c => c.id === id) || { id, label: id, icon: "", color: "#888" };
}

function channelLabel(meta) {
  return typeof meta.label === "string" ? meta.label : ((meta.label && (meta.label[LANG] || meta.label.en)) || meta.id);
}

function initials(name) {
  return (name || "?").trim().slice(0, 1).toUpperCase();
}

function channelTagsHtml(entry, editable) {
  cacheEntry(entry);
  const allIds = (OURFEED_CONFIG.channels || []).map(c => c.id);
  return allIds.map(id => {
    const meta = channelMeta(id);
    const label = `${meta.icon || ""} ${channelLabel(meta)}`.trim();
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
    if (channels.length === 1) { showToast(t("err_keep_one_tag"), "⚠️"); return; }
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
    alert(t("alert_tag_failed") + e.message);
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
  initI18n();
  renderTagline();
  renderFeedSectionSub();

  const meRes = await fetch("/api/me");
  if (meRes.status === 401) {
    location.href = "login.html";
    return null;
  }
  ME = await meRes.json();
  renderIdentityHead();
  const toggle = document.getElementById("identity-toggle");
  if (toggle) toggle.addEventListener("click", logout);
  if (ME.role === "admin") {
    document.querySelectorAll(".admin-only-nav").forEach(el => { el.style.display = "inline-block"; });
  }
  return ME;
}

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (res.status === 401) {
    location.href = "login.html";
    throw new Error(t("err_not_logged_in"));
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || t("err_request_failed", { status: res.status }));
  return data;
}

function showToast(msg, icon) {
  const el = document.getElementById("toast");
  if (!el) return;
  document.getElementById("toast-msg").textContent = msg;
  const iconEl = document.getElementById("toast-icon");
  if (iconEl && icon) iconEl.textContent = icon;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2600);
}

function formatRelativeTime(iso) {
  const then = new Date(iso).getTime();
  const diffSec = Math.floor((Date.now() - then) / 1000);
  if (diffSec < 60) return t("just_now");
  if (diffSec < 3600) return t("minutes_ago", { n: Math.floor(diffSec / 60) });
  if (diffSec < 86400) return t("hours_ago", { n: Math.floor(diffSec / 3600) });
  if (diffSec < 172800) return t("yesterday");
  return t("days_ago", { n: Math.floor(diffSec / 86400) });
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

// entry title/content can be a plain string, or a JSON-encoded {en, zh}
// object (same idea as config.json's tagline/channel labels), stored as
// plain TEXT on the backend since it doesn't know or care about language.
// Picks the current LANG, falls back to en then zh, and leaves ordinary
// strings untouched.
function localizedField(value) {
  if (typeof value !== "string") return value || "";
  const trimmed = value.trim();
  if (!trimmed.startsWith("{")) return value;
  try {
    const parsed = JSON.parse(trimmed);
    if (parsed && typeof parsed === "object" && (parsed.en !== undefined || parsed.zh !== undefined)) {
      return parsed[LANG] || parsed.en || parsed.zh || "";
    }
  } catch (e) {}
  return value;
}

// ---- 编辑（草稿/已发布通用） ----
function openEditModal(id) {
  const entry = entryCache[id];
  if (!entry) return;
  document.getElementById("edit-id").value = id;
  // Editing shows (and saves back) only the current language, a bilingual
  // entry that gets edited this way becomes single-language going forward,
  // that's an acceptable tradeoff rather than building a dual-language editor.
  document.getElementById("edit-title").value = localizedField(entry.title) || "";
  document.getElementById("edit-content").value = localizedField(entry.content) || "";
  document.getElementById("edit-modal").classList.add("show");
}
function closeEditModal() { document.getElementById("edit-modal").classList.remove("show"); }

async function submitEdit() {
  const id = document.getElementById("edit-id").value;
  const title = document.getElementById("edit-title").value.trim();
  const content = document.getElementById("edit-content").value.trim();
  if (!content) { alert(t("alert_content_required")); return; }
  try {
    await api(`/api/entries/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, title }),
    });
    closeEditModal();
    showToast(t("toast_saved_edit"), "✏️");
    if (typeof onEntryChanged === "function") onEntryChanged();
  } catch (e) {
    alert(t("alert_save_failed") + e.message);
  }
}

// ---- 删除（发布后条目走永久私有，不做硬删除） ----
async function deleteEntry(id) {
  if (!confirm(t("confirm_delete"))) return;
  try {
    await api(`/api/entries/${id}/privatize`, { method: "POST" });
    showToast(t("toast_deleted"), "🗑");
    if (typeof onEntryChanged === "function") onEntryChanged();
  } catch (e) {
    alert(t("alert_delete_failed") + e.message);
  }
}
