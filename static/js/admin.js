/* ========================================================================
   admin.js —— 管理后台
   登录 / 统计概览 / 关于我 / 兴趣爱好 / 电影 / 作品 / 分类 / 评论 / 改口令
   资源类模块由 RESOURCES 配置驱动，表格与表单自动生成
   ===================================================================== */

const state = {
  loggedIn: false,
  categories: [],
  stats: null,
  active: "overview",
  commentFilter: "all",
};

/* --------------------------- 资源定义 --------------------------- */

const CATEGORY_KINDS = [
  { value: "movie_genre", label: "电影类型" },
  { value: "work_type", label: "作品类型" },
  { value: "interest", label: "兴趣爱好" },
  { value: "skill", label: "技能标签" },
];

// 「页面区块」能管到的四个页面
const PAGE_OPTIONS = [
  { value: "index", label: "首页" },
  { value: "resume", label: "简历页" },
  { value: "movies", label: "电影页" },
  { value: "works", label: "音乐页" },
];

const RESOURCES = {
  interests: {
    title: "兴趣爱好",
    desc: "首页「我喜欢的东西」区块的卡片。改完前台立刻生效。",
    icon: "✨",
    endpoint: "/api/admin/interests",
    newLabel: "新增兴趣",
    fields: [
      { key: "title", label: "标题", type: "text", required: true },
      { key: "icon", label: "图标（emoji）", type: "text", default: "✨" },
      { key: "description", label: "描述", type: "textarea" },
      { key: "link", label: "跳转链接", type: "text", placeholder: "movies.html" },
      { key: "accent", label: "主题色", type: "color", default: "#a78bfa" },
      { key: "sort_order", label: "排序（越小越靠前）", type: "number", default: 0 },
    ],
    columns: [
      { key: "icon", label: "", width: "48px" },
      { key: "title", label: "标题" },
      { key: "description", label: "描述", clip: true },
      { key: "link", label: "链接", clip: true },
      { key: "sort_order", label: "排序" },
    ],
  },

  movies: {
    title: "恐怖电影",
    desc: "评分、长评、恐怖强度都在这里维护。删掉一部电影会连带删掉它下面的评论。",
    icon: "🎬",
    endpoint: "/api/admin/movies",
    newLabel: "新增电影",
    extra: [{ label: "从 TMDB 导入", action: "tmdb-import" }],
    fields: [
      { key: "title", label: "片名", type: "text", required: true },
      { key: "original_title", label: "原名", type: "text" },
      { key: "year", label: "年份", type: "number", default: 2000 },
      { key: "director", label: "导演", type: "text" },
      { key: "country", label: "国家 / 地区", type: "text" },
      { key: "poster", label: "海报（手填，可留空）", type: "image", full: true,
        hint: "从 TMDB 导入的片子不需要填这里，海报会走 TMDB 的 CDN。" },
      { key: "poster_path", label: "TMDB 海报路径", type: "text", full: true,
        hint: "形如 /abc123.jpg。改它等于换海报，一般不动。" },
      { key: "overview", label: "TMDB 简介", type: "textarea", full: true, rows: 5,
        hint: "官方剧情简介。你自己的看法写在下面的短评和长评里，两回事。" },
      { key: "rating", label: "我的评分（0-10）", type: "number", step: "0.1", default: 7 },
      { key: "scare_level", label: "恐怖强度（0-5）", type: "number", default: 3 },
      { key: "recommend_level", label: "推荐指数（0-5）", type: "number", default: 3 },
      { key: "category_id", label: "分类", type: "category", kind: "movie_genre" },
      { key: "tags", label: "标签（逗号分隔）", type: "tags", full: true },
      { key: "watched_at", label: "观看日期", type: "text", placeholder: "2024-03-18" },
      { key: "sort_order", label: "排序", type: "number", default: 0 },
      { key: "verdict", label: "一句话短评", type: "textarea", full: true },
      { key: "review", label: "长评正文", type: "textarea", full: true, rows: 9 },
    ],
    columns: [
      { key: "title", label: "片名" },
      { key: "year", label: "年份" },
      { key: "rating", label: "评分" },
      { key: "category", label: "分类", render: (r) => (r.category ? r.category.name : "未分类") },
      {
        key: "tmdb_id",
        label: "海报来源",
        render: (r) => (r.tmdb_id ? "TMDB CDN" : r.poster ? "本地 / 外链" : "无"),
      },
      { key: "verdict", label: "短评", clip: true },
    ],
  },

  works: {
    title: "作品",
    desc: "目前主要是音乐构思。状态分：构思中 / 有小样 / 已完成。",
    icon: "🎧",
    endpoint: "/api/admin/works",
    newLabel: "新增作品",
    fields: [
      { key: "title", label: "标题", type: "text", required: true },
      {
        key: "status",
        label: "状态",
        type: "select",
        default: "idea",
        options: [
          { value: "idea", label: "构思中" },
          { value: "demo", label: "有小样" },
          { value: "released", label: "已完成" },
        ],
      },
      { key: "kind", label: "类型标识", type: "text", default: "music" },
      { key: "category_id", label: "分类", type: "category", kind: "work_type" },
      { key: "cover", label: "封面", type: "image", full: true },
      {
        key: "audio_url",
        label: "音频（小样 / 成品）",
        type: "audio",
        full: true,
        note: "上传后就能在前台直接播放；勾了「允许下载」访客才能存到本地。",
      },
      { key: "allow_download", label: "允许下载", type: "bool", hint: "允许访客下载这首曲子" },
      { key: "audio_duration", label: "时长（秒）", type: "number", default: 0 },
      { key: "audio_size", label: "体积（字节）", type: "number", default: 0 },
      { key: "bpm", label: "BPM", type: "number", default: 0 },
      { key: "key_signature", label: "调性", type: "text", placeholder: "Am" },
      { key: "progress", label: "完成度（0-100）", type: "number", default: 0 },
      { key: "sort_order", label: "排序", type: "number", default: 0 },
      { key: "tags", label: "标签（逗号分隔）", type: "tags", full: true },
      { key: "style_suggest", label: "风格标签", type: "style-suggest", full: true },
      { key: "summary", label: "一句话简介", type: "textarea", full: true },
      { key: "notes", label: "创作笔记", type: "textarea", full: true, rows: 8 },
    ],
    columns: [
      { key: "title", label: "标题" },
      {
        key: "status",
        label: "状态",
        render: (r) => ({ idea: "构思中", demo: "有小样", released: "已完成" }[r.status] || r.status),
      },
      { key: "bpm", label: "BPM" },
      { key: "progress", label: "完成度", render: (r) => `${r.progress}%` },
      {
        key: "audio_url",
        label: "音频",
        render: (r) => (r.audio_url ? (r.allow_download ? "可播放 / 可下载" : "仅播放") : "无"),
      },
      { key: "summary", label: "简介", clip: true },
    ],
  },

  journey: {
    title: "成长路径",
    desc: "简历页的主角：我是怎么一步步走到这儿的。每一步只写三件事——当时卡在哪、我怎么走的、走出来之后得到了什么。履历在下面做佐证，不是主角。",
    icon: "🧭",
    endpoint: "/api/admin/journey",
    newLabel: "新增一步",
    fields: [
      {
        key: "stage",
        label: "阶段",
        type: "select",
        default: "turn",
        options: [
          { value: "start", label: "起点" },
          { value: "turn", label: "转折点" },
          { value: "now", label: "现在" },
          { value: "next", label: "下一步" },
        ],
      },
      { key: "title", label: "这一步的标题", type: "text", required: true },
      { key: "when", label: "时间（自由写）", type: "text", placeholder: "2023 年春天" },
      {
        key: "stuck",
        label: "当时卡在哪",
        type: "textarea",
        full: true,
        rows: 4,
        hint: "写具体。写「遇到困难」不如写「本地跑得好好的，一给别人演示端口就变」。",
      },
      { key: "action", label: "我怎么走的", type: "textarea", full: true, rows: 4 },
      { key: "gained", label: "走出来之后得到了什么", type: "textarea", full: true, rows: 4 },
      { key: "evidence", label: "佐证（一句话）", type: "text", full: true },
      { key: "link", label: "佐证链接", type: "text", full: true },
      { key: "sort_order", label: "排序", type: "number", default: 0 },
    ],
    columns: [
      { key: "title", label: "这一步" },
      {
        key: "stage",
        label: "阶段",
        render: (r) =>
          ({ start: "起点", turn: "转折点", now: "现在", next: "下一步" }[r.stage] || r.stage),
      },
      { key: "when", label: "时间" },
      { key: "stuck", label: "卡在哪", clip: true },
    ],
  },

  resume: {
    title: "简历经历",
    desc: "时间轴上的每一条：工作、教育、项目、获奖。勾选「进行中」会显示成至今。",
    icon: "📄",
    endpoint: "/api/admin/resume",
    newLabel: "新增经历",
    fields: [
      {
        key: "kind",
        label: "类型",
        type: "select",
        default: "work",
        options: [
          { value: "work", label: "工作" },
          { value: "education", label: "教育" },
          { value: "project", label: "项目" },
          { value: "award", label: "获奖" },
        ],
      },
      { key: "title", label: "标题 / 职位", type: "text", required: true },
      { key: "org", label: "公司 / 学校", type: "text" },
      { key: "role", label: "英文职位（可选）", type: "text" },
      { key: "location", label: "地点", type: "text" },
      { key: "start_date", label: "开始时间", type: "text", placeholder: "2023.06" },
      { key: "end_date", label: "结束时间", type: "text", placeholder: "2025.03" },
      { key: "current", label: "状态", type: "bool", hint: "进行中（显示「至今」）" },
      { key: "sort_order", label: "排序", type: "number", default: 0 },
      { key: "link", label: "相关链接", type: "text", full: true },
      { key: "tags", label: "标签（逗号分隔）", type: "tags", full: true },
      { key: "summary", label: "一句话概述", type: "textarea", full: true },
      {
        key: "highlights",
        label: "要点（一行一条）",
        type: "lines",
        full: true,
        rows: 6,
      },
    ],
    columns: [
      {
        key: "kind",
        label: "类型",
        render: (r) =>
          ({ work: "工作", education: "教育", project: "项目", award: "获奖" }[r.kind] || r.kind),
      },
      { key: "title", label: "标题" },
      { key: "org", label: "单位" },
      {
        key: "date",
        label: "时间",
        render: (r) => `${r.start_date || ""} — ${r.current ? "至今" : r.end_date || ""}`,
      },
      { key: "summary", label: "概述", clip: true },
    ],
  },

  skills: {
    title: "技能",
    desc: "熟练度同时决定 3D 技能球里的字号与亮度。",
    icon: "🧩",
    endpoint: "/api/admin/skills",
    newLabel: "新增技能",
    fields: [
      { key: "name", label: "名称", type: "text", required: true },
      { key: "level", label: "熟练度（0-100）", type: "number", default: 60 },
      { key: "group", label: "分组", type: "text", default: "其他" },
      { key: "color", label: "颜色", type: "color", default: "#00b8d4" },
      { key: "sort_order", label: "排序", type: "number", default: 0 },
      { key: "note", label: "备注", type: "text", full: true },
    ],
    columns: [
      { key: "name", label: "名称" },
      { key: "group", label: "分组" },
      {
        key: "level",
        label: "熟练度",
        render: (r) => {
          const meter = el("div", {
            class: "meter",
            style: { width: "90px", marginTop: "4px" },
          });
          meter.style.setProperty("--skill-color", r.color || "#00b8d4");
          const fill = el("div", { class: "skill-row__fill", style: { width: `${r.level}%` } });
          meter.appendChild(fill);
          const box = el("div", {}, [
            el("span", { class: "mono", text: String(r.level) }),
            meter,
          ]);
          return box;
        },
      },
      { key: "note", label: "备注", clip: true },
    ],
  },

  categories: {
    title: "分类管理",
    desc: "所有「细小分类」都在这里：电影类型、作品类型、兴趣爱好、技能标签。",
    icon: "🏷️",
    endpoint: "/api/admin/categories",
    newLabel: "新增分类",
    fields: [
      { key: "kind", label: "归属", type: "select", options: CATEGORY_KINDS, default: "movie_genre" },
      { key: "name", label: "名称", type: "text", required: true },
      { key: "slug", label: "别名（留空同名称）", type: "text" },
      { key: "color", label: "颜色", type: "color", default: "#38bdf8" },
      { key: "sort_order", label: "排序", type: "number", default: 0 },
      { key: "description", label: "说明", type: "textarea", full: true },
    ],
    columns: [
      {
        key: "kind",
        label: "归属",
        render: (r) => (CATEGORY_KINDS.find((k) => k.value === r.kind) || {}).label || r.kind,
      },
      { key: "name", label: "名称" },
      {
        key: "color",
        label: "颜色",
        render: (r) => {
          const dot = el("span", {
            class: "chip chip--dot",
            text: r.color,
            style: { "--chip-color": r.color },
          });
          return dot;
        },
      },
      { key: "description", label: "说明", clip: true },
      { key: "sort_order", label: "排序" },
    ],
  },

  sections: {
    title: "页面区块",
    desc: "前台每一页由若干区块拼起来。这里可以隐藏、删除、改顺序——改完刷新前台立刻生效。删错了用右上角的「恢复默认区块」找回来。",
    icon: "🧱",
    endpoint: "/api/admin/page-sections",
    newLabel: "新增区块",
    filter: { key: "page", options: PAGE_OPTIONS, allLabel: "全部页面" },
    extra: [{ label: "恢复默认区块", action: "reset-sections" }],
    fields: [
      { key: "page", label: "所属页面", type: "select", options: PAGE_OPTIONS, default: "index" },
      {
        key: "key",
        label: "区块标识",
        type: "text",
        required: true,
        hint: "前台认的英文标识，例如 about / grid。改了等于换了一个区块，一般不动它。",
      },
      { key: "title", label: "显示名", type: "text", hint: "只在这个列表里显示，不影响前台。" },
      { key: "visible", label: "显示", type: "bool", hint: "取消勾选 = 前台不再渲染这一块（配置还留着）" },
      { key: "sort_order", label: "排序（越小越靠前）", type: "number", default: 0 },
    ],
    columns: [
      {
        key: "page",
        label: "页面",
        render: (r) => (PAGE_OPTIONS.find((p) => p.value === r.page) || {}).label || r.page,
      },
      { key: "title", label: "区块" },
      { key: "key", label: "标识", render: (r) => el("code", { class: "mono", text: r.key }) },
      {
        key: "visible",
        label: "状态",
        render: (r) =>
          el("span", {
            class: r.visible ? "chip chip--ok" : "chip tag-pill--muted",
            text: r.visible ? "显示中" : "已隐藏",
          }),
      },
      { key: "sort_order", label: "排序" },
    ],
    rowActions: [
      {
        // 常用的开关，省得每次都开编辑弹层
        labelFor: (r) => (r.visible ? "隐藏" : "显示"),
        run: async (r, refresh) => {
          try {
            await API.put(`/api/admin/page-sections/${r.id}`, { visible: !r.visible });
            toast(r.visible ? "已隐藏" : "已显示");
            refresh();
          } catch (err) {
            toast(err.message, "err");
          }
        },
      },
    ],
  },
};

