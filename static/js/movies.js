/* ========================================================================
   movies.js —— 恐怖电影档案：幽灵 + 幽灵系宝可梦 主视觉
   数据走真实 API（/api/movies /api/categories）。
   ===================================================================== */

/* 主幽灵（沿用 personal-orbit 的手绘小幽灵） */
const GHOST_SVG = `<svg viewBox="0 0 260 290" role="img" aria-label="原创小幽灵插画"><defs><linearGradient id="ghost-body" x1="0" y1="0" x2=".9" y2="1"><stop offset="0" stop-color="#ded8ed" stop-opacity=".94"/><stop offset=".65" stop-color="#a89cba" stop-opacity=".8"/><stop offset="1" stop-color="#716681" stop-opacity=".45"/></linearGradient><linearGradient id="ghost-shine"><stop stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs><ellipse cx="131" cy="259" rx="64" ry="9" fill="#050810" opacity=".4"/><path d="M64 141c-5-55 13-100 64-103 49-3 78 34 74 85-3 42 11 67 14 96-17 8-25-12-39-9-14 2-18 28-34 24-15-3-20-22-33-19-18 3-23 23-36 14-13-8-8-26-23-29 9-16 16-36 13-59Z" fill="url(#ghost-body)" stroke="#dbd2e8" stroke-opacity=".45" stroke-width="1.2"/><path d="M77 117c-2-40 19-62 51-65" fill="none" stroke="url(#ghost-shine)" stroke-width="3" stroke-linecap="round"/><ellipse cx="111" cy="130" rx="8" ry="12" fill="#343042"/><ellipse cx="151" cy="125" rx="8" ry="12" fill="#343042"/><path d="M127 151q7 6 12-1" fill="none" stroke="#595064" stroke-width="3" stroke-linecap="round"/><ellipse cx="95" cy="151" rx="9" ry="4" fill="#c797a4" opacity=".45"/><ellipse cx="167" cy="145" rx="9" ry="4" fill="#c797a4" opacity=".45"/><path d="m42 76 3-9 3 9 9 3-9 3-3 9-3-9-9-3Z" fill="#baaac8" opacity=".65"/><path d="m219 157 2-6 2 6 6 2-6 2-2 6-2-6-6-2Z" fill="#b9c9bd" opacity=".7"/></svg>`;

/* 幽灵系宝可梦（简化手绘，配色贴主题）：耿鬼 / 迷拟Q / 烛光灵 */
const GENGAR = `<svg viewBox="0 0 100 100" role="img" aria-label="耿鬼"><path d="M50 14 C 71 14 85 32 85 53 C 85 75 69 89 50 89 C 31 89 15 75 15 53 C 15 32 29 14 50 14 Z" fill="#6d5b93"/><path d="M22 24 L34 14 L32 30 Z M78 24 L66 14 L68 30 Z" fill="#6d5b93"/><path d="M33 42 L48 47 L33 52 Z M67 42 L52 47 L67 52 Z" fill="#e23b3b"/><path d="M30 60 Q50 74 70 60 Q60 70 50 70 Q40 70 30 60 Z" fill="#f4eef6"/><path d="M38 62 L41 66 L44 62 M50 64 L53 68 L56 64 M62 62 L65 66 L68 62" stroke="#3a2f52" stroke-width="1.4" fill="none"/></svg>`;
const MIMIKYU = `<svg viewBox="0 0 100 100" role="img" aria-label="迷拟Q"><path d="M30 88 C 22 70 24 40 34 24 C 42 12 58 12 66 24 C 76 40 78 70 70 88 Z" fill="#e6d7a8"/><path d="M34 24 C 40 14 60 14 66 24 C 60 20 40 20 34 24 Z" fill="#cbb87e"/><path d="M40 30 L44 44 M60 30 L56 44" stroke="#3a3a3a" stroke-width="2.4" stroke-linecap="round"/><circle cx="41" cy="52" r="3.4" fill="#2a2a2a"/><circle cx="59" cy="52" r="3.4" fill="#2a2a2a"/><path d="M44 66 Q50 71 56 66" stroke="#2a2a2a" stroke-width="2.2" fill="none" stroke-linecap="round"/><path d="M72 50 L86 44 L82 58 Z" fill="#8a7a4e"/></svg>`;
const LITWICK = `<svg viewBox="0 0 100 100" role="img" aria-label="烛光灵"><ellipse cx="50" cy="86" rx="16" ry="4" fill="#000" opacity=".3"/><rect x="38" y="42" width="24" height="44" rx="9" fill="#e8ecf2"/><path d="M50 12 C 58 22 60 30 50 40 C 40 30 42 22 50 12 Z" fill="#a58fd0"/><path d="M50 22 C 54 27 55 31 50 36 C 45 31 46 27 50 22 Z" fill="#d9c9f2"/><circle cx="44" cy="58" r="3.6" fill="#f0c93f"/><circle cx="56" cy="58" r="3.6" fill="#f0c93f"/><path d="M42 70 Q50 75 58 70" stroke="#8a90a0" stroke-width="2" fill="none" stroke-linecap="round"/></svg>`;

