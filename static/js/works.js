/* ========================================================================
   works.js —— 作品页：按状态筛选、详情弹层（含音频小样与评论区）
   ===================================================================== */

const state = {
  works: [],
  categories: [],
  activeStatus: "all",
  activeTag: "",
};

const modal = () => document.getElementById("detail-modal");
const panel = () => document.getElementById("detail-panel");

const STATUS_FILTERS = [
  { key: "all", label: "全部" },
  { key: "idea", label: "构思中" },
  { key: "demo", label: "有小样" },
  { key: "released", label: "已完成" },
];

function renderStats() {
  const wrap = document.getElementById("work-stats");
  if (!wrap) return;
  wrap.textContent = "";
  const list = state.works;
  const avg = list.length
    ? Math.round(list.reduce((s, w) => s + (w.progress || 0), 0) / list.length)
    : 0;
  const items = [
    { num: String(list.length), label: "作品数" },
    {
      num: String(list.filter((w) => w.status === "released").length),
      label: "已完成",
    },
    { num: String(list.filter((w) => w.status === "demo").length), label: "有小样" },
    { num: `${avg}%`, label: "平均完成度" },
  ];
  items.forEach((it, i) => {
    wrap.appendChild(
      el(
        "div",
        {
          class: "glass glass--pad glass--spot stat reveal",
          style: { transitionDelay: `${i * 70}ms` },
        },
        [
          el("div", { class: "stat__num", text: it.num }),
          el("div", { class: "stat__label", text: it.label }),
        ]
      )
    );
  });
  initCursor(wrap);
}

function renderFilters() {
  const wrap = document.getElementById("work-filters");
  if (!wrap) return;
  wrap.textContent = "";

  STATUS_FILTERS.forEach((f) => {
    const n =
      f.key === "all"
        ? state.works.length
        : state.works.filter((w) => w.status === f.key).length;
    if (!n && f.key !== "all") return;
    const b = el("button", {
      class: "filter" + (state.activeStatus === f.key ? " is-active" : ""),
      type: "button",
      text: `${f.label} (${n})`,
      "aria-pressed": state.activeStatus === f.key ? "true" : "false",
    });
    b.addEventListener("click", () => {
      state.activeStatus = f.key;
      renderFilters();
      renderGrid();
    });
    wrap.appendChild(b);
  });

  // 分类筛选（作品类型）
  state.categories
    .filter((c) => c.kind === "work_type")
    .forEach((c) => {
      if (!state.works.some((w) => w.category_id === c.id)) return;
      wrap.appendChild(
        el("span", {
          class: "chip chip--dot",
          text: c.name,
          style: { "--chip-color": c.color, alignSelf: "center" },
          title: c.description || "",
        })
      );
    });

  renderTagFilters();
}

/* 风格标签筛选：标签由后台「推断 + 点选」写入，这里只负责把它们列出来 */
function renderTagFilters() {
  const wrap = document.getElementById("work-tag-filters");
  if (!wrap) return;
  wrap.textContent = "";

  const counter = new Map();
  state.works.forEach((w) => {
    (w.tags || []).forEach((t) => counter.set(t, (counter.get(t) || 0) + 1));
  });
  const tags = [...counter.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  if (!tags.length) return;

  wrap.appendChild(el("span", { class: "tag-filters__label", text: "风格" }));

  const mk = (tag, n) => {
    const on = state.activeTag === tag;
    const b = el("button", {
      class: "chip chip--pick" + (on ? " chip--ok" : ""),
      type: "button",
      text: tag ? `${tag} (${n})` : `全部风格 (${n})`,
      "aria-pressed": on ? "true" : "false",
    });
    b.addEventListener("click", () => {
      state.activeTag = on ? "" : tag;
      renderFilters();
      renderGrid();
    });
    wrap.appendChild(b);
  };

  mk("", state.works.length);
  tags.forEach(([t, n]) => mk(t, n));
}

function renderGrid() {
  const grid = document.getElementById("work-grid");
  if (!grid) return;
  grid.textContent = "";
  const list = state.works.filter((w) => {
    if (state.activeStatus !== "all" && w.status !== state.activeStatus) return false;
    if (state.activeTag && !(w.tags || []).includes(state.activeTag)) return false;
    return true;
  });
  if (!list.length) {
    grid.appendChild(
      el("div", { class: "glass glass--pad empty", style: { gridColumn: "1 / -1" } }, [
        el("p", { text: "这个状态下还没有作品。" }),
      ])
    );
    return;
  }
  list.forEach((w, i) => grid.appendChild(buildWorkCard(w, openWorkDetail, i)));
  revealStaggered(grid);
  initCursor(grid);
}

async function boot() {
  try {
    const [works, categories] = await Promise.all([
      API.get("/api/works"),
      API.get("/api/categories?kind=work_type"),
    ]);
    state.works = works;
    state.categories = categories;
    renderStats();
    renderFilters();
    renderGrid();
    // 区块的显示与顺序由后台「页面区块」决定
    await applyPageSections("works", {
      hero: document.getElementById("work-hero"),
      stats: document.getElementById("work-stats"),
      filters: document.getElementById("work-filters"),
      "tag-filters": document.getElementById("work-tag-filters"),
      grid: document.getElementById("work-grid"),
    });
    initReveal();
    initCursor();

    const m = /^#work-(\d+)$/.exec(location.hash);
    if (m) {
      const target = state.works.find((x) => String(x.id) === m[1]);
      if (target) openWorkDetail(target);
    }
  } catch (err) {
    toast(`加载失败：${err.message}`, "err");
  }
}

window.addEventListener("hashchange", () => {
  const deep = /^#work-(\d+)$/.exec(location.hash);
  if (!deep) return closeDetail();
  const target = state.works.find((x) => String(x.id) === deep[1]);
  if (target) openWorkDetail(target);
});

document.addEventListener("DOMContentLoaded", boot);
