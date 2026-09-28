/* ========================================================================
   home.js —— 首页：自我介绍开场 + 3D 环绕场景 + 各板块精选
   数据全部走真实 API，无 mock。
   ===================================================================== */

const state = { profile: null, movies: [], works: [], journey: [], resume: [], skills: [] };

// 成长路径四个阶段的中文名，与简历页保持一致
const STAGE_LABEL = { start: "起点", turn: "转折", now: "现在", next: "下一步" };

/* ---------------------------- 3D 环绕场景 ---------------------------- */
/* 移植 personal-orbit 的 W21 场景：拖动旋转 / 滑杆开合 / 自动呼吸。 */

function loadSceneRuntime() {
  const assets = [...document.querySelectorAll('script[type="application/x-ballball-lazy-scene"]')];
  return assets.reduce((chain, asset) => chain.then(() => new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = asset.src;
    script.onload = resolve;
    script.onerror = () => reject(new Error("三维场景加载失败"));
    document.body.appendChild(script);
    asset.remove();
  })), Promise.resolve());
}

function initScene() {
  const canvas = document.getElementById("scene");
  if (!canvas || !window.CreativeRuntime) return;
  const fail = (msg) => {
    const box = document.getElementById("scene-error");
    if (box) { box.textContent = msg; box.hidden = false; }
  };
  const item = window.CreativeRuntime.items().find((x) => x.id === "W21");
  if (!item) return fail("没有找到三维场景。");

  const reduced = matchMedia("(prefers-reduced-motion:reduce)");
  const sc = {
    ...window.CreativeRuntime.input(),
    duoUi: true, duoMode: "wallpaper", duoZoom: 0.85,
    duoAspect: 1.2, duoOpening: 155 / 180, dragX: -0.22, dragY: 0.1,
  };
  const params = {
    title: "保持好奇",
    subtitle: "A little room for possibility.",
    eyebrow: "BALLBALL / PERSONAL ORBIT",
    brand: "灵感星系",
    // 折叠屏壁纸：路径写在 HTML 的 data-wallpaper 上，后端会追版本号（改图即换缓存）
    image: canvas.dataset.wallpaper || "",
    accent: "#5f7f74",
    intensity: 0.32,
    seed: 42,
  };
  let paused = reduced.matches, auto = true, failed = false, sceneVisible = true;
  let time = 1, raf = 0, last = 0, drag = null;

  const fold = document.getElementById("fold");
  const foldOut = document.getElementById("fold-output");
  const autoBtn = document.getElementById("auto-fold");

  function paint() {
    if (failed || document.hidden) return;
    try {
      if (auto) sc.duoOpening = 0.6 + 0.36 * (0.5 + 0.5 * Math.cos(time * 0.48));
      sc.duoAspect = canvas.clientWidth / Math.max(1, canvas.clientHeight);
      window.CreativeRuntime.render(item, canvas, time, params, sc);
      const angle = Math.round(sc.duoOpening * 180);
      if (fold) fold.value = angle;
      if (foldOut) foldOut.textContent = angle + "°";
    } catch (e) {
      failed = true;
      fail("当前浏览器无法显示三维场景。正文、电影与音乐仍可正常浏览。");
      for (const id of ["fold", "auto-fold", "reset-scene"]) {
        const elx = document.getElementById(id);
        if (elx) elx.disabled = true;
      }
    }
  }
  function canAnimate() { return !paused && !failed && !document.hidden && sceneVisible; }
  function tick(now) {
    raf = 0;
    if (!canAnimate()) return;
    if (!last || now - last >= 1000 / 30) {
      if (last) time += Math.min(0.08, (now - last) / 1000);
      last = now;
      paint();
    }
    if (canAnimate()) raf = requestAnimationFrame(tick);
  }
  function sync() {
    cancelAnimationFrame(raf); raf = 0; last = 0;
    const t = document.getElementById("motion-toggle");
    if (t) {
      t.textContent = paused ? "恢复动画" : "暂停动画";
      t.setAttribute("aria-pressed", String(paused));
    }
    document.body.classList.toggle("paused", paused);
    if (canAnimate()) raf = requestAnimationFrame(tick);
  }
  if ("IntersectionObserver" in window) {
    const visibilityObserver = new IntersectionObserver(([entry]) => {
      sceneVisible = entry.isIntersecting;
      if (sceneVisible) paint();
      sync();
    }, { threshold: 0.05 });
    visibilityObserver.observe(canvas);
  }
  function resize() {
    const r = canvas.getBoundingClientRect();
    if (!r.width || !r.height) return;
    const dpr = Math.min(devicePixelRatio || 1, matchMedia("(max-width: 700px)").matches ? 1 : 1.5);
    canvas.width = Math.round(r.width * dpr);
    canvas.height = Math.round(r.height * dpr);
    paint();
  }

  canvas.addEventListener("pointerdown", (e) => {
    drag = { x: e.clientX, y: e.clientY, dx: sc.dragX, dy: sc.dragY };
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!drag) return;
    sc.dragX = drag.dx + (e.clientX - drag.x) / 320;
    sc.dragY = Math.max(-0.7, Math.min(0.7, drag.dy + (e.clientY - drag.y) / 320));
    paint();
  });
  canvas.addEventListener("pointerup", () => { drag = null; });
  canvas.addEventListener("pointercancel", () => { drag = null; });
  canvas.addEventListener("keydown", (e) => {
    const step = 0.12;
    if (e.key === "ArrowLeft") { sc.dragX -= step; paint(); }
    else if (e.key === "ArrowRight") { sc.dragX += step; paint(); }
    else if (e.key === "ArrowUp") { sc.dragY = Math.max(-0.7, sc.dragY - step); paint(); }
    else if (e.key === "ArrowDown") { sc.dragY = Math.min(0.7, sc.dragY + step); paint(); }
    else if (e.key === "Home") { reset(); }
    else return;
    e.preventDefault();
  });

  function reset() {
    sc.dragX = -0.22; sc.dragY = 0.1; sc.duoZoom = 0.85; sc.duoOpening = 155 / 180;
    time = 1; paint();
  }

  if (fold) {
    fold.addEventListener("input", () => {
      auto = false;
      sc.duoOpening = Number(fold.value) / 180;
      paint();
      if (autoBtn) { autoBtn.setAttribute("aria-pressed", "false"); autoBtn.textContent = "手动"; }
    });
  }
  if (autoBtn) {
    autoBtn.addEventListener("click", () => {
      auto = !auto;
      autoBtn.setAttribute("aria-pressed", String(auto));
      autoBtn.textContent = auto ? "自动" : "手动";
      paint();
    });
  }
  const resetBtn = document.getElementById("reset-scene");
  if (resetBtn) resetBtn.addEventListener("click", reset);
  const motionBtn = document.getElementById("motion-toggle");
  if (motionBtn) motionBtn.addEventListener("click", () => { paused = !paused; sync(); });

  reduced.addEventListener("change", () => { paused = reduced.matches; sync(); });
  window.addEventListener("resize", resize);
  resize();
  sync();
}