/* --------------------------- 全局错误兜底 --------------------------- */

/* 以前这里最大的坑：showAdmin 是 async 且没有兜底，一旦渲染抛错，
   登录框会静默弹回来，用户看到的正是「登录成功但后台完全用不了」。
   现在任何异常都会显式显示在页面顶部的红色错误条上。 */

const DIAG = {
  errors: [],
  push(msg) {
    DIAG.errors.push(String(msg));
  },
  text() {
    return [
      "Ballball 后台诊断信息",
      `时间: ${new Date().toISOString()}`,
      `地址: ${location.href}`,
      `UA: ${navigator.userAgent}`,
      `登录态: ${state.loggedIn}`,
      `当前面板: ${state.active}`,
      "",
      "错误记录:",
      ...(DIAG.errors.length
        ? DIAG.errors.map((e, i) => `  ${i + 1}. ${e}`)
        : ["  （无）"]),
    ].join("\n");
  },
};

function showFatal(msg) {
  DIAG.push(msg);
  const bar = document.getElementById("fatal-bar");
  if (!bar) return;
  document.getElementById("fatal-msg").textContent = msg;
  bar.hidden = false;
}

window.addEventListener("error", (e) => {
  showFatal(`脚本错误：${e.message}（${e.filename}:${e.lineno}）`);
});

