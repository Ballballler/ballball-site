/* ========================================================================
   common.js —— 全站公共逻辑
   请求封装 / 提示 / 入场动画 / 鼠标光晕 / 滚动进度 / 详情弹层
   安全约定：所有用户输入一律用 textContent 渲染，绝不使用 innerHTML 拼接

   两种运行模式：
     1. 动态模式（本地 / 自己的服务器）：一切走 /api/*，后台、登录都在；
     2. 静态模式（GitHub Pages）：tools/export_static.py 把数据库内容内联成
        window.__SITE_DATA__，只读部分照样渲染，写操作优雅降级。
   ===================================================================== */

/** 静态导出的数据快照。本地跑 FastAPI 时是 null，页面照旧走网络请求。 */
function staticSnapshot() {
  return (typeof window !== "undefined" && window.__SITE_DATA__) || null;
}

/** 静态站点上没有后端，写入类操作一律提前挡掉。 */
function isStaticMode() {
  return Boolean(staticSnapshot());
}

const STATIC_READONLY_MSG = "这是 GitHub Pages 上的只读版本，登录与写操作只在自己的服务器上可用";

/**
 * 在快照里找 GET 路径，找不到返回 undefined（调用方继续走网络请求）。
 */
function staticLookup(path) {
  const snap = staticSnapshot();
  if (!snap) return undefined;
  if (Object.prototype.hasOwnProperty.call(snap, path)) return snap[path];
  return undefined;
}

