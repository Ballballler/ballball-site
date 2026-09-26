/* ========================================================================
   home.js —— 首页：自我介绍开场 + 3D 环绕场景 + 各板块精选
   数据全部走真实 API，无 mock。
   ===================================================================== */

const state = { profile: null, movies: [], works: [], journey: [], resume: [], skills: [] };

// 成长路径四个阶段的中文名，与简历页保持一致
const STAGE_LABEL = { start: "起点", turn: "转折", now: "现在", next: "下一步" };

/* ---------------------------- 3D 环绕场景 ---------------------------- */
/* 移植 personal-orbit 的 W21 场景：拖动旋转 / 滑杆开合 / 自动呼吸。 */

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
  let paused = reduced.matches, auto = true, failed = false;
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
  function canAnimate() { return !paused && !failed && !document.hidden; }
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
  function resize() {
    const r = canvas.getBoundingClientRect();
    if (!r.width || !r.height) return;
    const dpr = Math.min(devicePixelRatio || 1, 1.5);
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
      el("p", { text: "不急着定义自己。让喜欢的事，慢慢长成自己的样子。" }),
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
  return sectionWrap("about", heading(1, "A LITTLE ABOUT ME", "在这里，慢慢认识我。", p.location ? `在 ${p.location}` : ""), grid);
}

function renderMoviesPreview() {
  const top = state.movies.slice(0, 3);
  // 首页直接开详情弹层，不再跳页
  const grid = el("div", { class: "movie-grid" },
    top.map((m) => buildMovieCard(m, openMovieDetail))
  );
  const box = el("div", {}, [
    grid,
    el("div", { style: { marginTop: "22px" } }, [
      el("a", { class: "button", href: "movies.html", text: "进入恐怖电影档案 ↗" }),
    ]),
  ]);
  return sectionWrap(
    "movies-preview",
    heading(3, "NOTES FROM THE DARK", "怕黑，也想多看一眼。", "主观评价，欢迎留下不同的看法。"),
    box
  );
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
      el("a", { class: "button", href: "works.html", text: "进入音乐构思 ↗" }),
    ]),
  ]);
  return sectionWrap(
    "works-preview",
    heading(4, "SOUNDS, BEFORE THEY BECOME SONGS", "把想象，写进声音。", "先记录，再让它们慢慢成形。"),
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
          el("li", { class: "peek-path__node" }, [
            el("span", { class: "peek-path__dot", text: String(i + 1) }),
            el("div", { class: "peek-path__body" }, [
              el("span", { class: "peek-path__stage", text: STAGE_LABEL[s.stage] || s.stage }),
              el("strong", { class: "peek-path__title", text: s.title }),
              s.when ? el("span", { class: "peek-path__when", text: s.when }) : null,
            ]),
          ])
        )
      )
    : el("p", { class: "empty", text: "还没写成长路径。去后台加第一步。" });

  // 在岗的排前面，其余按开始时间倒序
  const recent = [...state.resume]
    .sort(
      (a, b) =>
        Number(!!b.current) - Number(!!a.current) ||
        String(b.start_date || "").localeCompare(String(a.start_date || ""))
    )
    .slice(0, 3);

  const list = recent.length
    ? el("ul", { class: "peek-list" },
        recent.map((r) =>
          el("li", { class: "peek-list__item" }, [
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
          ])
        )
      )
    : el("p", { class: "empty", text: "还没有经历记录。" });

  const skills = [...state.skills]
    .sort((a, b) => (b.level || 0) - (a.level || 0))
    .slice(0, 6)
    .map((s) => el("span", { class: "chip", text: `${s.name} ${s.level ?? ""}`.trim() }));

  const box = el("div", { class: "peek" }, [
    el("div", { class: "peek__col glass" }, [
      el("div", { class: "eyebrow", text: "THE PATH · 成长路径" }),
      path,
    ]),
    el("div", { class: "peek__col glass" }, [
      el("div", { class: "eyebrow", text: "MOST RECENT · 最近经历" }),
      list,
      skills.length ? el("div", { class: "chips peek__skills" }, skills) : null,
    ]),
    el("div", { class: "peek__cta" }, [
      el("a", { class: "button primary", href: "resume.html", text: "查看完整简历 ↗" }),
    ]),
  ]);

  return sectionWrap(
    "resume-preview",
    heading(2, "RESUME AT A GLANCE", "走过的路，都在简历里。", "成长路径 + 最近经历，完整版在简历页。"),
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
      profile.tagline || "在恐怖片里找灵感，在音乐里找节奏。";

    await renderSections();
    initScene();
    initReveal();
    initCursor();
  } catch (err) {
    toast(`加载失败：${err.message}`, "err");
  }
}

document.addEventListener("DOMContentLoaded", boot);