window.addEventListener("unhandledrejection", (e) => {
  const r = e.reason;
  showFatal(`未处理的异步错误：${(r && r.message) || r}`);
});

/* --------------------------- 登录 / 会话 --------------------------- */

async function checkSession() {
  try {
    await API.get("/api/admin/session");
    state.loggedIn = true;
    await showAdmin();
  } catch (err) {
    state.loggedIn = false;
    document.getElementById("login-view").hidden = false;
    document.getElementById("admin-view").hidden = true;
    // 401 只是没登录，属正常；其余都要显式暴露，否则用户只会看到「没反应」
    if (!err || err.status !== 401) {
      showFatal(
        `无法进入后台：${(err && err.message) || err}` +
          (err && err.status ? `（HTTP ${err.status}）` : "（接口无响应，服务可能没启动）")
      );
    }
  }
}

async function showAdmin() {
  // 先渲染、后切视图：渲染失败就留在登录页并把错误说清楚，
  // 绝不留下「登录框消失了但后台是空白」这种死状态。
  try {
    await Promise.all([loadCategories(), loadStats()]);
    renderSide();
    await renderPane(state.active);
  } catch (err) {
    showFatal(`后台渲染失败：${(err && err.message) || err}`);
    throw err;
  }
  document.getElementById("login-view").hidden = true;
  document.getElementById("admin-view").hidden = false;
}

async function loadCategories() {
  try {
    state.categories = await API.get("/api/admin/categories");
  } catch (_) {
    state.categories = [];
  }
}

async function loadStats() {
  try {
    state.stats = await API.get("/api/admin/stats");
  } catch (_) {
    state.stats = null;
  }
}

/* --------------------------- 侧边导航 --------------------------- */

const TABS = [
  { key: "overview", icon: "📊", label: "概览" },
  { key: "profile", icon: "🙋", label: "关于我" },
  { key: "journey", icon: "🧭", label: "成长路径" },
  { key: "resume", icon: "📄", label: "简历经历" },
  { key: "skills", icon: "🧩", label: "技能" },
  { key: "interests", icon: "✨", label: "兴趣爱好" },
  { key: "movies", icon: "🎬", label: "电影" },
  { key: "works", icon: "🎧", label: "作品" },
  { key: "categories", icon: "🏷️", label: "分类" },
  { key: "sections", icon: "🧱", label: "页面区块" },
  { key: "comments", icon: "💬", label: "评论" },
  { key: "password", icon: "🔒", label: "改口令" },
];

function renderSide() {
  const nav = document.getElementById("side-nav");
  nav.textContent = "";
  TABS.forEach((t) => {
    const btn = el("button", { class: "side__btn", type: "button" }, [
      el("i", { text: t.icon }),
      el("span", { text: t.label }),
    ]);
    if (t.key === state.active) btn.classList.add("is-active");
    if (state.stats) {
      const map = {
        movies: state.stats.movies,
        works: state.stats.works,
        categories: state.stats.categories,
        interests: state.stats.interests,
        comments: state.stats.comments,
        resume: state.stats.resume_items,
        skills: state.stats.skills,
      };
      if (t.key === "comments" && state.stats.pending_comments) {
        // 有待审的先把「待审」顶上来，比总数更该被看见
        btn.appendChild(
          el("span", {
            class: "side__badge side__badge--warn",
            text: `${state.stats.pending_comments} 待审`,
          })
        );
      } else if (map[t.key] !== undefined) {
        btn.appendChild(el("span", { class: "side__badge", text: String(map[t.key]) }));
      }
    }
    btn.addEventListener("click", () => {
      state.active = t.key;
      renderSide();
      renderPane(t.key);
    });
    nav.appendChild(btn);
  });
}

/* --------------------------- 弹层表单 --------------------------- */

function openModal(title, bodyNode) {
  const modal = document.getElementById("admin-modal");
  const panel = document.getElementById("admin-modal-panel");
  panel.textContent = "";
  panel.appendChild(el("h3", { style: { marginBottom: "18px" }, text: title }));
  panel.appendChild(bodyNode);
  const close = el(
    "button",
    { class: "btn btn--icon modal__close", type: "button", "aria-label": "关闭", text: "✕" },
    []
  );
  close.addEventListener("click", closeModal);
  panel.appendChild(close);
  if (!modal.open) modal.showModal();
}

function closeModal() {
  const modal = document.getElementById("admin-modal");
  if (modal && modal.open) modal.close();
}

// 关闭时清空内容（Esc / 点遮罩都走这里）
document.getElementById("admin-modal").addEventListener("close", () => {
  const panel = document.getElementById("admin-modal-panel");
  if (panel) panel.textContent = "";
});

// 点遮罩关闭：dialog 的 ::backdrop 点击 target 就是 dialog 本身
document.getElementById("admin-modal").addEventListener("click", (e) => {
  if (e.target === e.currentTarget) closeModal();
});

/* --------------------------- 表单构建 --------------------------- */