const API = {
  async request(method, path, body) {
    const opts = {
      method,
      headers: {},
      credentials: "same-origin",
    };
    if (body !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(path, opts);
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch (_) {
      data = null;
    }
    if (!res.ok) {
      const message = (data && (data.detail || data.message)) || `请求失败（${res.status}）`;
      throw httpError(message, res.status);
    }
    return data;
  },
  /**
   * GET 优先查静态快照。命中就直接返回，不发网络请求 ——
   * GitHub Pages 上没有后端，但页面必须能渲染。
   */
  get: (p) => {
    const hit = staticLookup(p);
    if (hit !== undefined) return Promise.resolve(hit);
    return API.request("GET", p);
  },
  // GitHub Pages 上是纯静态文件，写操作没有任何后端可写 —— 提前挡掉，
  // 别让页面去 fetch 一个返回 HTML 的 404 再抛出难懂的错误。
  post: (p, b) => {
    if (isStaticMode()) return Promise.reject(httpError(STATIC_READONLY_MSG, 405));
    return API.request("POST", p, b);
  },
  put: (p, b) => {
    if (isStaticMode()) return Promise.reject(httpError(STATIC_READONLY_MSG, 405));
    return API.request("PUT", p, b);
  },
  patch: (p, b) => {
    if (isStaticMode()) return Promise.reject(httpError(STATIC_READONLY_MSG, 405));
    return API.request("PATCH", p, b);
  },
  del: (p) => {
    if (isStaticMode()) return Promise.reject(httpError(STATIC_READONLY_MSG, 405));
    return API.request("DELETE", p);
  },
  // 上传走 multipart，不能自己设 Content-Type，浏览器要拿它写 boundary
  async upload(path, formData) {
    const res = await fetch(path, {
      method: "POST",
      body: formData,
      credentials: "same-origin",
    });
    const text = await res.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch (_) {
      data = null;
    }
    if (!res.ok) {
      const message =
        (data && (data.detail || data.message)) || `上传失败（${res.status}）`;
      throw httpError(message, res.status);
    }
    return data;
  },
};

/** 带 HTTP 状态码的错误。后台靠 status 区分「没登录」和「接口真炸了」。 */
function httpError(message, status) {
  const err = new Error(message);
  err.status = status;
  return err;
}

/* ------------------------------ Toast ------------------------------ */

function toast(message, type = "ok") {
  let wrap = document.querySelector(".toast-wrap");
  if (!wrap) {
    wrap = document.createElement("div");
    wrap.className = "toast-wrap";
    document.body.appendChild(wrap);
  }
  const el = document.createElement("div");
  el.className = `toast toast--${type}`;
  el.textContent = message;
  wrap.appendChild(el);
  setTimeout(() => {
    el.classList.add("out");
    setTimeout(() => el.remove(), 320);
  }, 2600);
}

/* --------------------------- 滚动入场动画 --------------------------- */

let revealObserver = null;

function initReveal(scope = document) {
  if (!revealObserver) {
    revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
  }
  scope.querySelectorAll(".reveal:not(.in-view)").forEach((el) => {
    revealObserver.observe(el);
  });
}

/** 给动态插入的元素补上入场动画（带轻微错峰延迟） */
function revealStaggered(container, selector = ".reveal") {
  const items = container.querySelectorAll(selector);
  items.forEach((el, i) => {
    el.style.transitionDelay = `${Math.min(i * 60, 480)}ms`;
  });
  initReveal(container);
}

/* --------------------------- 页面区块装配 --------------------------- */
/* 前台每一页由若干区块拼成，显示哪些、按什么顺序由后台「页面区块」说了算。
   用法：applyPageSections("index", { about: node, "movies-preview": node, ... })
   - 接口不可用 → 什么都不做，页面按 HTML 原样渲染（不因为配置挂掉而白屏）
   - 接口返回空数组 → 这一页被后台清空了，map 里所有节点都移除
   - 排序只在同一个父节点内部重排，不会把节点搬到别的容器去 */

const SECTION_CACHE = {};

async function fetchPageSections(page) {
  if (SECTION_CACHE[page]) return SECTION_CACHE[page];
  try {
    const rows = await API.get(`/api/page-sections/${page}`);
    const list = Array.isArray(rows) ? rows : null;
    SECTION_CACHE[page] = list;
    return list;
  } catch (err) {
    console.warn(`页面区块配置拉取失败，按默认渲染：${err.message}`);
    return null;
  }
}

async function applyPageSections(page, map) {
  const rows = await fetchPageSections(page);
  if (!rows) return map; // null = 接口不可用，保持默认

  const visible = rows.filter((r) => r.visible !== false).map((r) => r.key);

  // 先摘掉被隐藏 / 被删除的
  Object.keys(map).forEach((key) => {
    const node = map[key];
    if (node && !visible.includes(key)) node.remove();
  });

  // 再按 sort_order 重排，按父节点分组，组内顺序跟随全局顺序
  const groups = new Map();
  visible.forEach((key) => {
    const node = map[key];
    if (!node || !node.parentNode) return;
    if (!groups.has(node.parentNode)) groups.set(node.parentNode, []);
    groups.get(node.parentNode).push(node);
  });
  groups.forEach((nodes, parent) => nodes.forEach((n) => parent.appendChild(n)));

  return map;
}

/* ---------------------------- 鼠标光晕 ---------------------------- */

function initCursor(scope = document) {
  scope.querySelectorAll(".glass--spot").forEach((card) => {
    card.addEventListener("pointermove", (e) => {
      const rect = card.getBoundingClientRect();
      card.style.setProperty("--mx", `${e.clientX - rect.left}px`);
      card.style.setProperty("--my", `${e.clientY - rect.top}px`);
    });
  });
}

/* --------------------------- 顶部滚动进度 --------------------------- */

function initProgress() {
  const bar = document.createElement("div");
  bar.className = "progress";
  document.body.appendChild(bar);
  const update = () => {
    const doc = document.documentElement;
    const max = doc.scrollHeight - doc.clientHeight;
    const pct = max > 0 ? (doc.scrollTop / max) * 100 : 0;
    bar.style.width = `${pct}%`;
  };
  window.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
  update();
}

/* ------------------------------ 导航 ------------------------------ */

function initNav() {
  const here = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".main-nav a, .nav__link").forEach((a) => {
    const href = a.getAttribute("href") || "";
    if (href === here || (here === "" && href === "index.html")) {
      a.classList.add("is-active");
    }
  });
}

/* ------------------------------ 工具 ------------------------------ */