const state = {
  movies: [],
  candidates: [],
  categories: [],
  activeCategory: 0,
  candidateCategory: 0, // 候选区的分类筛选：0 = 全部（含未分类）
  query: "",
};

/* ---------------------------- 候选片 ---------------------------- */
/* 候选片是「别人推荐、我还没看」的片子。这一区只在动态模式（本地 / 自己的
   服务器）下出现 —— 静态站没有后端，打不了分也删不掉，不如不显示。 */

function isCandidateMode() {
  return !isStaticMode() && state.candidates.length > 0;
}

function renderCandidates() {
  const host = document.getElementById("movie-candidates");
  const grid = document.getElementById("candidates-grid");
  if (!host || !grid) return;
  if (!isCandidateMode()) {
    host.hidden = true;
    grid.textContent = "";
    return;
  }
  host.hidden = false;
  grid.textContent = "";

  // 分类筛选：0 = 全部；-1 = 未分类；其余按 category_id 精确匹配
  const shown = state.candidates.filter((m) => {
    if (!state.candidateCategory) return true;
    if (state.candidateCategory === -1) return m.category_id == null;
    return m.category_id === state.candidateCategory;
  });

  const hint = document.getElementById("candidates-hint");
  if (hint) {
    hint.textContent = state.candidateCategory
      ? `这一栏有 ${shown.length} 部。打完分就算看过，会挪进正式档案；不想看的点「不看」划掉。`
      : `还有 ${shown.length} 部没看。打完分就算看过，会挪进正式档案；不想看的点「不看」划掉。`;
  }
  shown.forEach((m, i) => grid.appendChild(buildCandidateCard(m, i)));
  revealStaggered(grid);
}

function buildCandidateCard(movie, index) {
  const cover = el("div", { class: "candidate__cover" });
  const posterSrc = movie.poster_url || movie.poster;
  if (posterSrc) {
    const img = el("img", {
      src: posterSrc,
      alt: `${movie.title} 海报`,
      loading: "lazy",
      decoding: "async",
    });
    img.addEventListener("error", () => {
      img.remove();
      cover.appendChild(el("span", { class: "movie__cover-ph", text: "🎬" }));
    });
    cover.appendChild(img);
  } else {
    cover.appendChild(el("span", { class: "movie__cover-ph", text: "🎬" }));
  }

  const meta = [movie.year ? String(movie.year) : "", movie.director]
    .filter(Boolean)
    .join(" · ");
  const tmdb = movie.tmdb_rating ? `TMDB ${movie.tmdb_rating}` : "";

  const card = el(
    "article",
    { class: "glass glass--lift candidate reveal" },
    [
      cover,
      el("div", { class: "candidate__body" }, [
        el("h4", { class: "candidate__title", text: movie.title }),
        el("div", { class: "candidate__meta", text: meta }),
        tmdb ? el("div", { class: "candidate__tmdb", text: tmdb }) : null,
        el("p", {
          class: "candidate__overview",
          text: (movie.overview || "（TMDB 没有简介）").slice(0, 96),
        }),
        el("div", { class: "candidate__actions" }, [
          (() => {
            const b = el("button", {
              class: "candidate__btn candidate__btn--rate",
              type: "button",
              text: "打分",
            });
            b.addEventListener("click", () => openRateDialog(movie));
            return b;
          })(),
          (() => {
            const b = el("button", {
              class: "candidate__btn",
              type: "button",
              text: "不看",
            });
            b.addEventListener("click", () => dropCandidate(movie));
            return b;
          })(),
        ]),
      ]),
    ]
  );
  return card;
}