function buildField(field, record) {
  const value = record ? record[field.key] : undefined;
  const wrap = el("div", { class: "field" + (field.full ? " field--full" : "") });
  wrap.appendChild(el("label", { class: "field__label", text: field.label + (field.required ? " *" : "") }));

  let input;
  if (field.type === "textarea") {
    input = el("textarea", { class: "textarea" });
    if (field.rows) input.rows = field.rows;
    input.value = value ?? "";
  } else if (field.type === "select") {
    input = el("select", { class: "select" });
    field.options.forEach((o) => {
      const opt = el("option", { value: o.value, text: o.label });
      if ((value ?? field.default) === o.value) opt.selected = true;
      input.appendChild(opt);
    });
  } else if (field.type === "category") {
    input = el("select", { class: "select" });
    input.appendChild(el("option", { value: "", text: "未分类" }));
    state.categories
      .filter((c) => c.kind === field.kind)
      .forEach((c) => {
        const opt = el("option", { value: String(c.id), text: c.name });
        if (String(value ?? "") === String(c.id)) opt.selected = true;
        input.appendChild(opt);
      });
  } else if (field.type === "color") {
    input = el("input", { class: "input", type: "color" });
    input.value = value || field.default || "#00b8d4";
  } else if (field.type === "bool") {
    // 开关单独一行：checkbox 必须包在 label 里，这里提前返回
    const cb = el("input", { type: "checkbox" });
    cb.checked = !!value;
    cb.dataset.key = field.key;
    cb.dataset.type = field.type;
    wrap.appendChild(
      el("label", { class: "switch-line" }, [
        cb,
        document.createTextNode(field.hint || "是"),
      ])
    );
    return wrap;
  } else if (field.type === "lines") {
    // 一行一条，用来填简历的要点列表
    input = el("textarea", { class: "textarea" });
    if (field.rows) input.rows = field.rows;
    input.value = Array.isArray(value) ? value.join("\n") : "";
  } else if (field.type === "tags") {
    input = el("input", { class: "input", type: "text", placeholder: "心理惊悚, 高分" });
    input.value = Array.isArray(value) ? value.join(", ") : "";
  } else if (field.type === "number") {
    input = el("input", { class: "input", type: "number" });
    if (field.step) input.step = field.step;
    input.value = value ?? field.default ?? 0;
  } else if (field.type === "image") {
    input = el("input", {
      class: "input",
      type: "text",
      placeholder: field.placeholder || "图片 URL，或直接上传",
    });
    input.value = value ?? field.default ?? "";
  } else if (field.type === "audio") {
    input = el("input", {
      class: "input",
      type: "text",
      placeholder: field.placeholder || "音频 URL，或直接上传",
    });
    input.value = value ?? field.default ?? "";
  } else if (field.type === "style-suggest") {
    // 风格标签推断：按关键词 / BPM / 调性给候选，点一下写进上面的标签框
    const box = el("div", { class: "style-suggest" });
    const btn = el("button", { class: "btn btn--sm", type: "button", text: "推断风格标签" });
    const chips = el("div", { class: "chips style-suggest__chips" });
    const note = el("p", {
      class: "field__hint",
      text: "从标题 / 简介 / 创作笔记 / BPM / 调性里找线索。点一下就加进上面的标签，再点一下取消。",
    });
    box.appendChild(el("div", { class: "style-suggest__row" }, [btn]));
    box.appendChild(chips);
    box.appendChild(note);

    const readTags = () => {
      const form = btn.closest("form");
      const input = form && form.querySelector('[data-key="tags"]');
      if (!input) return { input: null, list: [] };
      return {
        input,
        list: input.value.split(/[,，]/).map((s) => s.trim()).filter(Boolean),
      };
    };
    const writeTags = (input, list) => {
      input.value = list.join(", ");
    };

    const paintChips = (styles, adopted) => {
      chips.textContent = "";
      if (!styles.length) {
        chips.appendChild(
          el("span", { class: "field__hint", text: "没找到明显线索——手动填，或者把风格写进创作笔记再试一次。" })
        );
        return;
      }
      styles.forEach((tag) => {
        const on = adopted.includes(tag);
        const chip = el("button", {
          class: "chip chip--pick" + (on ? " chip--ok" : ""),
          type: "button",
          text: (on ? "✓ " : "+ ") + tag,
          "aria-pressed": on ? "true" : "false",
        });
        chip.addEventListener("click", () => {
          const { input, list } = readTags();
          if (!input) return;
          const next = list.includes(tag) ? list.filter((t) => t !== tag) : [...list, tag];
          writeTags(input, next);
          paintChips(styles, next);
        });
        chips.appendChild(chip);
      });
    };

    btn.addEventListener("click", async () => {
      const form = btn.closest("form");
      if (!form) return;
      const val = (k) => {
        const i = form.querySelector(`[data-key="${k}"]`);
        return i ? i.value : "";
      };
      const { list } = readTags();
      btn.disabled = true;
      btn.textContent = "推断中…";
      try {
        const out = await API.post("/api/admin/works/suggest-tags", {
          title: val("title"),
          summary: val("summary"),
          notes: val("notes"),
          bpm: Number(val("bpm") || 0),
          key_signature: val("key_signature"),
          progress: Number(val("progress") || 0),
          tags: list,
        });
        paintChips(out.styles || [], list);
      } catch (err) {
        toast(err.message, "err");
      } finally {
        btn.disabled = false;
        btn.textContent = "推断风格标签";
      }
    });

    wrap.appendChild(box);
    return wrap;
  } else {
    input = el("input", { class: "input", type: "text", placeholder: field.placeholder || "" });
    input.value = value ?? field.default ?? "";
  }

  if (field.required) input.required = true;
  input.dataset.key = field.key;
  input.dataset.type = field.type;
  wrap.appendChild(input);

  if (field.type === "image") attachImageUpload(wrap, input);
  if (field.type === "audio") attachAudioUpload(wrap, input, field);
  if (field.hint) {
    wrap.appendChild(el("p", { class: "field__hint", text: field.hint }));
  }
  return wrap;
}

/* 音频字段：上传 + 试听 + 自动读时长。
   时长在浏览器里读，不装 mutagen 之类的服务端依赖也能拿到。 */
function attachAudioUpload(wrap, input, field) {
  wrap.classList.add("field--audio");
  const picker = el("input", { type: "file", accept: "audio/*,.mp3,.wav,.ogg,.m4a,.flac" });
  picker.hidden = true;
  const btn = el("button", { class: "btn btn--sm", type: "button", text: "上传音频" });
  const meta = el("span", { class: "field__meta", text: "" });
  const player = el("audio", { controls: true, preload: "metadata" });
  player.hidden = !input.value;
  if (input.value) player.src = input.value;

  const paintMeta = () => {
    if (!input.value) {
      meta.textContent = "";
      return;
    }
    const secs = Math.round(player.duration || 0);
    meta.textContent = secs && Number.isFinite(secs)
      ? `时长 ${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")}`
      : "";
  };
  player.addEventListener("loadedmetadata", paintMeta);

  input.addEventListener("input", () => {
    player.src = input.value;
    player.hidden = !input.value;
    paintMeta();
  });

  picker.addEventListener("change", async () => {
    const picked = picker.files && picker.files[0];
    if (!picked) return;
    btn.disabled = true;
    btn.textContent = "上传中…";
    try {
      const fd = new FormData();
      fd.append("file", picked);
      const res = await API.upload("/api/admin/upload-audio", fd);
      input.value = res.url;
      player.src = res.url;
      player.hidden = false;
      toast(`已上传（${Math.max(1, Math.round(res.size / 1024))} KB）`);
      // 时长要在元数据加载完才知道，顺手写进 hidden 的 duration 字段
      player.addEventListener(
        "loadedmetadata",
        () => {
          const secs = Math.round(player.duration || 0);
          const durInput = wrap.parentElement.querySelector('[data-key="audio_duration"]');
          const sizeInput = wrap.parentElement.querySelector('[data-key="audio_size"]');
          if (durInput && Number.isFinite(secs)) durInput.value = String(secs);
          if (sizeInput) sizeInput.value = String(res.size || 0);
          paintMeta();
        },
        { once: true }
      );
    } catch (err) {
      toast(err.message, "err");
    } finally {
      btn.disabled = false;
      btn.textContent = "上传音频";
      picker.value = "";
    }
  });

  wrap.appendChild(el("div", { class: "field__row" }, [btn, meta, picker]));
  wrap.appendChild(player);
  if (field.note) {
    wrap.appendChild(el("p", { class: "field__hint", text: field.note }));
  }
}

/* ------------------- 从 TMDB 导入电影 ------------------- */

