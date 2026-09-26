/* ========================================================================
   resume.js —— 简历页：自我介绍开场、3D 技能球、技能条、时间轴
   ===================================================================== */

const KIND_LABEL = {
  work: "工作",
  education: "教育",
  project: "项目",
  award: "获奖",
};

const state = {
  profile: null,
  items: [],
  skills: [],
  journey: [],
  filter: "all",
  sphere: null,
};

/* ---------------------------- 开场：自我介绍 ---------------------------- */

function renderIntro(profile) {
  document.getElementById("resume-name").textContent = profile.name || "Ballball";
  document.getElementById("resume-headline").textContent =
    profile.headline || profile.tagline || "";
  // 开场用 bio 的开头：首段太短就带上第二段，保证开场有分量又不冗长
  const paras = (profile.bio || "").trim().split(/\n\s*\n/).filter(Boolean);
  let intro = paras[0] || "";
  if (intro.length < 40 && paras[1]) intro = `${paras[0]}\n\n${paras[1]}`;
  document.getElementById("resume-intro").textContent = intro;
  document.title = `简历 · ${profile.name || "Ballball"}`;

  const contacts = document.getElementById("resume-contacts");
  if (!contacts) return;
  if (profile.location) {
    contacts.appendChild(el("span", { class: "chip", text: `📍 ${profile.location}` }));
  }
  if (profile.email) {
    contacts.appendChild(el("span", { class: "chip", text: `✉️ ${profile.email}` }));
  }
  (profile.links || []).forEach((l) => {
    if (!l || !l.url) return;
    contacts.appendChild(
      el("a", {
        class: "chip",
        href: l.url,
        target: l.url.startsWith("http") ? "_blank" : "_self",
        rel: l.url.startsWith("http") ? "noopener noreferrer" : "",
        text: `🔗 ${l.label || l.url}`,
      })
    );
  });
}

/* ---------------------------- 技能球 + 技能条 ---------------------------- */

function renderSkills(skills) {
  // 3D 球
  const host = document.getElementById("skill-sphere");
  if (host && skills.length) {
    const tags = skills.map((s) => ({
      text: s.name,
      level: s.level,
      color: s.color || "#00b8d4",
    }));
    const size = window.innerWidth < 640 ? 120 : 150;
    state.sphere = createTagSphere(host, tags, { radius: size });
  }

  // 分组技能条
  const wrap = document.getElementById("skill-bars");
  if (!wrap) return;
  wrap.textContent = "";
  if (!skills.length) {
    wrap.appendChild(el("p", { class: "empty", text: "还没有技能，去后台加几条。" }));
    return;
  }

  const groups = new Map();
  skills.forEach((s) => {
    const key = s.group || "其他";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(s);
  });

  groups.forEach((list, name) => {
    const box = el("div", { class: "skill-group" });
    box.appendChild(el("div", { class: "skill-group__title", text: name }));
    list.forEach((s) => {
      const meter = el("div", { class: "skill-row__meter" }, [
        el("div", { class: "skill-row__fill", style: { width: "0%" } }),
      ]);
      meter.style.setProperty("--skill-color", s.color || "#00b8d4");
      box.appendChild(
        el("div", { class: "skill-row", title: s.note || "" }, [
          el("div", { class: "skill-row__name", text: s.name }),
          meter,
          el("div", { class: "skill-row__val", text: `${s.level}` }),
        ])
      );
      // 进入视口后再生长
      requestAnimationFrame(() => {
        setTimeout(() => {
          meter.firstChild.style.width = `${s.level}%`;
        }, 200);
      });
    });
    wrap.appendChild(box);
  });
}

/* ---------------------------- 时间轴 ---------------------------- */

function renderFilters() {
  const wrap = document.getElementById("resume-filters");
  if (!wrap) return;
  wrap.textContent = "";
  const counts = { all: state.items.length };
  state.items.forEach((i) => {
    counts[i.kind] = (counts[i.kind] || 0) + 1;
  });

  const mk = (key, label) => {
    const b = el("button", {
      class: "filter" + (state.filter === key ? " is-active" : ""),
      type: "button",
      text: `${label} (${counts[key] || 0})`,
      "aria-pressed": state.filter === key ? "true" : "false",
    });
    b.addEventListener("click", () => {
      state.filter = key;
      renderFilters();
      renderTimeline();
    });
    return b;
  };

  wrap.appendChild(mk("all", "全部"));
  Object.keys(KIND_LABEL).forEach((k) => {
    if (counts[k]) wrap.appendChild(mk(k, KIND_LABEL[k]));
  });
}

function dateRange(item) {
  const start = item.start_date || "";
  const end = item.current ? "至今" : item.end_date || "";
  if (!start && !end) return "";
  return `${start} — ${end}`.replace(/\s—\s$/, "");
}