function fmtDate(value) {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`;
}

/** 生成 DOM 的小助手：{tag, class, text, ...} */
function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  Object.entries(props).forEach(([k, v]) => {
    if (v === null || v === undefined || v === false) return;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else if (k === "html") throw new Error("禁止使用 html 属性，改用 text");
    else if (k === "style") Object.assign(node.style, v);
    else if (k.startsWith("on") && typeof v === "function") {
      node.addEventListener(k.slice(2).toLowerCase(), v);
    } else node.setAttribute(k, v);
  });
  (Array.isArray(children) ? children : [children]).forEach((c) => {
    if (c === null || c === undefined || c === false) return;
    node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
  });
  return node;
}

function levelDots(level, max = 5) {
  const wrap = el("span", { class: "level-dots" });
  for (let i = 1; i <= max; i += 1) {
    wrap.appendChild(el("i", { class: i <= level ? "on" : "" }));
  }
  return wrap;
}

/* --------------------------- 卡片构建（复用） --------------------------- */

function scoreRing(rating) {
  const ring = el("div", { class: "score-ring", title: `评分 ${rating}` });
  // 10 分制换算成 0-1 的圆周比例
  ring.style.setProperty("--pct", String(Math.max(0, Math.min(1, rating / 10))));
  ring.appendChild(el("span", { text: Number(rating).toFixed(1) }));
  return ring;
}

function buildMovieCard(movie, onOpen) {
  const cover = el("div", { class: "movie__cover" });
  // poster_url 是后端拼好的最终地址：TMDB CDN 优先，其次手填 poster
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
  cover.appendChild(el("span", { class: "movie__year", text: String(movie.year) }));

  const card = el(
    "article",
    {
      class: "glass glass--spot glass--shine glass--lift movie reveal",
      tabindex: "0",
      role: "button",
      "aria-label": `查看《${movie.title}》的详情`,
    },
    [
      cover,
      el("div", { class: "movie__body" }, [
        el("h3", { class: "movie__title", text: movie.title }),
        el("div", {
          class: "movie__meta",
          text: [movie.director, movie.country].filter(Boolean).join(" · "),
        }),
        el("p", { class: "movie__verdict", text: movie.verdict || "还没写短评。" }),
        el("div", { class: "movie__foot" }, [
          el("span", { text: `恐怖强度 ${movie.scare_level}/5` }),
          movie.category
            ? el("span", {
                class: "chip chip--dot",
                text: movie.category.name,
                style: { "--chip-color": movie.category.color },
              })
            : el("span", { class: "chip", text: "未分类" }),
        ]),
      ]),
    ]
  );

  // 评分环浮在封面右下角
  const ringWrap = el("div", { class: "movie__score" }, [scoreRing(movie.rating)]);
  cover.appendChild(ringWrap);

  const open = () => onOpen && onOpen(movie);
  card.addEventListener("click", open);
  card.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      open();
    }
  });
  return card;
}

const STATUS_TEXT = { idea: "构思中", demo: "有小样", released: "已完成" };

function buildWorkCard(work, onOpen, index = 0) {
  // 唱片视觉：每个作品一张可转动的黑胶。label 文字随序号变化。
  const seq = String(index + 1).padStart(2, "0");
  const recordArt = el("div", { class: "record-art" }, [
    el("div", { class: "record-stamp", text: `SOUND SKETCH / ${seq}` }),
    el("div", { class: "record" }, [
      el("div", { class: "record-label", text: `ORBIT\nSIDE ${seq}` }),
    ]),
    el("span", { class: "record-note", text: work.audio_url ? "可试听" : "AN IDEA, NOT A TRACK" }),
  ]);

  const card = el(
    "article",
    {
      class: "glass glass--spot glass--shine glass--lift work reveal",
      tabindex: "0",
      role: "button",
      "aria-label": `查看作品《${work.title}》的详情`,
    },
    [
      recordArt,
      el("div", { class: "card-body" }, [
        el("div", { class: "work__top" }, [
          el("h3", { class: "work__title", text: work.title }),
          el("span", {
            class: `status status--${work.status}`,
            text: STATUS_TEXT[work.status] || work.status,
          }),
        ]),
      el("p", { class: "work__summary", text: work.summary }),
      // 风格标签：后台从简介 / 笔记 / BPM / 调性推断后点选写入
      Array.isArray(work.tags) && work.tags.length
        ? el("div", { class: "work__tags chips" },
            work.tags.map((t) => el("span", { class: "chip", text: t }))
          )
        : null,
      el("div", { class: "work__specs" }, [
        work.bpm ? el("span", {}, [document.createTextNode("BPM "), el("b", { text: String(work.bpm) })]) : null,
        work.key_signature
          ? el("span", {}, [document.createTextNode("调性 "), el("b", { text: work.key_signature })])
          : null,
        work.category ? el("span", { class: "chip chip--dot", text: work.category.name, style: { "--chip-color": work.category.color } }) : null,
        work.audio_url
          ? el("span", {
              class: "chip",
              text: work.allow_download ? "♪ 可试听 / 可下载" : "♪ 可试听",
            })
          : null,
      ]),
      el("div", { class: "work__progress" }, [
        el("div", { class: "work__progress-row" }, [
          el("span", { text: "完成度" }),
          el("span", { text: `${work.progress}%` }),
        ]),
        (() => {
          const meter = el("div", { class: "meter" }, [
            el("div", { class: "meter__fill meter__fill--amber", style: { width: "0%" } }),
          ]);
          // 进入视口后再填充，制造生长动画
          requestAnimationFrame(() => {
            setTimeout(() => {
              meter.firstChild.style.width = `${work.progress}%`;
            }, 260);
          });
          return meter;
        })(),
      ]),
    ]),
  ]);

  const open = () => onOpen && onOpen(work);
  card.addEventListener("click", open);
  card.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      open();
    }
  });
  return card;
}

/* ========================================================================
   详情弹层 —— 全站共用，原生 <dialog>
   --------------------------------------------------------------------
   踩过的坑：以前 .modal 是个普通 div，CSS 里只给了宽高没给定位，
   JS 把它 hidden=false 之后它就作为普通块级元素渲染在页面最底部，
   看起来就是「详情掉到左下角、文字还被截断」。
   现在统一用原生 dialog：居中、遮罩、Esc 关闭、焦点回收全部交给浏览器，
   我们只负责填内容和同步 URL 深链。
   ===================================================================== */

function ensureDetailDialog() {
  let dlg = document.getElementById("detail-modal");
  // 旧版在 HTML 里写死的是 <div class="modal">，这里直接换成 dialog
  if (dlg && dlg.tagName !== "DIALOG") {
    dlg.remove();
    dlg = null;
  }
  if (!dlg) {
    dlg = el("dialog", {
      class: "modal",
      id: "detail-modal",
      "aria-label": "详情",
    });
    dlg.appendChild(el("div", { class: "modal-panel", id: "detail-panel" }));
    document.body.appendChild(dlg);
  }
  if (!dlg.dataset.wired) {
    dlg.dataset.wired = "1";
    // 点遮罩关闭：遮罩上的点击 target 就是 dialog 自己
    dlg.addEventListener("click", (e) => {
      if (e.target === dlg) dlg.close();
    });
    // 关闭时清内容、还原深链。Esc 也走这条路。
    dlg.addEventListener("close", () => {
      const panel = document.getElementById("detail-panel");
      if (panel) panel.textContent = "";
      if (/^#(movie|work)-/.test(location.hash)) {
        history.replaceState(null, "", location.pathname + location.search);
      }
    });
  }
  return dlg;
}

function closeDetail() {
  const dlg = document.getElementById("detail-modal");
  if (dlg && dlg.tagName === "DIALOG" && dlg.open) dlg.close();
}

function detailCloseButton() {
  const btn = el("button", {
    class: "modal-close",
    type: "button",
    "aria-label": "关闭详情",
    text: "×",
  });
  btn.addEventListener("click", closeDetail);
  return btn;
}

function openDetailWith(node, hash) {
  const dlg = ensureDetailDialog();
  const panel = document.getElementById("detail-panel");
  panel.textContent = "";
  panel.appendChild(node);
  panel.appendChild(detailCloseButton());
  if (!dlg.open) dlg.showModal();
  initCursor(panel);
  if (hash) history.replaceState(null, "", hash);
}

/* ------------------------------ 电影详情 ------------------------------ */

function openMovieDetail(movie) {
  const posterSrc = movie.poster_url || movie.poster;
  const poster = el("div", { class: "detail__poster" });
  if (posterSrc) {
    const img = el("img", { src: posterSrc, alt: `${movie.title} 海报`, loading: "lazy" });
    img.addEventListener("error", () => {
      img.remove();
      poster.appendChild(document.createTextNode("🎬"));
    });
    poster.appendChild(img);
  } else {
    poster.appendChild(document.createTextNode("🎬"));
  }

  const head = el("div", { class: "detail__head" }, [
    poster,
    el("div", { style: { flex: "1", minWidth: "220px" } }, [
      el("h2", { class: "detail__title", id: "detail-title", text: movie.title }),
      el("div", {
        class: "detail__meta",
        text: [
          movie.original_title,
          movie.year ? `${movie.year} 年` : "",
          movie.director ? `导演 ${movie.director}` : "",
          movie.country,
        ]
          .filter(Boolean)
          .join(" · "),
      }),
      el("div", { class: "chips", style: { marginTop: "12px" } }, [
        movie.category
          ? el("span", {
              class: "chip chip--dot",
              text: movie.category.name,
              style: { "--chip-color": movie.category.color },
            })
          : null,
        ...(movie.tags || []).map((t) => el("span", { class: "chip", text: `#${t}` })),
        movie.watched_at ? el("span", { class: "chip", text: `看于 ${movie.watched_at}` }) : null,
      ].filter(Boolean)),
    ]),
    el("div", {}, [scoreRing(movie.rating)]),
  ]);

  const scoreBox = (label, node) =>
    el("div", { class: "score-box" }, [
      el("div", { class: "score-box__label", text: label }),
      node,
    ]);

  const parts = [
    head,
    el("div", { class: "detail__scores" }, [
      scoreBox("恐怖强度", levelDots(movie.scare_level)),
      scoreBox("推荐指数", levelDots(movie.recommend_level)),
      scoreBox(
        "我的评分",
        el("div", {
          style: { fontWeight: "800", fontSize: "1.1rem", color: "var(--mint)" },
          text: `${movie.rating} / 10`,
        })
      ),
    ]),
  ];

  if (movie.overview) {
    parts.push(
      el("div", { class: "detail__section" }, [
        el("h3", { text: "剧情简介" }),
        el("p", { class: "review", text: movie.overview }),
        el("p", {
          class: "field__hint",
          text: movie.runtime
            ? `片长 ${movie.runtime} 分钟${movie.tmdb_rating ? ` · TMDB 评分 ${movie.tmdb_rating}` : ""} · 资料来自 TMDB`
            : "资料来自 TMDB",
        }),
      ])
    );
  }
  if (movie.verdict) {
    parts.push(
      el("p", {
        class: "review review--verdict",
        text: movie.verdict,
      })
    );
  }
  parts.push(
    el("div", { class: "detail__section" }, [
      el("h3", { text: "我的长评" }),
      el("p", { class: "review", text: movie.review || "这篇还没写完，先记个标题在这儿。" }),
    ])
  );

  const wrap = el("div", { class: "detail" }, parts);
  openDetailWith(wrap, `#movie-${movie.id}`);
}