/* ---------------------------- 板块渲染 ---------------------------- */

function heading(num, en, title, desc) {
  return el("div", { class: "section-heading reveal" }, [
    el("div", {}, [
      el("div", { class: "eyebrow" }, [
        el("span", { class: "section-number", text: String(num).padStart(2, "0") }),
        document.createTextNode(en),
      ]),
      el("h2", { text: title }),
    ]),
    desc ? el("p", { text: desc }) : null,
  ]);
}

function sectionWrap(id, head, body) {
  return el("section", { class: "section", id }, [el("div", { class: "shell" }, [head, body])]);
}

function renderAbout(p) {
  const grid = el("div", { class: "about-grid" }, [
    el("p", { class: "about-copy", text: p.bio || p.tagline || "这段介绍还在生长。" }),
    el("div", { class: "about-orbits glass" }, [
      el("div", { class: "eyebrow", text: "ROOM FOR POSSIBILITY" }),
      el("div", { class: "big-word", text: "Stay curious." }),
      el("p", { text: "在这里记录工作、电影与音乐，也把灵感慢慢做成作品。" }),
      el("div", { class: "about-highlights" },
        (p.highlights || []).slice(0, 4).map((h) =>
          el("span", { class: "chip", text: `${h.icon || ""} ${h.title || ""}`.trim() })
        )
      ),
      el("div", { class: "about-links" },
        (p.links || []).slice(0, 4).map((l) =>
          el("a", { class: "chip", href: l.url, target: "_blank", rel: "noopener", text: l.label || l.url })
        )
      ),
    ]),
  ]);
  return sectionWrap("about", heading(1, "A LITTLE ABOUT ME", "工作之外，也有自己的小宇宙。", p.location ? `生活在 ${p.location}` : ""), grid);
}