function openResetSections(onDone) {
  const box = el("div", {}, [
    el("p", {
      class: "field__hint",
      text: "选择一页，把它的区块恢复成出厂状态：隐藏的重新显示、删掉的加回来、顺序重排。这一页上你做的自定义会全部丢掉。",
    }),
  ]);
  const sel = el(
    "select",
    { class: "select", style: { marginTop: "12px", marginBottom: "16px" } },
    PAGE_OPTIONS.map((o) => el("option", { value: o.value, text: o.label }))
  );
  box.appendChild(sel);

  const goBtn = el("button", { class: "btn btn--primary btn--sm", type: "button", text: "恢复这一页" });
  box.appendChild(goBtn);

  goBtn.addEventListener("click", async () => {
    const label = (PAGE_OPTIONS.find((o) => o.value === sel.value) || {}).label || sel.value;
    if (!confirm(`确定把「${label}」的区块恢复成默认？这一页的自定义配置会被清掉。`)) return;
    goBtn.disabled = true;
    try {
      await API.post("/api/admin/page-sections/reset", { page: sel.value });
      toast("已恢复默认区块");
      closeModal();
      if (onDone) onDone();
    } catch (err) {
      toast(err.message, "err");
    } finally {
      goBtn.disabled = false;
    }
  });

  openModal("恢复默认区块", box);
}

async function openTmdbImport(onImported) {
  const box = el("div", { class: "tmdb" });

  const qInput = el("input", {
    class: "input",
    type: "text",
    placeholder: "片名，例如：闪灵 / The Shining",
  });
  const searchBtn = el("button", { class: "btn btn--primary btn--sm", type: "button", text: "搜索" });
  const browseBtn = el("button", { class: "btn btn--sm", type: "button", text: "浏览恐怖片库" });
  const pagePrev = el("button", { class: "btn btn--sm", type: "button", text: "上一页" });
  const pageNext = el("button", { class: "btn btn--sm", type: "button", text: "下一页" });
  const pageInfo = el("span", { class: "field__meta", text: "" });
  const status = el("p", { class: "field__hint", text: "" });
  const list = el("div", { class: "tmdb__list" });

  let mode = "search";
  let page = 1;
  let totalPages = 1;

  const form = el("div", { class: "field__row" }, [qInput, searchBtn, browseBtn]);
  box.appendChild(form);
  box.appendChild(el("div", { class: "field__row" }, [pagePrev, pageInfo, pageNext]));
  box.appendChild(status);
  box.appendChild(
    el("p", {
      class: "field__hint",
      text: "海报与简介来自 TMDB，只存地址不存图片，本地磁盘不占空间。",
    })
  );
  box.appendChild(list);

  async function run(nextPage = 1) {
    page = nextPage;
    list.textContent = "";
    status.textContent = "加载中…";
    let data;
    try {
      data =
        mode === "search"
          ? await API.get(`/api/admin/tmdb/search?q=${encodeURIComponent(qInput.value)}&page=${page}`)
          : await API.get(`/api/admin/tmdb/discover?page=${page}`);
    } catch (err) {
      status.textContent = `请求失败：${err.message}`;
      return;
    }
    if (!data.configured) {
      status.textContent =
        "还没配置 TMDB_API_KEY：去 themoviedb.org 注册 → 设置 → API 申请一个免费 key，写进 .env 的 TMDB_API_KEY 后重启服务即可。";
      return;
    }
    status.textContent = data.results.length
      ? `共 ${data.total_results} 条，第 ${data.page}/${data.total_pages} 页`
      : "没有匹配的条目，换个关键词试试。";
    totalPages = data.total_pages || 1;
    pageInfo.textContent = `${data.page} / ${totalPages}`;

    data.results.forEach((item) => {
      const card = el("div", { class: "tmdb__card" });
      const img = el("img", { class: "tmdb__poster", alt: item.title || "海报" });
      if (item.poster_url) {
        img.src = item.poster_url;
      } else {
        img.hidden = true;
      }
      const info = el("div", { class: "tmdb__info" }, [
        el("div", {
          class: "tmdb__title",
          text: `${item.title}${item.year ? `（${item.year}）` : ""}`,
        }),
        el("div", {
          class: "field__meta",
          text: [item.original_title, item.tmdb_rating ? `TMDB ${item.tmdb_rating}` : ""]
            .filter(Boolean)
            .join(" · "),
        }),
        el("p", { class: "tmdb__overview", text: (item.overview || "").slice(0, 160) }),
      ]);
      const pick = el("button", { class: "btn btn--sm btn--primary", type: "button", text: "导入" });
      pick.addEventListener("click", async () => {
        pick.disabled = true;
        pick.textContent = "导入中…";
        try {
          const created = await API.post("/api/admin/movies/from-tmdb", {
            tmdb_id: item.tmdb_id,
          });
          toast(`已导入《${created.title}》`);
          closeModal();
          if (onImported) onImported();
        } catch (err) {
          toast(err.message, "err");
          pick.disabled = false;
          pick.textContent = "导入";
        }
      });
      card.appendChild(img);
      card.appendChild(info);
      card.appendChild(el("div", { class: "tmdb__actions" }, [pick]));
      list.appendChild(card);
    });
  }

  searchBtn.addEventListener("click", () => {
    mode = "search";
    if (!qInput.value.trim()) {
      status.textContent = "先输入片名。";
      return;
    }
    run(1);
  });
  qInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      searchBtn.click();
    }
  });
  browseBtn.addEventListener("click", () => {
    mode = "discover";
    run(1);
  });
  pagePrev.addEventListener("click", () => run(Math.max(1, page - 1)));
  pageNext.addEventListener("click", () => run(Math.min(totalPages, page + 1)));

  openModal("从 TMDB 导入电影", box);
  // 打开就先给一页恐怖片库，比空着让人猜更好用
  mode = "discover";
  run(1);
}

/* 图片字段的上传条：URL 输入框 + 本地文件 + 缩略图，两个表单都用它 */

function attachImageUpload(wrap, input) {
  wrap.classList.add("field--image");
  const picker = el("input", { type: "file", accept: "image/*" });
  picker.hidden = true;
  const btn = el("button", { class: "btn btn--sm", type: "button", text: "上传图片" });
  const preview = el("img", { class: "field__thumb", alt: "预览" });
  preview.hidden = !input.value;
  if (input.value) preview.src = input.value;

  btn.addEventListener("click", () => picker.click());
  input.addEventListener("input", () => {
    preview.src = input.value;
    preview.hidden = !input.value;
  });
  picker.addEventListener("change", async () => {
    const picked = picker.files && picker.files[0];
    if (!picked) return;
    btn.disabled = true;
    btn.textContent = "上传中…";
    try {
      const fd = new FormData();
      fd.append("file", picked);
      const res = await API.upload("/api/admin/upload", fd);
      input.value = res.url;
      preview.src = res.url;
      preview.hidden = false;
      toast(`已上传（${Math.max(1, Math.round(res.size / 1024))} KB）`);
    } catch (err) {
      toast(err.message, "err");
    } finally {
      btn.disabled = false;
      btn.textContent = "上传图片";
      picker.value = "";
    }
  });

  wrap.appendChild(el("div", { class: "field__row" }, [btn, preview, picker]));
}

function collectForm(formEl, fields) {
  const payload = {};
  fields.forEach((f) => {
    const input = formEl.querySelector(`[data-key="${f.key}"]`);
    if (!input) return;
    let v = input.value;
    if (f.type === "number") {
      v = v === "" ? undefined : Number(v);
      if (Number.isNaN(v)) v = undefined;
    } else if (f.type === "category") {
      v = v === "" ? null : Number(v);
    } else if (f.type === "bool") {
      v = !!input.checked;
    } else if (f.type === "lines") {
      v = v
        .split("\n")
        .map((s) => s.trim())
        .filter(Boolean);
    } else if (f.type === "tags") {
      v = v
        .split(/[,，]/)
        .map((s) => s.trim())
        .filter(Boolean);
    } else if (f.type === "select" && f.key === "kind") {
      v = v;
    }
    payload[f.key] = v;
  });
  return payload;
}