/** 打分弹层：分值 + 强度 + 推荐 + 短评，存完即转正 */
function openRateDialog(movie) {
  const wrap = el("div", { class: "detail" });
  wrap.appendChild(
    el("div", { class: "rate__head" }, [
      (() => {
        const img = el("img", { class: "rate__poster", alt: `${movie.title} 海报` });
        if (movie.poster_url || movie.poster) img.src = movie.poster_url || movie.poster;
        else img.hidden = true;
        return img;
      })(),
      el("div", {}, [
        el("h3", { text: movie.title }),
        el("p", {
          class: "enroll__hint",
          text: [movie.year, movie.director, movie.runtime ? `${movie.runtime} 分钟` : ""]
            .filter(Boolean)
            .join(" · "),
        }),
        movie.overview
          ? el("p", { class: "rate__overview", text: movie.overview.slice(0, 200) })
          : null,
      ]),
    ])
  );

  const ratingInput = el("input", {
    type: "range",
    min: "0",
    max: "10",
    step: "0.5",
    value: "7",
    "aria-label": "我的评分，0 到 10 分",
  });
  const ratingOut = el("output", { class: "enroll__output", text: "7.0" });
  ratingInput.addEventListener("input", () => {
    ratingOut.textContent = Number(ratingInput.value).toFixed(1);
  });

  const scare = dotPicker(5, 3);
  const recommend = dotPicker(5, 3);
  const verdictInput = el("input", {
    type: "text",
    maxlength: "300",
    placeholder: "一句话结论，例如：今年最惊喜的一部",
    "aria-label": "一句话短判",
  });
  const watchedInput = el("input", {
    type: "date",
    value: new Date().toISOString().slice(0, 10),
    "aria-label": "观看日期",
  });
  const catSelect = el("select", { "aria-label": "分类" }, [
    el("option", { value: "", text: "沿用 TMDB 给的分类" }),
    ...state.categories.map((c) => el("option", { value: String(c.id), text: c.name })),
  ]);
  if (movie.category_id) {
    [...catSelect.options].forEach((o) => {
      if (o.value === String(movie.category_id)) o.selected = true;
    });
  }

  wrap.appendChild(
    el("div", { class: "enroll__field" }, [
      el("label", { class: "enroll__label", text: "我的评分" }),
      el("div", { class: "enroll__range" }, [ratingInput, ratingOut]),
    ])
  );
  wrap.appendChild(
    el("div", { class: "enroll__field" }, [
      el("label", { class: "enroll__label", text: "恐怖强度（1 最温和，5 最吓人）" }),
      scare.node,
    ])
  );
  wrap.appendChild(
    el("div", { class: "enroll__field" }, [
      el("label", { class: "enroll__label", text: "推荐指数" }),
      recommend.node,
    ])
  );
  wrap.appendChild(
    el("div", { class: "enroll__field" }, [
      el("label", { class: "enroll__label", text: "一句话短判" }),
      verdictInput,
    ])
  );
  wrap.appendChild(
    el("div", { class: "enroll__field" }, [
      el("label", { class: "enroll__label", text: "观看日期" }),
      watchedInput,
    ])
  );
  wrap.appendChild(
    el("div", { class: "enroll__field" }, [
      el("label", { class: "enroll__label", text: "分类" }),
      catSelect,
    ])
  );

  const saveBtn = el("button", { class: "searchbar__add", type: "button", text: "记下来，转正" });
  const skipBtn = el("button", { class: "searchbar__clear", type: "button", text: "先不打分" });
  skipBtn.addEventListener("click", () => closeDetail());
  saveBtn.addEventListener("click", async () => {
    saveBtn.disabled = true;
    saveBtn.textContent = "保存中…";
    try {
      await API.post(`/api/admin/movies/${movie.id}/rate`, {
        rating: Number(ratingInput.value),
        scare_level: scare.get(),
        recommend_level: recommend.get(),
        verdict: verdictInput.value.trim(),
        watched_at: watchedInput.value,
        category_id: catSelect.value ? Number(catSelect.value) : null,
      });
      toast(`《${movie.title}》已转正进档案`);
      closeDetail();
      await reloadMovies();
    } catch (err) {
      toast(err.message, "err");
      saveBtn.disabled = false;
      saveBtn.textContent = "记下来，转正";
    }
  });
  wrap.appendChild(el("div", { class: "enroll__actions" }, [skipBtn, saveBtn]));
  openDetailWith(wrap, "看完就打个分");
  saveBtn.focus();
}