function renderMoviesPreview() {
  // 首页这块是「精选」，必须和电影页看到的同一批：
  //  1. candidate 是后台的待看清单（没评分、没短评），电影页会过滤掉它们，
  //     首页要是照单全收，就会出现「首页有、详情页找不到」的错位
  //  2. 再按评分挑最值得看的 3 部，而不是抓数据库里排最前的 3 条
  const watched = state.movies.filter((m) => m.status !== "candidate");
  const top = watched.slice().sort(byScoreDesc).slice(0, 3);

  if (!top.length) {
    return sectionWrap(
      "movies-preview",
      heading(3, "NOTES FROM THE DARK", "每一次观影，都值得留下。", ""),
      el("p", { class: "muted", text: "观影记录还在累积中。写下第一篇短评后，它就会出现在这里。" })
    );
  }

  // 首页直接开详情弹层，不再跳页
  const grid = el("div", { class: "movie-grid" },
    top.map((m) => buildMovieCard(m, openMovieDetail))
  );
  const total = watched.length;
  const box = el("div", {}, [
    grid,
    el("div", { style: { marginTop: "22px" } }, [
      el("a", {
        class: "button",
        href: "movies.html",
        text: `浏览全部 ${total} 部观影记录 ↗`,
      }),
    ]),
  ]);
  return sectionWrap(
    "movies-preview",
    heading(
      3,
      "NOTES FROM THE DARK",
      "每一次观影，都值得留下。",
      `从 ${total} 部已看影片中选出评分最高的 ${top.length} 部。每个分数都是当下最真实的感受。`
    ),
    box
  );
}

/** 评分降序；同分按标题稳定排序，避免每次刷新顺序乱跳 */
function byScoreDesc(a, b) {
  const diff = (b.rating || 0) - (a.rating || 0);
  if (diff) return diff;
  return String(a.title || "").localeCompare(String(b.title || ""), "zh-Hans-CN");
}

function renderWorksPreview() {
  const top = state.works.slice(0, 3);
  // 首页直接开详情弹层，不再跳页
  const grid = el("div", { class: "music-grid" },
    top.map((w, i) => buildWorkCard(w, openWorkDetail, i))
  );
  const box = el("div", {}, [
    grid,
    el("div", { style: { marginTop: "22px" } }, [
      el("a", { class: "button", href: "works.html", text: "听听创作片段 ↗" }),
    ]),
  ]);
  return sectionWrap(
    "works-preview",
    heading(4, "SOUNDS, BEFORE THEY BECOME SONGS", "让一段旋律，慢慢长成作品。", "从灵感片段到完整作品，把每一步都收好。"),
    box
  );
}

/* ---------------------------- 简历速览 ---------------------------- */
/* 首页此前跳过了简历这一块，访客只能从顶部导航进。
   这里补一个摘要：成长路径前几级 + 最近经历 + 技能亮点，末尾给一个直达按钮。 */

