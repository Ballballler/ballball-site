/* ========================================================================
   movies.js —— 恐怖电影档案：幽灵 + 幽灵系宝可梦 主视觉
   数据走真实 API（/api/movies /api/categories），评论落库。
   ===================================================================== */

/* 主幽灵（沿用 personal-orbit 的手绘小幽灵） */
const GHOST_SVG = `<svg viewBox="0 0 260 290" role="img" aria-label="原创小幽灵插画"><defs><linearGradient id="ghost-body" x1="0" y1="0" x2=".9" y2="1"><stop offset="0" stop-color="#ded8ed" stop-opacity=".94"/><stop offset=".65" stop-color="#a89cba" stop-opacity=".8"/><stop offset="1" stop-color="#716681" stop-opacity=".45"/></linearGradient><linearGradient id="ghost-shine"><stop stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs><ellipse cx="131" cy="259" rx="64" ry="9" fill="#050810" opacity=".4"/><path d="M64 141c-5-55 13-100 64-103 49-3 78 34 74 85-3 42 11 67 14 96-17 8-25-12-39-9-14 2-18 28-34 24-15-3-20-22-33-19-18 3-23 23-36 14-13-8-8-26-23-29 9-16 16-36 13-59Z" fill="url(#ghost-body)" stroke="#dbd2e8" stroke-opacity=".45" stroke-width="1.2"/><path d="M77 117c-2-40 19-62 51-65" fill="none" stroke="url(#ghost-shine)" stroke-width="3" stroke-linecap="round"/><ellipse cx="111" cy="130" rx="8" ry="12" fill="#343042"/><ellipse cx="151" cy="125" rx="8" ry="12" fill="#343042"/><path d="M127 151q7 6 12-1" fill="none" stroke="#595064" stroke-width="3" stroke-linecap="round"/><ellipse cx="95" cy="151" rx="9" ry="4" fill="#c797a4" opacity=".45"/><ellipse cx="167" cy="145" rx="9" ry="4" fill="#c797a4" opacity=".45"/><path d="m42 76 3-9 3 9 9 3-9 3-3 9-3-9-9-3Z" fill="#baaac8" opacity=".65"/><path d="m219 157 2-6 2 6 6 2-6 2-2 6-2-6-6-2Z" fill="#b9c9bd" opacity=".7"/></svg>`;

/* 幽灵系宝可梦（简化手绘，配色贴主题）：耿鬼 / 迷拟Q / 烛光灵 */
const GENGAR = `<svg viewBox="0 0 100 100" role="img" aria-label="耿鬼"><path d="M50 14 C 71 14 85 32 85 53 C 85 75 69 89 50 89 C 31 89 15 75 15 53 C 15 32 29 14 50 14 Z" fill="#6d5b93"/><path d="M22 24 L34 14 L32 30 Z M78 24 L66 14 L68 30 Z" fill="#6d5b93"/><path d="M33 42 L48 47 L33 52 Z M67 42 L52 47 L67 52 Z" fill="#e23b3b"/><path d="M30 60 Q50 74 70 60 Q60 70 50 70 Q40 70 30 60 Z" fill="#f4eef6"/><path d="M38 62 L41 66 L44 62 M50 64 L53 68 L56 64 M62 62 L65 66 L68 62" stroke="#3a2f52" stroke-width="1.4" fill="none"/></svg>`;
const MIMIKYU = `<svg viewBox="0 0 100 100" role="img" aria-label="迷拟Q"><path d="M30 88 C 22 70 24 40 34 24 C 42 12 58 12 66 24 C 76 40 78 70 70 88 Z" fill="#e6d7a8"/><path d="M34 24 C 40 14 60 14 66 24 C 60 20 40 20 34 24 Z" fill="#cbb87e"/><path d="M40 30 L44 44 M60 30 L56 44" stroke="#3a3a3a" stroke-width="2.4" stroke-linecap="round"/><circle cx="41" cy="52" r="3.4" fill="#2a2a2a"/><circle cx="59" cy="52" r="3.4" fill="#2a2a2a"/><path d="M44 66 Q50 71 56 66" stroke="#2a2a2a" stroke-width="2.2" fill="none" stroke-linecap="round"/><path d="M72 50 L86 44 L82 58 Z" fill="#8a7a4e"/></svg>`;
const LITWICK = `<svg viewBox="0 0 100 100" role="img" aria-label="烛光灵"><ellipse cx="50" cy="86" rx="16" ry="4" fill="#000" opacity=".3"/><rect x="38" y="42" width="24" height="44" rx="9" fill="#e8ecf2"/><path d="M50 12 C 58 22 60 30 50 40 C 40 30 42 22 50 12 Z" fill="#a58fd0"/><path d="M50 22 C 54 27 55 31 50 36 C 45 31 46 27 50 22 Z" fill="#d9c9f2"/><circle cx="44" cy="58" r="3.6" fill="#f0c93f"/><circle cx="56" cy="58" r="3.6" fill="#f0c93f"/><path d="M42 70 Q50 75 58 70" stroke="#8a90a0" stroke-width="2" fill="none" stroke-linecap="round"/></svg>`;