/* ------------------------------ 作品详情 ------------------------------ */

function waveform() {
  const w = el("div", { class: "waveform", "aria-hidden": "true" });
  for (let i = 0; i < 26; i += 1) {
    const bar = el("i");
    bar.style.animationDelay = `${(i % 13) * 0.09}s`;
    bar.style.height = `${20 + ((i * 37) % 60)}%`;
    w.appendChild(bar);
  }
  return w;
}

function openWorkDetail(work) {
  const disc = el("div", { class: "detail__poster detail__disc" }, [
    el(
      "div",
      {
        class: "record",
        style: { height: "100%", width: "100%", animationDuration: "24s" },
      },
      [el("div", { class: "record-label", text: "ORBIT" })]
    ),
  ]);

  const head = el("div", { class: "detail__head" }, [
    disc,
    el("div", { style: { flex: "1", minWidth: "220px" } }, [
      el("h2", { class: "detail__title", id: "detail-title", text: work.title }),
      el("div", { class: "chips", style: { marginTop: "12px" } }, [
        el("span", {
          class: `status status--${work.status}`,
          text: STATUS_TEXT[work.status] || work.status,
        }),
        work.category
          ? el("span", {
              class: "chip chip--dot",
              text: work.category.name,
              style: { "--chip-color": work.category.color },
            })
          : null,
        ...(work.tags || []).map((t) => el("span", { class: "chip", text: `#${t}` })),
      ].filter(Boolean)),
    ]),
  ]);

  const parts = [
    head,
    el("div", { class: "detail__scores" }, [
      el("div", { class: "score-box" }, [
        el("div", { class: "score-box__label", text: "BPM" }),
        el("div", {
          style: { fontWeight: "800", fontSize: "1.1rem" },
          text: String(work.bpm || "—"),
        }),
      ]),
      el("div", { class: "score-box" }, [
        el("div", { class: "score-box__label", text: "调性" }),
        el("div", {
          style: { fontWeight: "800", fontSize: "1.1rem" },
          text: work.key_signature || "—",
        }),
      ]),
      el("div", { class: "score-box" }, [
        el("div", { class: "score-box__label", text: "完成度" }),
        (() => {
          const meter = el("div", { class: "meter", style: { marginTop: "10px" } }, [
            el("div", { class: "meter__fill meter__fill--amber", style: { width: "0%" } }),
          ]);
          setTimeout(() => {
            meter.firstChild.style.width = `${work.progress}%`;
          }, 200);
          return meter;
        })(),
      ]),
    ]),
  ];

  if (work.summary) {
    parts.push(
      el("p", { class: "review review--idea", text: work.summary })
    );
  }

  if (work.audio_url) {
    const player = el("audio", {
      controls: "",
      src: work.audio_url,
      preload: "metadata",
      class: "work-player",
    });
    const meta = el("p", { class: "field__hint", style: { marginTop: "8px" }, text: "" });
    const paintMeta = () => {
      const secs = Math.round(player.duration || work.audio_duration || 0);
      const size = work.audio_size ? `${(work.audio_size / 1024 / 1024).toFixed(1)} MB` : "";
      meta.textContent = [
        Number.isFinite(secs) && secs > 0
          ? `时长 ${Math.floor(secs / 60)}:${String(secs % 60).padStart(2, "0")}`
          : "",
        size,
      ]
        .filter(Boolean)
        .join(" · ");
    };
    player.addEventListener("loadedmetadata", paintMeta);
    paintMeta();

    const box = [el("h3", { text: "试听" }), player, meta];
    if (work.allow_download) {
      box.push(
        el("div", { class: "work-player__actions" }, [
          el("a", {
            class: "btn btn--sm",
            href: work.audio_url,
            download: "",
            text: "下载这首",
          }),
        ])
      );
    }
    parts.push(el("div", { class: "glass glass--pad glass--soft" }, box));
  }

  parts.push(
    el("div", { class: "detail__section" }, [
      el("h3", { text: "创作笔记" }),
      el("p", { class: "review", text: work.notes || "还没写笔记。" }),
    ])
  );

  openDetailWith(el("div", { class: "detail" }, parts), `#work-${work.id}`);
}

/* ------------------------------ 启动 ------------------------------ */

document.addEventListener("DOMContentLoaded", () => {
  initProgress();
  initNav();
  initCursor();
  initReveal();
});