/* --------------------------- 资源模块 --------------------------- */

async function renderResource(key) {
  const cfg = RESOURCES[key];
  const pane = document.getElementById("pane");
  pane.textContent = "";

  const actions = el("div", { class: "pane__actions" }, [
    el("button", { class: "btn btn--primary btn--sm", type: "button", text: `+ ${cfg.newLabel}` }),
  ]);
  const head = el("div", { class: "pane__head" }, [
    el("div", {}, [
      el("div", { class: "pane__title", text: cfg.title }),
      el("div", { class: "pane__desc", text: cfg.desc }),
    ]),
    actions,
  ]);
  actions.firstChild.addEventListener("click", () => openResourceForm(key, null));

  // 资源自带的额外动作（电影的「从 TMDB 导入」、区块的「恢复默认」）
  (cfg.extra || []).forEach((act) => {
    const btn = el("button", { class: "btn btn--sm", type: "button", text: act.label });
    btn.addEventListener("click", () => {
      if (act.action === "tmdb-import") {
        openTmdbImport(() => renderPane(key));
      } else if (act.action === "reset-sections") {
        openResetSections(() => renderPane(key));
      }
    });
    actions.appendChild(btn);
  });

  // 可选的筛选器（目前只有「页面区块」按页面过滤）
  let filterValue = "all";
  if (cfg.filter) {
    const sel = el("select", { class: "select" }, [
      el("option", { value: "all", text: cfg.filter.allLabel || "全部" }),
      ...cfg.filter.options.map((o) => el("option", { value: o.value, text: o.label })),
    ]);
    sel.addEventListener("change", () => {
      filterValue = sel.value;
      paint();
    });
    actions.appendChild(sel);
  }

  pane.appendChild(head);

  const tableWrap = el("div", { class: "table-wrap" }, [
    el("p", { class: "empty", text: "加载中…" }),
  ]);
  pane.appendChild(tableWrap);

  let rows = [];
  try {
    rows = await API.get(cfg.endpoint);
  } catch (err) {
    tableWrap.textContent = "";
    tableWrap.appendChild(el("p", { class: "empty", text: `加载失败：${err.message}` }));
    return;
  }

  function paint() {
    tableWrap.textContent = "";
    const shown = cfg.filter
      ? rows.filter((r) => filterValue === "all" || String(r[cfg.filter.key]) === filterValue)
      : rows;
    if (!shown.length) {
      tableWrap.appendChild(
        el("p", {
          class: "empty",
          text: rows.length ? "这个筛选下没有数据。" : "还没有数据，点右上角新增第一条。",
        })
      );
      return;
    }
    const table = el("table", { class: "table" });
    const thead = el("thead");
    const tr = el("tr");
    cfg.columns.forEach((c) => tr.appendChild(el("th", { text: c.label })));
    tr.appendChild(el("th", { text: "操作", style: { textAlign: "right" } }));
    thead.appendChild(tr);
    table.appendChild(thead);

    const tbody = el("tbody");
    shown.forEach((r) => {
      const line = el("tr");
      cfg.columns.forEach((c) => {
        const td = el("td", { class: c.clip ? "cell-clip" : "" });
        if (c.render) {
          const out = c.render(r);
          td.appendChild(typeof out === "string" ? document.createTextNode(out) : out);
        } else {
          const v = r[c.key];
          td.textContent = v === null || v === undefined ? "" : String(v);
        }
        line.appendChild(td);
      });

      const actions = el("td", {}, [
        el("div", { class: "table__actions" }, [
          el("button", { class: "btn btn--sm", type: "button", text: "编辑" }),
          el("button", { class: "btn btn--sm btn--rose", type: "button", text: "删除" }),
        ]),
      ]);
      const btnBox = actions.querySelector(".table__actions");
      // 资源自定义的快捷动作（区块的「隐藏 / 显示」）
      (cfg.rowActions || []).forEach((act) => {
        const btn = el("button", {
          class: "btn btn--sm",
          type: "button",
          text: act.labelFor ? act.labelFor(r) : act.label,
        });
        btn.addEventListener("click", () => act.run(r, () => paint()));
        btnBox.appendChild(btn);
      });

      const [editBtn, delBtn] = actions.querySelectorAll("button");
      editBtn.addEventListener("click", () => openResourceForm(key, r, () => paint()));
      delBtn.addEventListener("click", async () => {
        const name = r.title || r.name || `第 ${r.id} 条`;
        if (!confirm(`确定删除「${name}」？此操作不可撤销。`)) return;
        try {
          await API.del(`${cfg.endpoint}/${r.id}`);
          toast("已删除");
          await loadCategories();
          await loadStats();
          renderSide();
          renderResource(key);
        } catch (err) {
          toast(err.message, "err");
        }
      });
      line.appendChild(actions);
      tbody.appendChild(line);
    });
    table.appendChild(tbody);
    tableWrap.appendChild(table);
  }

  paint();
}

function openResourceForm(key, record, onSaved) {
  const cfg = RESOURCES[key];
  const form = el("form", { class: "form-grid" });
  cfg.fields.forEach((f) => form.appendChild(buildField(f, record)));

  const actions = el("div", { class: "form-actions", style: { gridColumn: "1 / -1" } }, [
    el("button", { class: "btn", type: "button", text: "取消" }),
    el("button", { class: "btn btn--primary", type: "submit", text: record ? "保存修改" : "创建" }),
  ]);
  const [cancelBtn, submitBtn] = actions.querySelectorAll("button");
  cancelBtn.addEventListener("click", closeModal);
  form.appendChild(actions);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = collectForm(form, cfg.fields);
    submitBtn.disabled = true;
    const original = submitBtn.textContent;
    submitBtn.textContent = "保存中…";
    try {
      if (record) {
        await API.put(`${cfg.endpoint}/${record.id}`, payload);
        toast("已保存");
      } else {
        await API.post(cfg.endpoint, payload);
        toast("已创建");
      }
      closeModal();
      await loadCategories();
      await loadStats();
      renderSide();
      if (onSaved) onSaved();
      else renderResource(key);
    } catch (err) {
      toast(err.message, "err");
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = original;
    }
  });

  openModal(record ? `编辑 · ${record.title || record.name || record.id}` : cfg.newLabel, form);
}

/* --------------------------- 概览 --------------------------- */