/** 不看这部：直接从候选里删掉 */
async function dropCandidate(movie) {
  if (!window.confirm(`把《${movie.title}》从候选里删掉？`)) return;
  try {
    await API.del(`/api/admin/movies/${movie.id}`);
    toast(`已划掉《${movie.title}》`);
    await reloadMovies();
  } catch (err) {
    toast(err.message, "err");
  }
}

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
  // 统计只算正式档案：候选片还没看，混进来会把平均分和「最吓人的」带偏
  const watched = state.movies.filter((m) => m.status !== "candidate");
  const n = watched.length;
  const avg = n ? (watched.reduce((s, m) => s + m.rating, 0) / n).toFixed(1) : "0.0";
  const top = watched.reduce((a, m) => (m.scare_level > (a?.scare_level || 0) ? m : a), null);
  host.textContent = "";
  const rows = [
    ["收录影片", String(n)],
    ["平均评分", avg],
    ["最吓人的", top ? `《${top.title}》` : "—"],
    ["待看候选", String(state.candidates.length)],
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

/* 候选区的分类筛选。
   候选片单可能包含多个来源（大众恐怖片 / 伪纪录片 …），平铺在一起来看很糊，
   所以给它自己的分类栏 —— 与上面正式档案的筛选互相独立。 */
function renderCandidateFilters() {
  const wrap = document.getElementById("candidates-filters");
  if (!wrap) return;
  wrap.textContent = "";

  // 只列出**真的在候选区里有片子**的分类，避免点进去一片空白
  const counts = new Map();
  state.candidates.forEach((m) => {
    const key = m.category_id == null ? -1 : m.category_id;
    counts.set(key, (counts.get(key) || 0) + 1);
  });

  const mk = (label, value, count) => {
    const b = el("button", {
      type: "button",
      class: "filter" + (state.candidateCategory === value ? " is-active" : ""),
      text: count == null ? label : `${label} ${count}`,
      "aria-pressed": state.candidateCategory === value ? "true" : "false",
    });
    b.addEventListener("click", () => {
      state.candidateCategory = value;
      renderCandidateFilters();
      renderCandidates();
    });
    return b;
  };

  wrap.appendChild(mk("全部", 0, state.candidates.length));
  state.categories.forEach((c) => {
    const n = counts.get(c.id);
    if (n) wrap.appendChild(mk(c.name, c.id, n));
  });
  if (counts.get(-1)) wrap.appendChild(mk("未分类", -1, counts.get(-1)));
}

/* ---------------------------- 网格 ---------------------------- */

/** 搜索命中判定：片名 / 原名 / 导演 / 标签，大小写和中英文空格都容错 */
function matchesQuery(m, q) {
  if (!q) return true;
  const needle = q.trim().toLowerCase();
  if (!needle) return true;
  const hay = [m.title, m.original_title, m.director, (m.tags || []).join(" "), m.verdict]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  // 支持「闪灵」这类连续片段，也支持 "the shining" 这种按空格拆开的多词
  return hay.includes(needle) || needle.split(/\s+/).every((w) => hay.includes(w));
}

function visibleMovies() {
  return state.movies.filter((m) => {
    if (state.activeCategory === 0) {
      /* 全部 */
    } else if (state.activeCategory === -1) {
      if (m.category_id) return false;
    } else if (m.category_id !== state.activeCategory) {
      return false;
    }
    return matchesQuery(m, state.query);
  });
}
function renderGrid() {
  const grid = document.getElementById("movie-grid");
  grid.textContent = "";
  const list = visibleMovies();
  renderSearchStatus(list.length);
  if (!list.length) {
    grid.appendChild(
      el("div", {
        class: "empty",
        text: state.query
          ? `档案里没有匹配「${state.query}」的片子。`
          : "这个分类下还没有电影。",
      })
    );
    return;
  }
  list.forEach((m) => grid.appendChild(buildMovieCard(m, openMovieDetail)));
  revealStaggered(grid);
  initCursor(grid);
}

/* ---------------------------- 搜索栏 ---------------------------- */

function renderSearchStatus(hits) {
  const bar = document.getElementById("movie-search-status");
  if (!bar) return;
  const q = state.query.trim();
  bar.classList.toggle("searchbar__status--empty", Boolean(q) && hits === 0);
  if (!q) {
    bar.textContent = `档案里共 ${state.movies.length} 部，输个片名试试。`;
    return;
  }
  if (hits > 0) {
    bar.textContent = `匹配到 ${hits} 部。`;
    return;
  }
  // 没命中：本地能建档就给一条直达路径，静态站只能说明原因
  if (isStaticMode()) {
    bar.textContent = `档案里没有「${q}」。这是线上只读版，新片要回到本地后台加。`;
    return;
  }
  bar.textContent = `档案里没有「${q}」。点右边「登记一部」，直接去 TMDB 搜它。`;
}

function initSearchbar() {
  const input = document.getElementById("movie-q");
  const clear = document.getElementById("movie-q-clear");
  const addBtn = document.getElementById("movie-add");
  const form = document.getElementById("movie-search-form");
  if (!input) return;

  let timer = null;
  input.addEventListener("input", () => {
    clear.hidden = !input.value;
    // 防抖：别每敲一个字就重排整个网格
    clearTimeout(timer);
    timer = setTimeout(() => {
      state.query = input.value;
      renderGrid();
    }, 180);
  });

  form.addEventListener("submit", (e) => {
    e.preventDefault(); // 静态站没有后端，提交反而会刷新页面丢掉快照
    state.query = input.value;
    renderGrid();
  });

  clear.addEventListener("click", () => {
    input.value = "";
    clear.hidden = true;
    state.query = "";
    renderGrid();
    input.focus();
  });

  if (isStaticMode()) {
    // 线上没法写库，与其让按钮点了报错，不如直接说清楚
    addBtn.disabled = true;
    addBtn.textContent = "线上只读 · 回本地登记";
    return;
  }
  addBtn.addEventListener("click", () => {
    openEnrollDialog(input.value.trim());
  });
}

/* ---------------------------- 登记一部 ---------------------------- */
/*  看完 → 搜索 → 写评价 → 存档。
    只在动态模式（本地 / 自己的服务器）下可用：静态站没有后端可写。
    TMDB 搜索走的是 /api/admin/*，同域请求会自动带上后台会话 cookie ——
    所以只要在本机后台登录过，前台就能直接搜；没登录会拿到 401，提示去登录。 */

/** 五档点选：数值 + aria-pressed 双表达，不靠颜色单独传达状态 */
function dotPicker(max, initial, onChange) {
  let value = initial;
  const wrap = el("div", { class: "enroll__dots", role: "group" });
  const dots = [];
  for (let i = 1; i <= max; i += 1) {
    const b = el("button", {
      class: "enroll__dot",
      type: "button",
      text: String(i),
      "aria-pressed": i === value ? "true" : "false",
      "aria-label": `${i} / ${max}`,
    });
    b.addEventListener("click", () => {
      value = i;
      dots.forEach((d, idx) => d.setAttribute("aria-pressed", idx + 1 === value ? "true" : "false"));
      if (onChange) onChange(value);
    });
    dots.push(b);
    wrap.appendChild(b);
  }
  return { node: wrap, get: () => value };
}

function openEnrollDialog(initialQuery = "") {
  const wrap = el("div", { class: "detail" });

  /* ---- 第一步：从 TMDB 里搜 ---- */
  const qInput = el("input", {
    class: "searchbar__input",
    type: "search",
    value: initialQuery,
    placeholder: "片名，例如：闪灵 / The Shining",
    "aria-label": "在 TMDB 里搜索片名",
  });
  const goBtn = el("button", { class: "searchbar__add", type: "button", text: "搜索" });
  const status = el("p", { class: "enroll__hint", role: "status", "aria-live": "polite", text: "" });
  const list = el("div", { class: "tmdb__list" });

  const searchRow = el("div", { class: "enroll__field" }, [
    el("label", { class: "enroll__label", text: "1 · 在 TMDB 里找到这部片" }),
    el("div", { style: { display: "flex", gap: "8px" } }, [qInput, goBtn]),
    status,
  ]);

  /* ---- 第二步：写自己的评价（搜到片之后才展开） ---- */
  const pickedBox = el("div");
  const formBox = el("div");
  formBox.hidden = true;

  let picked = null;

  function buildForm() {
    formBox.textContent = "";
    formBox.hidden = false;

    const ratingInput = el("input", {
      type: "range",
      min: "0",
      max: "10",
      step: "0.5",
      value: "7",
      "aria-label": "我的评分，0 到 10 分",
    });
    const ratingOut = el("output", { class: "enroll__output", text: "7.0" });
    ratingInput.addEventListener("input", () => {
      ratingOut.textContent = Number(ratingInput.value).toFixed(1);
    });

    const scare = dotPicker(5, 3);
    const recommend = dotPicker(5, 3);

    const verdictInput = el("input", {
      type: "text",
      maxlength: "300",
      placeholder: "一句话结论，例如：恐怖片的天花板",
      "aria-label": "一句话短判",
    });
    const reviewInput = el("textarea", {
      placeholder: "看完想说的话。想写多长都行，不急着收尾。",
      "aria-label": "我的长评",
    });
    const watchedInput = el("input", {
      type: "date",
      value: new Date().toISOString().slice(0, 10),
      "aria-label": "观看日期",
    });
    const catSelect = el("select", { "aria-label": "分类" }, [
      el("option", { value: "", text: "先不分类" }),
      ...state.categories.map((c) => el("option", { value: String(c.id), text: c.name })),
    ]);

    const saveBtn = el("button", { class: "searchbar__add", type: "button", text: "保存进档案" });
    const cancelBtn = el("button", { class: "searchbar__clear", type: "button", text: "重选一部" });

    cancelBtn.addEventListener("click", () => {
      picked = null;
      formBox.hidden = true;
      pickedBox.textContent = "";
      qInput.focus();
    });

    saveBtn.addEventListener("click", async () => {
      if (!picked) return;
      saveBtn.disabled = true;
      saveBtn.textContent = "保存中…";
      try {
        const created = await API.post("/api/admin/movies/from-tmdb", {
          tmdb_id: picked.tmdb_id,
          category_id: catSelect.value ? Number(catSelect.value) : null,
          rating: Number(ratingInput.value),
          scare_level: scare.get(),
          recommend_level: recommend.get(),
          watched_at: watchedInput.value,
          verdict: verdictInput.value.trim(),
          review: reviewInput.value.trim(),
        });
        toast(`《${created.title}》已存进档案`);
        closeDetail();
        await reloadMovies();
      } catch (err) {
        toast(err.message, "err");
        saveBtn.disabled = false;
        saveBtn.textContent = "保存进档案";
      }
    });

    formBox.appendChild(el("h3", { text: "2 · 写下你自己的判断" }));
    formBox.appendChild(
      el("div", { class: "enroll__field" }, [
        el("label", { class: "enroll__label", text: "我的评分" }),
        el("div", { class: "enroll__range" }, [ratingInput, ratingOut]),
      ])
    );
    formBox.appendChild(
      el("div", { class: "enroll__field" }, [
        el("label", { class: "enroll__label", text: "恐怖强度（1 最温和，5 最吓人）" }),
        scare.node,
      ])
    );
    formBox.appendChild(
      el("div", { class: "enroll__field" }, [
        el("label", { class: "enroll__label", text: "推荐指数" }),
        recommend.node,
      ])
    );
    formBox.appendChild(
      el("div", { class: "enroll__field" }, [
        el("label", { class: "enroll__label", text: "一句话短判" }),
        verdictInput,
      ])
    );
    formBox.appendChild(
      el("div", { class: "enroll__field" }, [
        el("label", { class: "enroll__label", text: "我的长评" }),
        reviewInput,
      ])
    );
    formBox.appendChild(
      el("div", { class: "enroll__field" }, [
        el("label", { class: "enroll__label", text: "观看日期" }),
        watchedInput,
      ])
    );
    formBox.appendChild(
      el("div", { class: "enroll__field" }, [
        el("label", { class: "enroll__label", text: "分类" }),
        catSelect,
      ])
    );
    formBox.appendChild(el("div", { class: "enroll__actions" }, [cancelBtn, saveBtn]));
    saveBtn.focus();
  }

  function pickItem(item) {
    picked = item;
    pickedBox.textContent = "";
    const img = el("img", { alt: item.title || "海报" });
    if (item.poster_url) img.src = item.poster_url;
    else img.hidden = true;
    pickedBox.appendChild(
      el("div", { class: "enroll__picked" }, [
        img,
        el("div", {}, [
          el("div", { class: "tmdb__title", text: `${item.title}${item.year ? `（${item.year}）` : ""}` }),
          el("p", { class: "enroll__hint", text: (item.overview || "").slice(0, 120) }),
        ]),
      ])
    );
    buildForm();
  }

  async function runSearch() {
    const q = qInput.value.trim();
    if (!q) {
      status.textContent = "先输入片名。";
      return;
    }
    goBtn.disabled = true;
    status.textContent = "搜索中…";
    list.textContent = "";
    let data;
    try {
      data = await API.get(`/api/admin/tmdb/search?q=${encodeURIComponent(q)}`);
    } catch (err) {
      goBtn.disabled = false;
      status.textContent =
        err.status === 401
          ? "还没有后台会话：先打开 admin.html 登录一次，再回来搜。"
          : `搜索失败：${err.message}`;
      return;
    }
    goBtn.disabled = false;
    if (!data.configured) {
      status.textContent = "还没配置 TMDB_API_KEY，见 .env 里的说明。";
      return;
    }
    if (!data.results.length) {
      status.textContent = "TMDB 里也没有，换个写法试试（用原名更容易搜到）。";
      return;
    }
    status.textContent = `找到 ${data.total_results} 条，挑一部：`;
    data.results.forEach((item) => {
      const card = el("div", { class: "tmdb__card" });
      const img = el("img", { class: "tmdb__poster", alt: item.title || "海报" });
      if (item.poster_url) img.src = item.poster_url;
      else img.hidden = true;
      const pick = el("button", { class: "btn btn--sm btn--primary", type: "button", text: "就这部" });
      pick.addEventListener("click", () => pickItem(item));
      card.appendChild(img);
      card.appendChild(
        el("div", { class: "tmdb__info" }, [
          el("div", { class: "tmdb__title", text: `${item.title}${item.year ? `（${item.year}）` : ""}` }),
          el("div", {
            class: "enroll__hint",
            text: [item.original_title, item.tmdb_rating ? `TMDB ${item.tmdb_rating}` : ""]
              .filter(Boolean)
              .join(" · "),
          }),
        ])
      );
      card.appendChild(el("div", { class: "tmdb__actions" }, [pick]));
      list.appendChild(card);
    });
  }

  goBtn.addEventListener("click", runSearch);
  qInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      runSearch();
    }
  });

  wrap.appendChild(searchRow);
  wrap.appendChild(list);
  wrap.appendChild(pickedBox);
  wrap.appendChild(formBox);
  openDetailWith(wrap, "");

  // 带上搜索框里已有的词就直接搜一次，省一步
  if (initialQuery) runSearch();
}

/* ---------------------------- 启动 ---------------------------- */

/** 把接口返回的整份列表拆成「正式档案」和「候选片」两类 */
function splitMovies(all) {
  const list = all || [];
  state.movies = list.filter((m) => m.status !== "candidate");
  state.candidates = list.filter((m) => m.status === "candidate");
}

/** 存进一部新片之后把列表拉回来（静态站没有后端，这条只在动态模式走到） */
async function reloadMovies() {
  try {
    const [movies, categories] = await Promise.all([
      API.get("/api/movies"),
      API.get("/api/categories?kind=movie_genre"),
    ]);
    splitMovies(movies);
    state.categories = categories || [];
    renderStats();
    renderFilters();
    renderCandidateFilters();
    renderCandidates();
    renderGrid();
  } catch (err) {
    toast(`刷新失败：${err.message}`, "err");
  }
}

async function boot() {
  try {
    const [movies, categories] = await Promise.all([
      API.get("/api/movies"),
      API.get("/api/categories?kind=movie_genre"),
    ]);
    splitMovies(movies);
    state.categories = categories || [];
    renderStage();
    renderStats();
    renderFilters();
    initSearchbar();
    renderCandidateFilters();
    renderCandidates();
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