function renderTimeline() {
  const wrap = document.getElementById("resume-timeline");
  if (!wrap) return;
  wrap.textContent = "";

  const list = state.items.filter(
    (i) => state.filter === "all" || i.kind === state.filter
  );

  if (!list.length) {
    wrap.appendChild(el("p", { class: "empty", text: "这个分类下还没有条目。" }));
    return;
  }

  list.forEach((item) => {
    const card = el(
      "div",
      {
        class:
          "glass glass--pad glass--spot holo tl-card reveal" +
          (item.current ? " tl-item--current-host" : ""),
      },
      [
        el("div", { class: "tl-card__top" }, [
          el("div", {}, [
            el("div", { class: "tl-card__title", text: item.title }),
            el("div", { class: "tl-card__org" }, [
              document.createTextNode(item.org || ""),
              item.role ? el("span", { text: ` · ${item.role}` }) : null,
              item.location ? el("span", { text: ` · ${item.location}` }) : null,
            ]),
          ]),
          el("div", { class: "tl-card__date mono", text: dateRange(item) }),
        ]),
        item.summary ? el("p", { class: "tl-card__summary", text: item.summary }) : null,
        item.highlights && item.highlights.length
          ? el(
              "ul",
              { class: "tl-card__list" },
              item.highlights.map((h) => el("li", { text: h }))
            )
          : null,
        el("div", { class: "tl-card__foot" }, [
          el("span", {
            class: `kind-badge kind-badge--${item.kind}`,
            text: KIND_LABEL[item.kind] || item.kind,
          }),
          ...(item.tags || []).map((t) => el("span", { class: "chip", text: `#${t}` })),
          item.link
            ? el("a", {
                class: "chip",
                href: item.link,
                target: "_blank",
                rel: "noopener noreferrer",
                text: "查看 ↗",
              })
            : null,
        ].filter(Boolean)),
      ].filter(Boolean)
    );

    const node = el("div", {
      class: "tl-item" + (item.current ? " tl-item--current" : ""),
    });
    node.appendChild(card);
    wrap.appendChild(node);
  });

  revealStaggered(wrap);
  initCursor(wrap);
}

/* ---------------------------- 成长路径 ---------------------------- */

const STAGE_TEXT = {
  start: "起点",
  turn: "转折点",
  now: "现在",
  next: "下一步",
};

function renderJourney() {
  const wrap = document.getElementById("journey-path");
  if (!wrap) return;
  wrap.textContent = "";

  if (!state.journey.length) {
    wrap.appendChild(
      el("p", { class: "empty", text: "还没写成长路径。去后台「成长路径」里加第一步。" })
    );
    return;
  }

  state.journey.forEach((step, idx) => {
    // 阶梯：--i 控制每一级向右缩进，data-stage 决定这一级的颜色
    const node = el("article", { class: "journey__step reveal" });
    node.dataset.stage = step.stage;
    node.style.setProperty("--i", String(idx));

    node.appendChild(el("div", { class: "journey__dot", text: String(idx + 1) }));

    node.appendChild(
      el("div", { class: "journey__head" }, [
        el("span", { class: "journey__stage", text: STAGE_TEXT[step.stage] || step.stage }),
        el("h3", { class: "journey__title", text: step.title }),
        step.when ? el("span", { class: "journey__when", text: step.when }) : null,
      ])
    );

    // 三问：卡在哪 / 怎么走 / 得到了什么
    const qa = (label, text) =>
      text
        ? el("div", { class: "journey__qa" }, [
            el("span", { class: "journey__label", text: label }),
            el("p", { class: "journey__text", text }),
          ])
        : null;

    node.appendChild(
      el("div", { class: "journey__answers" }, [
        qa("卡在哪", step.stuck),
        qa("怎么走的", step.action),
        qa("得到了什么", step.gained),
      ].filter(Boolean))
    );

    if (step.evidence || step.link) {
      const ev = el("p", { class: "journey__evidence" }, []);
      if (step.link) {
        const a = el("a", { href: step.link, target: "_blank", rel: "noopener", text: step.evidence || step.link });
        ev.appendChild(el("span", { text: "佐证：" }));
        ev.appendChild(a);
      } else {
        ev.textContent = `佐证：${step.evidence}`;
      }
      node.appendChild(ev);
    }

    wrap.appendChild(node);
  });

  revealStaggered(wrap);
  initCursor(wrap);
}

/* ---------------------------- 启动 ---------------------------- */

async function boot() {
  try {
    const [profile, resume] = await Promise.all([
      API.get("/api/profile"),
      API.get("/api/resume"),
    ]);
    state.profile = profile;
    state.items = resume.items || [];
    state.skills = resume.skills || [];
    // 成长路径是这一页的主角，先于履历渲染
    state.journey = resume.journey || [];

    renderIntro(profile);
    renderJourney();
    renderSkills(state.skills);
    renderFilters();
    renderTimeline();
    // 区块的显示与顺序由后台「页面区块」决定
    await applyPageSections("resume", {
      hero: document.getElementById("resume-hero"),
      journey: document.getElementById("journey"),
      skills: document.getElementById("skills"),
      timeline: document.getElementById("timeline"),
    });
    initReveal();
    initCursor();
  } catch (err) {
    toast(`加载失败：${err.message}`, "err");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn-print");
  if (btn) {
    btn.addEventListener("click", () => window.print());
  }
  boot();
});

// 打印前把技能球销毁掉，避免打印时残留动画帧
window.addEventListener("beforeprint", () => {
  if (state.sphere) {
    state.sphere.destroy();
    state.sphere = null;
  }
});