function renderOverview() {
  const pane = document.getElementById("pane");
  pane.textContent = "";
  pane.appendChild(
    el("div", { class: "pane__head" }, [
      el("div", {}, [
        el("div", { class: "pane__title", text: "概览" }),
        el("div", { class: "pane__desc", text: "站点当前的内容规模。" }),
      ]),
    ])
  );

  const s = state.stats || {};
  if (s.using_default_password) {
    pane.appendChild(
      el("div", { class: "alert alert--danger" }, [
        el("span", { text: "⚠️" }),
        el("div", {}, [
          el("b", { text: "你还在用默认口令 admin12345" }),
          el("span", {
            text: "部署到公网之前必须改掉。左边「改口令」可以直接改。",
          }),
        ]),
      ])
    );
  }

  if (s.pending_comments) {
    const tip = el("div", { class: "alert alert--click", tabindex: "0", role: "button" }, [
      el("span", { text: "💬" }),
      el("div", {}, [
        el("b", { text: `${s.pending_comments} 条评论等你审核` }),
        el("span", { text: "点这里去处理，通过之后前台才会显示。" }),
      ]),
    ]);
    tip.addEventListener("click", () => {
      state.active = "comments";
      renderSide();
      renderComments();
    });
    tip.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        tip.click();
      }
    });
    pane.appendChild(tip);
  }

  const grid = el("div", { class: "stat-grid" });
  [
    { num: s.movies ?? 0, label: "电影" },
    { num: s.works ?? 0, label: "作品" },
    { num: s.interests ?? 0, label: "兴趣" },
    { num: s.categories ?? 0, label: "分类" },
    { num: s.resume_items ?? 0, label: "简历条目" },
    { num: s.skills ?? 0, label: "技能" },
    { num: s.comments ?? 0, label: "评论" },
    { num: s.pending_comments ?? 0, label: "待审核" },
    { num: s.avg_rating ?? 0, label: "平均评分" },
  ].forEach((it) => {
    grid.appendChild(
      el("div", { class: "glass glass--pad stat" }, [
        el("div", { class: "stat__num", text: String(it.num) }),
        el("div", { class: "stat__label", text: it.label }),
      ])
    );
  });
  pane.appendChild(grid);

  pane.appendChild(
    el("div", { class: "glass glass--pad glass--soft" }, [
      el("h3", { style: { marginBottom: "10px" }, text: "接下来可以做的" }),
      el("ul", { style: { margin: 0, paddingLeft: "20px", color: "var(--ink-soft)" } }, [
        el("li", { text: "在「关于我」里换成你自己的简介、头像和联系方式。" }),
        el("li", { text: "在「简历经历」里把示例经历替换成你真实的履历。" }),
        el("li", { text: "在「技能」里调整熟练度，首页与简历页的 3D 球会跟着变。" }),
        el("li", { text: "在「兴趣爱好」里调整首页卡片的顺序和配色。" }),
        el("li", { text: "在「电影」里把你真正看过的片子录进来，示例数据可以直接删。" }),
        el("li", { text: "在「分类」里补充你自己的细小分类，前台筛选会自动跟上。" }),
      ]),
    ])
  );
}

/* --------------------------- 关于我 --------------------------- */

async function renderProfile() {
  const pane = document.getElementById("pane");
  pane.textContent = "";
  pane.appendChild(
    el("div", { class: "pane__head" }, [
      el("div", {}, [
        el("div", { class: "pane__title", text: "关于我" }),
        el("div", {
          class: "pane__desc",
          text: "首页 Hero 与「关于我」区块的内容。links 与 highlights 用 JSON 数组填写。",
        }),
      ]),
    ])
  );

  let profile;
  try {
    profile = await API.get("/api/profile");
  } catch (err) {
    pane.appendChild(el("p", { class: "empty", text: `加载失败：${err.message}` }));
    return;
  }

  const form = el("form", { class: "form-grid" });
  const fields = [
    { key: "name", label: "名字", type: "text" },
    { key: "headline", label: "一句话身份", type: "text" },
    { key: "location", label: "所在地", type: "text" },
    { key: "email", label: "邮箱", type: "text" },
    { key: "avatar", label: "头像", type: "image", full: true },
    { key: "tagline", label: "首页副标题", type: "textarea", full: true },
    { key: "bio", label: "自我介绍正文（支持空行分段）", type: "textarea", full: true, rows: 10 },
    {
      key: "links",
      label: "外链 JSON，例：[{\"label\":\"GitHub\",\"url\":\"https://...\"}]",
      type: "json",
      full: true,
      rows: 4,
    },
    {
      key: "highlights",
      label: "亮点 JSON，例：[{\"icon\":\"🎬\",\"title\":\"标题\",\"text\":\"说明\"}]",
      type: "json",
      full: true,
      rows: 6,
    },
  ];

  fields.forEach((f) => {
    const wrap = el("div", { class: "field field--full" });
    wrap.appendChild(el("label", { class: "field__label", text: f.label }));
    const input =
      f.type === "textarea" || f.type === "json"
        ? el("textarea", { class: "textarea" })
        : el("input", { class: "input", type: "text" });
    if (f.rows) input.rows = f.rows;
    if (f.type === "json") {
      input.value = JSON.stringify(profile[f.key] || [], null, 2);
    } else {
      input.value = profile[f.key] ?? "";
    }
    input.dataset.key = f.key;
    input.dataset.type = f.type;
    wrap.appendChild(input);
    if (f.type === "image") attachImageUpload(wrap, input);
    form.appendChild(wrap);
  });

  const actions = el("div", { class: "form-actions", style: { gridColumn: "1 / -1" } }, [
    el("button", { class: "btn btn--primary", type: "submit", text: "保存" }),
  ]);
  form.appendChild(actions);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = actions.querySelector("button");
    btn.disabled = true;
    btn.textContent = "保存中…";
    try {
      const payload = {};
      fields.forEach((f) => {
        const input = form.querySelector(`[data-key="${f.key}"]`);
        const raw = input.value;
        if (f.type === "json") {
          try {
            payload[f.key] = JSON.parse(raw || "[]");
          } catch (_) {
            throw new Error(`${f.label} 不是合法 JSON`);
          }
        } else {
          payload[f.key] = raw;
        }
      });
      await API.put("/api/admin/profile", payload);
      toast("已保存，刷新前台看看");
    } catch (err) {
      toast(err.message, "err");
    } finally {
      btn.disabled = false;
      btn.textContent = "保存";
    }
  });

  pane.appendChild(form);
}

/* --------------------------- 评论管理 --------------------------- */

const COMMENT_FILTERS = [
  { key: "all", label: "全部" },
  { key: "pending", label: "待审核" },
  { key: "visible", label: "已公开" },
  { key: "hidden", label: "已隐藏" },
];

const TARGET_LABEL = { movie: "电影", work: "作品", profile: "主页" };

// 未隐藏 = 已公开；隐藏且站长没动过 = 待审核；隐藏且处理过 = 主动隐藏
function commentStatus(c) {
  if (!c.hidden) return { text: "已公开", cls: "tag-pill--ok" };
  return c.reviewed
    ? { text: "已隐藏", cls: "tag-pill--muted" }
    : { text: "待审核", cls: "tag-pill--warn" };
}