function renderResumePreview() {
  const steps = state.journey.slice(0, 4);
  const path = steps.length
    ? el("ol", { class: "peek-path" },
        steps.map((s, i) =>
          el("li", { class: "peek-path__node reveal", style: { transitionDelay: `${i * 75}ms` } }, [
            el("span", { class: "peek-path__dot", text: String(i + 1) }),
            el("div", { class: "peek-path__body" }, [
              el("span", { class: "peek-path__stage", text: STAGE_LABEL[s.stage] || s.stage }),
              el("strong", { class: "peek-path__title", text: s.title }),
              s.when ? el("span", { class: "peek-path__when", text: s.when }) : null,
            ]),
          ])
        )
      )
    : el("p", { class: "empty", text: "成长记录正在整理中。" });

  // 在岗的排前面，其余按开始时间倒序
  const recent = [...state.resume]
    .sort(
      (a, b) =>
        Number(!!b.current) - Number(!!a.current) ||
        String(b.start_date || "").localeCompare(String(a.start_date || ""))
    )
    .slice(0, 3);

  const current = recent.find((item) => item.kind === "work" && item.current);
  const list = recent.length
    ? el("ul", { class: "peek-list" },
        recent.map((r, index) =>
          el("li", { class: "peek-list__item reveal", style: { transitionDelay: `${index * 80}ms` } }, [
            el("div", { class: "peek-list__row" }, [
              el("strong", { text: r.title }),
              el("span", {
                class: "peek-list__when",
                text: `${r.start_date || "—"} — ${r.current ? "至今" : r.end_date || "—"}`,
              }),
            ]),
            (r.role || r.org)
              ? el("span", { class: "peek-list__org", text: [r.role, r.org].filter(Boolean).join(" · ") })
              : null,
            r.summary ? el("p", { class: "peek-list__sum", text: r.summary }) : null,
            r === current && r.highlights?.length
              ? el("ul", { class: "peek-list__highlights" }, r.highlights.slice(0, 2).map((item) => el("li", { text: item })))
              : null,
          ])
        )
      )
    : el("p", { class: "empty", text: "新的经历，很快会在这里出现。" });

  const skills = [...state.skills]
    .sort((a, b) => (b.level || 0) - (a.level || 0))
    .slice(0, 6)
    .map((s) => el("span", { class: "chip", text: `${s.name} ${s.level ?? ""}`.trim() }));

  const evidence = (current?.highlights || []).join(" ");
  const metricPatterns = [
    { pattern: /(\d+\+?)\s*项检查点/, suffix: "项", label: "标准化检查点" },
    { pattern: /(\d+(?:\.\d+)?%)\s*以上/, suffix: "+", label: "信息准确率" },
    { pattern: /返工率降\s*(\d+%)/, suffix: "", label: "返工率下降" },
  ];
  const metrics = metricPatterns
    .map(({ pattern, suffix, label }) => {
      const match = evidence.match(pattern);
      return match ? { value: `${match[1]}${suffix}`, label } : null;
    })
    .filter(Boolean);

  const box = el("div", { class: "peek-wrap" }, [
    metrics.length
      ? el("div", { class: "peek-metrics", "aria-label": "近期工作成果" }, metrics.map((metric, index) =>
          el("div", { class: "peek-metric glass reveal", style: { transitionDelay: `${index * 85}ms` } }, [
            el("strong", { text: metric.value }),
            el("span", { text: metric.label }),
          ])
        ))
      : null,
    el("div", { class: "peek" }, [
    el("div", { class: "peek__col glass reveal" }, [
      el("div", { class: "eyebrow", text: "THE PATH · 成长路径" }),
      path,
    ]),
    el("div", { class: "peek__col peek__col--experience glass reveal" }, [
      el("div", { class: "eyebrow", text: "MOST RECENT · 最近经历" }),
      list,
      skills.length ? el("div", { class: "chips peek__skills" }, skills) : null,
    ]),
    el("div", { class: "peek__cta" }, [
      el("a", { class: "button primary", href: "resume.html", text: "查看完整简历 ↗" }),
    ]),
    ]),
  ]);

  return sectionWrap(
    "resume-preview",
    heading(2, "RESUME AT A GLANCE", "走过的路，都算数。", "从关键转折到近期工作，看看经历如何汇成今天的能力。"),
    box
  );
}

async function renderSections() {
  const host = document.getElementById("sections");
  host.textContent = "";
  // 四个板块的显示与顺序交给后台「页面区块」决定
  const map = {
    about: renderAbout(state.profile),
    "resume-preview": renderResumePreview(),
    "movies-preview": renderMoviesPreview(),
    "works-preview": renderWorksPreview(),
  };
  Object.values(map).forEach((node) => host.appendChild(node));
  await applyPageSections("index", map);
  const contact = document.getElementById("contact-text");
  if (contact) contact.textContent = state.profile.email ? `可以写信给我：${state.profile.email}` : "下一个灵感，正在路上。";
}

/* ---------------------------- 启动 ---------------------------- */

async function boot() {
  try {
    // /api/resume 是聚合接口，一次给齐 journey / items / skills
    const [profile, movies, works, resume] = await Promise.all([
      API.get("/api/profile"),
      API.get("/api/movies"),
      API.get("/api/works"),
      API.get("/api/resume"),
    ]);
    state.profile = profile;
    state.movies = movies || [];
    state.works = works || [];
    state.journey = (resume && resume.journey) || [];
    state.resume = (resume && resume.items) || [];
    state.skills = (resume && resume.skills) || [];

    document.getElementById("profile-name").textContent = profile.name || "Ballball";
    document.getElementById("profile-intro").textContent =
      profile.tagline || "把喜欢的事认真做下去：看电影、写音乐，也把想法变成能用的工具。";

    await renderSections();
    const sceneAssets = [...document.querySelectorAll('script[type="application/x-ballball-lazy-scene"]')];
    if (sceneAssets.length) {
      const load = () => loadSceneRuntime().then(initScene).catch(() => {
        const box = document.getElementById("scene-error");
        if (box) { box.textContent = "三维场景暂时无法加载，正文仍可正常浏览。"; box.hidden = false; }
      });
      if ("requestIdleCallback" in window) requestIdleCallback(load, { timeout: 1800 });
      else setTimeout(load, 300);
    }
    initReveal();
    initCursor();
  } catch (err) {
    toast(`加载失败：${err.message}`, "err");
  }
}

document.addEventListener("DOMContentLoaded", boot);