const state = { movies: [], categories: [], activeCategory: 0 };

/* ---------------------------- 主视觉 ---------------------------- */

function renderStage() {
  document.getElementById("ghost-host").innerHTML = "";
  const host = document.getElementById("ghost-host");
  host.insertAdjacentHTML("beforeend", GHOST_SVG);
  const pals = document.getElementById("ghost-pals");
  pals.innerHTML = "";
  [GENGAR, MIMIKYU, LITWICK].forEach((svg) => pals.insertAdjacentHTML("beforeend", svg));
}

/* ---------------------------- 统计 ---------------------------- */

function renderStats() {
  const host = document.getElementById("movie-stats");
  if (!host) return;
  const n = state.movies.length;
  const avg = n ? (state.movies.reduce((s, m) => s + m.rating, 0) / n).toFixed(1) : "0.0";
  const top = state.movies.reduce((a, m) => (m.scare_level > (a?.scare_level || 0) ? m : a), null);
  host.textContent = "";
  const rows = [
    ["收录影片", String(n)],
    ["平均评分", avg],
    ["最吓人的", top ? `《${top.title}》` : "—"],
    ["分类数", String(state.categories.length)],
  ];
  rows.forEach(([k, v]) => {
    host.appendChild(
      el("div", { style: { display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #ffffff0a" } }, [
        el("span", { style: { fontSize: "11px", color: "var(--muted)" }, text: k }),
        el("span", { style: { fontSize: "13px", fontFamily: "var(--mono)", color: "var(--violet)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "60%" }, text: v }),
      ])
    );
  });
}

/* ---------------------------- 筛选 ---------------------------- */

function renderFilters() {
  const wrap = document.getElementById("movie-filters");
  wrap.textContent = "";
  const mk = (label, value) => {
    const b = el("button", {
      type: "button",
      class: "filter" + (state.activeCategory === value ? " is-active" : ""),
      text: label,
      "aria-pressed": state.activeCategory === value ? "true" : "false",
    });
    b.addEventListener("click", () => {
      state.activeCategory = value;
      renderFilters();
      renderGrid();
    });
    return b;
  };
  wrap.appendChild(mk("全部", 0));
  state.categories.forEach((c) => wrap.appendChild(mk(c.name, c.id)));
  wrap.appendChild(mk("未分类", -1));
}

/* ---------------------------- 网格 ---------------------------- */

function renderGrid() {
  const grid = document.getElementById("movie-grid");
  grid.textContent = "";
  const list = state.movies.filter((m) => {
    if (state.activeCategory === 0) return true;
    if (state.activeCategory === -1) return !m.category_id;
    return m.category_id === state.activeCategory;
  });
  if (!list.length) {
    grid.appendChild(el("div", { class: "empty", text: "这个分类下还没有电影。去后台加一部。" }));
    return;
  }
  list.forEach((m) => grid.appendChild(buildMovieCard(m, openMovieDetail)));
  revealStaggered(grid);
  initCursor(grid);
}

/* ---------------------------- 启动 ---------------------------- */

async function boot() {
  try {
    const [movies, categories] = await Promise.all([
      API.get("/api/movies"),
      API.get("/api/categories?kind=movie_genre"),
    ]);
    state.movies = movies || [];
    state.categories = categories || [];
    renderStage();
    renderStats();
    renderFilters();
    renderGrid();
    // 区块的显示与顺序由后台「页面区块」决定
    await applyPageSections("movies", {
      hero: document.getElementById("movie-hero"),
      stats: document.getElementById("movie-stats"),
      filters: document.getElementById("movie-filters"),
      grid: document.getElementById("movie-grid"),
    });
    initReveal();
    initCursor();
    // 支持 #movie-<id> 深链
    const deep = location.hash.match(/^#movie-(\d+)$/);
    if (deep) {
      const target = state.movies.find((x) => x.id === Number(deep[1]));
      if (target) openMovieDetail(target);
    }
  } catch (err) {
    toast(`加载失败：${err.message}`, "err");
  }
}

// 深链可能在渲染完成前就被 hashchange 触发（同一页点两次锚点）
window.addEventListener("hashchange", () => {
  const deep = location.hash.match(/^#movie-(\d+)$/);
  if (!deep) return closeDetail();
  const target = state.movies.find((x) => x.id === Number(deep[1]));
  if (target) openMovieDetail(target);
});

document.addEventListener("DOMContentLoaded", boot);