async function renderComments() {
  const pane = document.getElementById("pane");
  pane.textContent = "";

  const moderating = !!(state.stats && state.stats.comment_moderation);
  const approveAllBtn = el("button", {
    class: "btn btn--sm",
    type: "button",
    text: "全部通过",
  });

  pane.appendChild(
    el("div", { class: "pane__head" }, [
      el("div", {}, [
        el("div", { class: "pane__title", text: "评论" }),
        el("div", {
          class: "pane__desc",
          text: moderating
            ? "当前是「先审后发」：新留言要你点「通过」才会公开。"
            : "当前是「即发即显」。想改成先审后发，在 .env 里设 COMMENT_MODERATION=1 后重启。",
        }),
      ]),
      el("div", { class: "table__actions" }, [approveAllBtn]),
    ])
  );

  const filterBar = el("div", { class: "filter-bar" });
  COMMENT_FILTERS.forEach((f) => {
    const btn = el("button", {
      class: "chip-btn" + (state.commentFilter === f.key ? " is-active" : ""),
      type: "button",
      text: f.label,
    });
    btn.addEventListener("click", () => {
      state.commentFilter = f.key;
      renderComments();
    });
    filterBar.appendChild(btn);
  });
  pane.appendChild(filterBar);

  approveAllBtn.addEventListener("click", async () => {
    if (!confirm("把当前所有待审核评论一次性公开？")) return;
    try {
      const res = await API.post("/api/admin/comments/approve-all", {});
      toast(res.message);
      await loadStats();
      renderSide();
      renderComments();
    } catch (err) {
      toast(err.message, "err");
    }
  });

  const wrap = el("div", { class: "table-wrap" }, [el("p", { class: "empty", text: "加载中…" })]);
  pane.appendChild(wrap);

  let rows = [];
  try {
    rows = await API.get(`/api/admin/comments?status=${state.commentFilter}`);
  } catch (err) {
    wrap.textContent = "";
    wrap.appendChild(el("p", { class: "empty", text: `加载失败：${err.message}` }));
    return;
  }

  wrap.textContent = "";
  if (!rows.length) {
    wrap.appendChild(
      el("p", {
        class: "empty",
        text:
          state.commentFilter === "pending"
            ? "没有待审核的评论。"
            : state.commentFilter === "hidden"
            ? "没有被隐藏的评论。"
            : "还没有人留言。",
      })
    );
    return;
  }

  const table = el("table", { class: "table" });
  const thead = el("thead");
  const tr = el("tr");
  ["状态", "昵称", "内容", "留言位置", "时间", "操作"].forEach((t) =>
    tr.appendChild(el("th", { text: t }))
  );
  thead.appendChild(tr);
  table.appendChild(thead);

  const tbody = el("tbody");

  rows.forEach((c) => {
    const line = el("tr", { class: c.hidden ? "row-hidden" : "" });
    const status = commentStatus(c);
    line.appendChild(
      el("td", {}, [el("span", { class: `tag-pill ${status.cls}`, text: status.text })])
    );
    line.appendChild(el("td", { text: c.nickname }));
    line.appendChild(el("td", { class: "cell-clip", text: c.content }));
    line.appendChild(
      el("td", {
        text: `${TARGET_LABEL[c.target_type] || c.target_type} · ${
          c.target_title || `#${c.target_id}`
        }`,
      })
    );
    line.appendChild(el("td", { text: fmtDate(c.created_at) }));

    const approveBtn = el("button", {
      class: "btn btn--sm btn--ok",
      type: "button",
      text: "通过",
    });
    const hideBtn = el("button", {
      class: "btn btn--sm",
      type: "button",
      text: c.hidden ? "恢复" : "隐藏",
    });
    const delBtn = el("button", { class: "btn btn--sm btn--rose", type: "button", text: "删除" });

    approveBtn.addEventListener("click", async () => {
      try {
        const updated = await API.patch(`/api/admin/comments/${c.id}/approve`);
        c.hidden = updated.hidden;
        c.reviewed = updated.reviewed;
        toast("已通过，现在前台能看到了");
        await loadStats();
        renderSide();
        renderComments();
      } catch (err) {
        toast(err.message, "err");
      }
    });

    hideBtn.addEventListener("click", async () => {
      try {
        const updated = await API.patch(`/api/admin/comments/${c.id}/hide`);
        c.hidden = updated.hidden;
        c.reviewed = updated.reviewed;
        toast(c.hidden ? "已隐藏" : "已恢复显示");
        await loadStats();
        renderSide();
        renderComments();
      } catch (err) {
        toast(err.message, "err");
      }
    });

    delBtn.addEventListener("click", async () => {
      if (!confirm("确定删除这条评论？此操作不可撤销。")) return;
      try {
        await API.del(`/api/admin/comments/${c.id}`);
        toast("已删除");
        await loadStats();
        renderSide();
        renderComments();
      } catch (err) {
        toast(err.message, "err");
      }
    });

    const buttons = [approveBtn, hideBtn, delBtn];
    if (!c.hidden && c.reviewed) buttons.splice(0, 1); // 已公开的不需要「通过」

    line.appendChild(el("td", {}, [el("div", { class: "table__actions" }, buttons)]));
    tbody.appendChild(line);
  });
  table.appendChild(tbody);
  wrap.appendChild(table);
}

/* --------------------------- 改口令 --------------------------- */

function renderPassword() {
  const pane = document.getElementById("pane");
  pane.textContent = "";
  pane.appendChild(
    el("div", { class: "pane__head" }, [
      el("div", {}, [
        el("div", { class: "pane__title", text: "修改管理口令" }),
        el("div", { class: "pane__desc", text: "口令以 PBKDF2 散列存储，看不到明文。" }),
      ]),
    ])
  );

  const form = el("form", { style: { maxWidth: "420px" } });
  const mk = (label, type, id) => {
    const wrap = el("div", { class: "field" });
    wrap.appendChild(el("label", { class: "field__label", for: id, text: label }));
    const input = el("input", { class: "input", type, id, required: "" });
    wrap.appendChild(input);
    return { wrap, input };
  };

  const oldF = mk("当前口令", "password", "pw-old");
  const newF = mk("新口令（至少 6 位）", "password", "pw-new");
  const newF2 = mk("再输入一次新口令", "password", "pw-new2");

  const btn = el("button", { class: "btn btn--primary", type: "submit", text: "更新口令" });

  form.append(oldF.wrap, newF.wrap, newF2.wrap, btn);

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (newF.input.value !== newF2.input.value) {
      toast("两次输入的新口令不一致", "err");
      return;
    }
    btn.disabled = true;
    try {
      await API.post("/api/admin/password", {
        old_password: oldF.input.value,
        new_password: newF.input.value,
      });
      toast("口令已更新，下次登录请用新口令");
      form.reset();
      await loadStats();
      renderSide();
    } catch (err) {
      toast(err.message, "err");
    } finally {
      btn.disabled = false;
    }
  });

  pane.appendChild(form);
}

/* --------------------------- 面板路由 --------------------------- */

function renderPane(key) {
  if (key === "overview") return renderOverview();
  if (key === "profile") return renderProfile();
  if (key === "comments") return renderComments();
  if (key === "password") return renderPassword();
  if (RESOURCES[key]) return renderResource(key);
  return renderOverview();
}

/* --------------------------- 启动 --------------------------- */

document.addEventListener("DOMContentLoaded", () => {
  initProgress();

  /* 错误条的按钮 */
  const copyBtn = document.getElementById("fatal-copy");
  if (copyBtn) {
    copyBtn.addEventListener("click", async () => {
      const text = DIAG.text();
      try {
        await navigator.clipboard.writeText(text);
        toast("诊断信息已复制");
      } catch (_) {
        // 剪贴板不可用时退回选中文本，用户仍可手动 Ctrl+C
        window.prompt("复制下面的诊断信息：", text);
      }
    });
  }
  const reloadBtn = document.getElementById("fatal-reload");
  if (reloadBtn) {
    reloadBtn.addEventListener("click", () => location.reload());
  }

  const loginErr = document.getElementById("login-err");
  const setLoginErr = (msg) => {
    if (!loginErr) return;
    loginErr.textContent = msg || "";
    loginErr.hidden = !msg;
  };

  const loginForm = document.getElementById("login-form");
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = document.getElementById("login-password");
    const btn = loginForm.querySelector("button[type=submit]");
    btn.disabled = true;
    btn.textContent = "验证中…";
    setLoginErr("");
    try {
      await API.post("/api/admin/login", { password: input.value });
      input.value = "";
      state.loggedIn = true;
      toast("登录成功");
      await showAdmin();
    } catch (err) {
      const msg = (err && err.message) || String(err);
      setLoginErr(msg);
      toast(msg, "err");
      // 口令不对和「进去了但渲染不出来」是两件事，分别提示
      if (!err || err.status !== 401) {
        showFatal(`登录请求异常：${msg}${err && err.status ? `（HTTP ${err.status}）` : ""}`);
      }
    } finally {
      btn.disabled = false;
      btn.textContent = "进入后台";
    }
  });

  document.getElementById("btn-logout").addEventListener("click", async () => {
    try {
      await API.post("/api/admin/logout", {});
    } catch (_) {
      /* 忽略 */
    }
    location.reload();
  });

  checkSession();
});
