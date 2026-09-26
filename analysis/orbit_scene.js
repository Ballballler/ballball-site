
/* Original procedural website scenes. Verified with Three.js 0.182.0; no external assets.
 * Host owns renderer, sizing, input, DOM, RAF and disposal. Time is in seconds.
 * Every update derives the complete visible state from t/params/input, never delta time.
 */
(function() {
    "use strict";
    Math.PI;
    const templates = [];
    // W08: four real depth layers, charts and a spatial connection graph; host supplies real UI.
    window.CreativeWebsiteDesign = templates;
})();

/* Original interactive website studies. Canvas thumbnails and real DOM share preset data. */ (() => {
    "use strict";
    const TAU = Math.PI * 2, esc = v => String(v).replace(/[&<>"']/g, c => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    }[c]));
    const defs = [];
    function art(c, x, y, w, h, t, n = 0, accent = "#819782", mode = "abstract") {
        c.save();
        c.translate(x, y);
        c.scale(w / 600, h / 420);
        c.beginPath();
        c.rect(0, 0, 600, 420);
        c.clip();
        const palettes = [ [ "#c5c7b9", "#626f61", "#e1ddcf" ], [ "#b9cbc9", "#3e5b54", "#e1d3b9" ], [ "#c4aea0", "#735546", "#e5d5c2" ], [ "#a3acb9", "#4c5b6c", "#e0e0d7" ] ], p = palettes[n % 4];
        c.fillStyle = p[0];
        c.fillRect(0, 0, 600, 420);
        if (mode === "landscape") {
            const g = c.createLinearGradient(0, 0, 0, 420);
            g.addColorStop(0, "#b6ccce");
            g.addColorStop(.6, "#dbe0cf");
            g.addColorStop(1, "#8da9a5");
            c.fillStyle = g;
            c.fillRect(0, 0, 600, 420);
            for (let layer = 0; layer < 5; layer++) {
                c.beginPath();
                c.moveTo(0, 420);
                for (let k = 0; k <= 90; k++) {
                    const xx = k / 90 * 600, yy = 150 + layer * 46 + Math.sin(k * .06 + layer * 2 + n) * 48 + Math.sin(k * .16 + layer) * 18;
                    c.lineTo(xx, yy);
                }
                c.lineTo(600, 420);
                c.closePath();
                c.fillStyle = [ "#94aaa1", "#819b8e", "#668878", "#456d5c", "#244f42" ][layer];
                c.fill();
            }
            c.fillStyle = "#ece3c7";
            c.beginPath();
            c.arc(435, 79, 31, 0, TAU);
            c.fill();
        } else if (mode === "architecture") {
            c.fillStyle = p[2];
            c.fillRect(0, 300, 600, 120);
            for (let k = 0; k < 7; k++) {
                const xx = 75 + k * 62, yy = 80 + Math.sin(k * .7 + n) * 25;
                c.fillStyle = k % 2 ? p[2] : p[1];
                c.fillRect(xx, yy, 54, 240 - yy * .2);
                c.fillStyle = "#ffffff33";
                c.fillRect(xx + 3, yy, 6, 200);
            }
            c.fillStyle = accent;
            c.fillRect(125, 326, 340, 4);
        } else if (mode === "record") {
            c.fillStyle = "#33382f";
            c.fillRect(0, 0, 600, 420);
            c.translate(300, 210);
            c.rotate(t * .35 + n);
            for (let r = 172; r > 0; r -= 2) {
                c.strokeStyle = r % 6 === 0 ? "#747a65" : "#121810";
                c.lineWidth = 1;
                c.beginPath();
                c.arc(0, 0, r, 0, TAU);
                c.stroke();
            }
            c.fillStyle = accent;
            c.beginPath();
            c.arc(0, 0, 67, 0, TAU);
            c.fill();
            c.fillStyle = "#263128";
            c.font = "600 15px Arial";
            c.textAlign = "center";
            c.fillText("SIDE / A", 0, -13);
            c.beginPath();
            c.arc(0, 0, 6, 0, TAU);
            c.fill();
        } else {
            c.translate(300, 205);
            c.rotate(Math.sin(t * .35 + n) * .11);
            c.fillStyle = "#0002";
            c.beginPath();
            c.ellipse(20, 151, 146, 19, 0, 0, TAU);
            c.fill();
            for (let k = 13; k >= 0; k--) {
                const g = c.createLinearGradient(-170, 0, 170, 0);
                g.addColorStop(0, p[1]);
                g.addColorStop(.42, p[2]);
                g.addColorStop(.7, accent);
                g.addColorStop(1, p[1]);
                c.strokeStyle = g;
                c.lineWidth = 13;
                c.beginPath();
                c.ellipse(0, k * 8 - 55, 140 - k * 2, 60, Math.sin(t * .22 + n) * .15, 0, TAU);
                c.stroke();
            }
        }
        c.restore();
    }
    function txt(c, v, x, y, size, col, max = 1100, font = "Arial") {
        c.fillStyle = col;
        c.font = "500 " + size + "px " + font;
        c.fillText(v, x, y, max);
    }
    function thumb(c, t, p = {}, input = {}) {
        const d = this.site, a = {
            ...this.defaults,
            ...p
        }, kind = d.kind;
        const bg = d.bg, ink = d.ink, accent = a.accent;
        c.fillStyle = bg;
        c.fillRect(0, 0, 1200, 675);
        txt(c, "STUDIO / " + this.id.slice(1), 42, 42, 16, ink);
        txt(c, "WORK         ABOUT         EXPLORE ↗", 830, 42, 12, ink, 330);
        c.strokeStyle = ink + "25";
        c.beginPath();
        c.moveTo(42, 65);
        c.lineTo(1158, 65);
        c.stroke();
        if (kind === "portfolio") {
            txt(c, a.title, 42, 169, 85, ink);
            txt(c, a.subtitle, 44, 208, 16, ink);
            for (let k = 0; k < 4; k++) {
                const x = 44 + k * 350 - Math.sin(t * .35) * 48;
                art(c, x, 252, 324, 302, t, k, accent);
                txt(c, [ "FORM", "MONO", "SOLACE", "NORTH" ][k], x, 591, 17, ink);
            }
        } else if (kind === "editorial" || kind === "magazine") {
            txt(c, a.title, 44, 220, kind === "editorial" ? 91 : 78, ink, 615, "Georgia");
            txt(c, a.subtitle, 48, 288, 17, ink, 550);
            art(c, 728, 112, 360, 440, t, kind === "editorial" ? 0 : 2, accent);
            txt(c, "READ THE STORY  ↗", 48, 526, 18, ink);
            txt(c, "A journal of ideas, objects and everyday life.", 48, 576, 15, ink, 590);
        } else if (kind === "gallery") {
            txt(c, a.title, 44, 146, 63, ink);
            for (let k = 0; k < 5; k++) {
                const w = 195 + Math.sin(t * .5 + k) * 25;
                art(c, 44 + k * 224, 205 + Math.sin(t * .5 + k) * 32, w, 320, t, k, accent);
            }
            txt(c, "01—05     MOVE TO EXPLORE", 44, 610, 14, ink);
        } else if (kind === "saas") {
            txt(c, a.title, 160, 188, 72, ink, 930);
            txt(c, a.subtitle, 238, 232, 19, ink);
            for (let k = 0; k < 3; k++) {
                const x = 118 + k * 325, y = 320 + Math.sin(t * .7 + k) * 13;
                c.fillStyle = k === 1 ? accent : "#fff";
                c.beginPath();
                c.roundRect(x, y, 304, 248, 15);
                c.fill();
                txt(c, [ "Overview", "Projects", "Insights" ][k], x + 25, y + 42, 19, k === 1 ? "#fff" : ink);
                for (let j = 0; j < 7; j++) {
                    c.fillStyle = k === 1 ? "#ffffffaa" : accent + "88";
                    const h = 40 + (Math.sin(j * 1.5 + t) + 1) * 42;
                    c.fillRect(x + 28 + j * 35, y + 204 - h, 22, h);
                }
            }
        } else if (kind === "travel") {
            art(c, 0, 67, 1200, 608, t, 1, accent, "landscape");
            txt(c, a.title, 53, 249, 100, "#f6f2e6", 1080, "Georgia");
            txt(c, a.subtitle, 59, 300, 21, "#f6f2e6");
            txt(c, "EXPLORE THE COLLECTION  ↗", 60, 567, 18, "#f6f2e6");
        } else if (kind === "music") {
            txt(c, a.title, 42, 217, 87, ink, 510);
            txt(c, a.subtitle, 46, 268, 18, ink, 480);
            art(c, 600, 98, 545, 467, t, 0, accent, "record");
            txt(c, "LATEST RELEASES  ↗", 46, 545, 20, ink);
        } else if (kind === "architecture") {
            txt(c, a.title, 42, 160, 65, ink);
            for (let k = 0; k < 4; k++) {
                const y = 223 + k * 85;
                txt(c, "0" + (k + 1), 44, y, 15, ink);
                txt(c, [ "Courtyard House", "Quiet Pavilion", "Open Library", "Garden Studio" ][k], 110, y, 32, ink, 550);
                c.strokeStyle = ink + "30";
                c.beginPath();
                c.moveTo(44, y + 26);
                c.lineTo(670, y + 26);
                c.stroke();
            }
            art(c, 727, 215, 420, 347, t, 2, accent, "architecture");
        } else if (kind === "developer") {
            txt(c, a.title, 46, 225, 82, ink, 605);
            txt(c, a.subtitle, 50, 281, 18, ink, 560);
            c.fillStyle = "#1a262b";
            c.beginPath();
            c.roundRect(725, 140, 422, 375, 15);
            c.fill();
            for (let k = 0; k < 9; k++) txt(c, [ "$ create something", "", "const idea = {", "  clarity: true,", "  curiosity: Infinity,", "};", "", "> Ready in 0.8s", "_" ][k], 753, 185 + k * 32, 16, k > 6 ? accent : "#8b9d9d", 370, "monospace");
            txt(c, "START BUILDING  ↗", 50, 511, 20, ink);
        } else if (kind === "exhibition") {
            txt(c, a.title, 42, 209, 140, ink, 1080);
            c.save();
            c.translate(600, 400);
            c.rotate(t * .1);
            for (let k = 0; k < 20; k++) {
                c.rotate(TAU / 20);
                c.strokeStyle = ink;
                c.lineWidth = 1.5;
                c.strokeRect(-200, -90, 400, 180);
            }
            c.restore();
            txt(c, "18 OCT — 24 NOV      GALLERY 02", 44, 624, 16, ink);
        } else if (kind === "material") {
            txt(c, a.title, 46, 176, 76, ink, 750, "Georgia");
            for (let k = 0; k < 3; k++) {
                art(c, 44 + k * 380, 236, 355, 305, t, k + 1, accent);
                txt(c, [ "Stone / 01", "Paper / 02", "Wood / 03" ][k], 44 + k * 380, 579, 19, ink);
            }
        } else {
            txt(c, a.title, 44, 160, 73, ink);
            txt(c, "2026", 810, 166, 93, accent);
            for (let k = 0; k < 10; k++) {
                const h = 70 + k * 23 + Math.sin(t * .6 + k) * 10;
                c.fillStyle = k === 8 ? ink : accent;
                c.fillRect(62 + k * 106, 555 - h, 72, h);
            }
            txt(c, "12 MONTHS       48 PROJECTS       ONE DIRECTION", 44, 625, 16, ink);
        }
    }
    const items = defs.map(([id, name, kind, bg, ink, accent, title, subtitle]) => ({
        id: id,
        name: name,
        family: "website",
        site: {
            kind: kind,
            bg: bg,
            ink: ink
        },
        category: kind,
        duration: 12,
        accent: accent,
        description: subtitle,
        interaction: "Scroll, open projects, and use the page controls.",
        draw: thumb,
        defaults: {
            title: title,
            subtitle: subtitle,
            accent: accent,
            intensity: .6,
            seed: 42
        }
    }));
    const style = `\n.site-page{--paper:#eee;--ink:#222;--accent:#859684;background:var(--paper);color:var(--ink);height:100%;overflow:auto;overscroll-behavior:contain;font:14px/1.5 Arial,"PingFang SC",sans-serif;container-type:inline-size;scroll-behavior:smooth;position:relative}.site-page *{box-sizing:border-box}.site-page button{font:inherit;color:inherit;cursor:pointer;background:transparent;border:0;border-radius:0}.site-page button:focus-visible{outline:2px solid var(--accent);outline-offset:3px}.site-top{height:64px;padding:0 4%;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid color-mix(in srgb,var(--ink) 15%,transparent)}.site-brand{font-weight:650;letter-spacing:.04em}.site-nav{display:flex;gap:22px;font-size:11px}.site-body{padding:48px 4% 30px}.site-eyebrow{font-size:10px;letter-spacing:.15em;margin-bottom:18px}.site-page h1{font-size:clamp(40px,7cqw,96px);line-height:1.02;letter-spacing:-.045em;font-weight:500;margin:0 0 25px;max-width:100%;overflow-wrap:anywhere}.site-page p{font-size:14px;line-height:1.65}.site-intro{opacity:.75;max-width:490px}.site-page canvas{display:block;width:100%;height:auto;aspect-ratio:10/7;object-fit:cover;touch-action:auto;border-radius:0}.site-art{overflow:hidden;position:relative;background:#0001}.site-art canvas{transition:transform .8s cubic-bezier(.2,.7,.2,1)}.site-art:hover canvas{transform:scale(1.035)}.site-caption{display:flex;justify-content:space-between;padding:13px 0;font-size:12px;text-align:left;width:100%}.site-gallery{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:22px;margin:32px 0}.site-cta{display:inline-block!important;padding:12px 19px!important;border:1px solid currentColor!important;border-radius:2px!important;margin:18px 0 8px!important;font-size:12px!important}.site-cta:hover{background:var(--ink)!important;color:var(--paper)!important}.site-bottom{padding:55px 4%;border-top:1px solid color-mix(in srgb,var(--ink) 15%,transparent)}.site-bottom h2{font:normal 40px/1.1 Georgia,serif;max-width:600px;margin:0 0 24px}.site-detail{padding:24px;background:color-mix(in srgb,var(--ink) 7%,var(--paper));margin-top:20px}.site-detail strong{font-size:20px}.site-detail[hidden]{display:none}.site-kicker{font-size:10px;opacity:.6}.site-split{display:grid;grid-template-columns:1.2fr 1fr;gap:9%;align-items:center}.site-tabs{display:flex;gap:6px;flex-wrap:wrap;margin:24px 0}.site-tabs button{padding:8px 15px;border:1px solid color-mix(in srgb,var(--ink) 25%,transparent);border-radius:99px;font-size:12px}.site-page .site-tabs button[aria-pressed=true]{background:var(--ink);color:var(--paper)}.site-stats{display:flex;gap:24px;margin:28px 0}.site-stats b{font-size:36px;font-weight:500}.site-stats small{display:block;font-size:10px;opacity:.6}.site-bars{height:200px;display:flex;gap:5%;align-items:end;padding:18px;background:#fff6}.site-bars i{flex:1;background:var(--accent);height:calc(var(--h)*1%);transition:height .65s}.site-page[data-kind=portfolio] .site-gallery{display:flex;overflow:auto;scroll-snap-type:x mandatory}.site-page[data-kind=portfolio] .site-gallery>div{min-width:44%;scroll-snap-align:start}.site-page[data-kind=editorial] h1,.site-page[data-kind=magazine] h1,.site-page[data-kind=travel] h1,.site-page[data-kind=material] h1{font-family:Georgia,serif;letter-spacing:-.05em}.site-page[data-kind=editorial] .site-art{transform:rotate(-4deg);box-shadow:20px 20px 0 #0001}.site-page[data-kind=gallery] .site-gallery{display:flex;gap:12px;height:330px}.site-page[data-kind=gallery] .site-gallery>div{flex:1;min-width:0;transition:flex .7s}.site-page[data-kind=gallery] .site-gallery>div:hover,.site-page[data-kind=gallery] .site-gallery>div:focus-within{flex:2.5}.site-page[data-kind=gallery] canvas{height:290px;object-fit:cover}.site-page[data-kind=saas] .site-hero{text-align:center;max-width:850px;margin:auto}.site-page[data-kind=saas] .site-intro{margin:0 auto}.site-board{padding:25px;background:#fff;border-radius:17px;box-shadow:0 24px 50px #33445518;transform:perspective(1100px) rotateX(calc(var(--my,0)*-3deg)) rotateY(calc(var(--mx,0)*4deg));transition:transform .1s}.site-page[data-kind=travel] .site-body{padding:0}.site-travel{height:520px;position:relative;display:grid;align-items:center;padding:4%}.site-travel>.site-art{position:absolute;inset:0}.site-travel canvas{width:100%;height:100%;object-fit:cover}.site-travel>.site-copy{position:relative;color:#fff5de;max-width:700px;text-shadow:0 2px 20px #193b2844}.site-page[data-kind=music] .site-art{border-radius:50%;aspect-ratio:1}.site-page[data-kind=music] canvas{height:100%;object-fit:cover}.site-project{border-top:1px solid #0003;padding:20px 0}.site-project summary{cursor:pointer;list-style:none;font-size:clamp(21px,3cqw,37px);display:flex;gap:24px;align-items:center}.site-project summary small{font:12px Arial}.site-project summary::after{content:'+';margin-left:auto}.site-project[open] summary::after{content:'−'}.site-project .site-art{max-width:600px;margin:20px 0 10px}.site-terminal{background:#17242a;color:#92b7a7;border:1px solid #ffffff16;padding:25px;border-radius:12px;font:13px/2 monospace;white-space:pre-wrap;min-height:300px}.site-terminal b{color:#eee}.site-page[data-kind=exhibition] h1{font-size:clamp(60px,12cqw,155px);letter-spacing:-.075em}.site-poster{height:290px;position:relative;overflow:hidden}.site-poster span{position:absolute;left:calc(50% - 160px);top:55px;width:320px;height:160px;border:1px solid currentColor;transform:rotate(calc(var(--i)*9deg + var(--time,0)*1deg))}.site-reading{display:grid;grid-template-columns:1fr 2fr;gap:12%;padding:40px 0}.site-reading h2{font:36px Georgia}.site-reading p{font:18px/1.8 Georgia}.site-progress{position:sticky;top:0;height:3px;background:var(--accent);width:calc(var(--progress,0)*100%);z-index:2}.site-page[data-kind=report] .site-bars{height:290px;background:transparent}.site-page[data-kind=material] .site-art{border-radius:48% 48% 0 0}.site-page[data-kind=material] .site-gallery{gap:5%}.site-feature-copy{min-height:48px}.site-page .site-hidden{display:none!important}@container(max-width:620px){.site-body{padding:30px 5%}.site-split,.site-reading{grid-template-columns:1fr;gap:26px}.site-nav{gap:12px;font-size:10px}.site-split>.site-art{max-height:310px}.site-gallery{grid-template-columns:1fr 1fr;gap:12px}.site-page[data-kind=portfolio] .site-gallery>div{min-width:76%}.site-stats{gap:16px}.site-stats b{font-size:28px}.site-page[data-kind=gallery] .site-gallery{height:250px}.site-page[data-kind=gallery] canvas{height:205px}.site-travel{height:520px}.site-gallery>div:nth-child(3){grid-column:1/-1}.site-page[data-kind=material] .site-gallery>div:nth-child(3){grid-column:auto}.site-page[data-kind=material] .site-gallery{grid-template-columns:1fr}.site-page[data-kind=material] canvas{max-height:360px}.site-page h1{font-size:clamp(38px,10cqw,70px)}}@media(prefers-reduced-motion:reduce){.site-page,.site-page *{scroll-behavior:auto!important;transition:none!important}}\n`;
    function mount(host, item, params) {
        const p = {
            ...item.defaults,
            ...params
        }, d = item.site, kind = d.kind, abort = new AbortController, signal = abort.signal;
        let active = 0, playing = !matchMedia("(prefers-reduced-motion: reduce)").matches, time = 0, last = 0, raf = 0, visible = true;
        const zh = (document.documentElement.lang || "").toLowerCase().startsWith("zh"), ui = zh ? {
            preview: "网站交互预览",
            art: "原创程序配图",
            explore: "探索更多",
            home: "首页",
            navExplore: "探索",
            about: "关于",
            back: "回到顶部",
            bottom: "这是一份可以继续替换文案、配图和内容的网站设计样例。",
            aboutTitle: "关于这个工作室",
            aboutText: "我们通过排版、材料与互动，为想法找到清晰的表达。",
            detail: "项目详情在这里展开。正式制作时，Agent 可以替换为你的案例、图片、链接和介绍。",
            run: "运行演示",
            rerun: "再次运行"
        } : {
            preview: "interactive website preview",
            art: "original procedural artwork",
            explore: "Explore more",
            home: "Home",
            navExplore: "Explore",
            about: "About",
            back: "Back to top",
            bottom: "A website study ready for your copy, images, links, and content.",
            aboutTitle: "About this studio",
            aboutText: "We use type, materials, and interaction to give ideas a clear form.",
            detail: "Project details open here. The Agent can replace these with your work, images, links, and story.",
            run: "Run demo",
            rerun: "Run again"
        };
        const options = kind === "travel" ? zh ? [ "山林", "海岸", "旷野" ] : [ "Mountains", "Coast", "Open land" ] : kind === "music" ? [ "SIDE A", "SIDE B", "SIDE C" ] : kind === "material" ? zh ? [ "石材", "纸张", "木材" ] : [ "Stone", "Paper", "Wood" ] : kind === "report" ? [ "2024", "2025", "2026" ] : zh ? [ "概览", "协作", "洞察" ] : [ "Overview", "Collaboration", "Insights" ];
        const visual = (n = 0, mode = "abstract") => '<div class="site-art"><canvas width="600" height="420" data-visual="' + n + '" data-mode="' + mode + '" aria-label="' + esc(ui.art) + '"></canvas></div>';
        const copy = '<div class="site-copy"><div class="site-eyebrow">INDEPENDENT / ' + item.id + "</div><h1>" + esc(p.title) + '</h1><p class="site-intro">' + esc(p.subtitle) + '</p><button class="site-cta" data-scroll>' + esc(ui.explore) + " ↗</button></div>";
        const gallery = (mode = "abstract", count = 3) => '<div class="site-gallery">' + Array.from({
            length: count
        }, (_, n) => "<div>" + visual(n, mode) + '<button class="site-caption" data-project="' + n + '"><span>' + [ "Form & space", "A quiet rhythm", "New perspectives", "Field notes", "Common ground" ][n] + "</span><span>↗</span></button></div>").join("") + "</div>";
        const tabs = '<div class="site-tabs">' + options.map((name, n) => '<button data-option="' + n + '" aria-pressed="' + (n === 0) + '">' + name + "</button>").join("") + "</div>";
        const bars = '<div class="site-bars">' + Array.from({
            length: 9
        }, (_, n) => '<i style="--h:' + (18 + n * 7) + '"></i>').join("") + "</div>";
        let content = "";
        if (kind === "portfolio" || kind === "gallery") content = '<div class="site-hero">' + copy + "</div>" + gallery("abstract", kind === "gallery" ? 5 : 4);
        if (kind === "editorial" || kind === "magazine") content = '<div class="site-split">' + copy + visual(kind === "editorial" ? 0 : 2) + "</div>" + (kind === "magazine" ? '<div class="site-reading"><h2>Look a little closer.</h2><div><p>Good stories begin with a small observation. A familiar object, a changing light, a place we walk past every day.</p><p>This is a journal about finding something worth keeping. An invitation to slow down, to notice, and to make with intention.</p></div></div>' : gallery("architecture"));
        if (kind === "saas") content = '<div class="site-hero">' + copy + '</div><div class="site-board">' + tabs + '<p class="site-feature-copy">把项目、任务与灵感放在同一个清晰的空间。</p>' + bars + "</div>";
        if (kind === "travel") content = '<div class="site-travel">' + visual(1, "landscape") + copy + '</div><div style="padding:20px 4%">' + tabs + '<p class="site-feature-copy">沿着山路，找一段安静的旅程。</p>' + gallery("landscape") + "</div>";
        if (kind === "music") content = '<div class="site-split">' + copy + visual(0, "record") + "</div>" + tabs + '<p class="site-feature-copy">SIDE A · First light · 视觉试听演示，不含音频。</p>';
        if (kind === "architecture") content = copy + [ "Courtyard House", "Quiet Pavilion", "Open Library", "Garden Studio" ].map((name, n) => '<details class="site-project" ' + (n === 0 ? "open" : "") + "><summary><small>0" + (n + 1) + "</small>" + name + "</summary>" + visual(n, "architecture") + "<p>从光线、材料与人的日常出发，重新理解一个空间。</p></details>").join("");
        if (kind === "developer") content = '<div class="site-split">' + copy + '<div class="site-terminal">$ create something\n\n<b>const idea = {</b>\n  clarity: true,\n  curiosity: Infinity,\n<b>};</b>\n\n<span class="site-build-status">Ready to explore.</span>\n<button class="site-cta" data-build>' + esc(ui.run) + " ↗</button></div></div>";
        if (kind === "exhibition") content = copy + '<div class="site-poster">' + Array.from({
            length: 20
        }, (_, n) => '<span style="--i:' + n + '"></span>').join("") + '</div><div class="site-tabs"><button data-program="0" aria-pressed="true">周五 · 艺术家对谈</button><button data-program="1" aria-pressed="false">周六 · 开放工作室</button></div><p class="site-feature-copy">18:00 — 19:00 · Gallery 02 · 免费开放</p>';
        if (kind === "material") content = copy + tabs + gallery();
        if (kind === "report") content = copy + tabs + '<div class="site-stats"><div><b data-stat>48</b><small>PROJECTS</small></div><div><b>12</b><small>COMMUNITIES</small></div><div><b>+32%</b><small>PROGRESS</small></div></div>' + bars;
        host.innerHTML = "<style>" + style + '</style><div class="site-page" data-kind="' + kind + '" tabindex="0" aria-label="' + esc(p.title + " " + ui.preview) + '"><div class="site-progress"></div><div class="site-top"><span class="site-brand">STUDIO / ' + item.id.slice(1) + '</span><nav class="site-nav"><button data-home>' + esc(ui.home) + "</button><button data-scroll>" + esc(ui.navExplore) + "</button><button data-about>" + esc(ui.about) + '</button></nav></div><div class="site-body">' + content + '<section class="site-detail" hidden aria-live="polite"></section></div><section class="site-bottom"><span class="site-kicker">THOUGHTFULLY MADE</span><h2>Good things take a little curiosity.</h2><p>' + esc(ui.bottom) + '</p><button class="site-cta" data-home>' + esc(ui.back) + " ↑</button></section></div>";
        const page = host.querySelector(".site-page");
        page.style.setProperty("--paper", d.bg);
        page.style.setProperty("--ink", d.ink);
        page.style.setProperty("--accent", /^#[a-f\d]{6}$/i.test(p.accent) ? p.accent : item.accent);
        const detail = page.querySelector(".site-detail"), bottom = page.querySelector(".site-bottom"), canvases = [ ...page.querySelectorAll("canvas") ];
        const on = (el, event, fn) => el.addEventListener(event, fn, {
            signal: signal
        });
        function reveal(title, text) {
            detail.replaceChildren();
            const h = document.createElement("strong"), paragraph = document.createElement("p");
            h.textContent = title;
            paragraph.textContent = text;
            detail.append(h, paragraph);
            detail.hidden = false;
            detail.scrollIntoView({
                behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth",
                block: "nearest"
            });
        }
        function repaint() {
            for (const canvas of canvases) {
                const c = canvas.getContext("2d");
                art(c, 0, 0, 600, 420, time, Number(canvas.dataset.visual) + active, p.accent, canvas.dataset.mode);
            }
            page.style.setProperty("--time", String(time * 10));
        }
        on(page, "click", event => {
            const b = event.target.closest("button");
            if (!b) return;
            if (b.hasAttribute("data-home")) page.scrollTo({
                top: 0,
                behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth"
            });
            if (b.hasAttribute("data-scroll")) bottom.scrollIntoView({
                behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth",
                block: "start"
            });
            if (b.hasAttribute("data-about")) reveal(ui.aboutTitle, ui.aboutText);
            if (b.hasAttribute("data-project")) reveal([ "Form & space", "A quiet rhythm", "New perspectives", "Field notes", "Common ground" ][Number(b.dataset.project)], ui.detail);
            if (b.hasAttribute("data-option")) {
                active = Number(b.dataset.option);
                for (const tab of page.querySelectorAll("[data-option]")) tab.setAttribute("aria-pressed", String(tab === b));
                const text = page.querySelector(".site-feature-copy");
                if (text) text.textContent = kind === "travel" ? [ "沿着山路，找一段安静的旅程。", "沿着海岸，听潮水改变一天的节奏。", "走进旷野，看风经过开阔的地平线。" ][active] : kind === "music" ? options[active] + " · " + [ "First light", "After hours", "Slow motion" ][active] + " · 视觉演示，不含音频。" : [ "把项目、任务与灵感放在同一个清晰的空间。", "让讨论与项目进度保持同步。", "用清晰的数据发现下一步方向。" ][active];
                page.querySelectorAll(".site-bars i").forEach((bar, n) => bar.style.setProperty("--h", String(15 + (n * 13 + active * 23) % 78)));
                const stat = page.querySelector("[data-stat]");
                if (stat) stat.textContent = String([ 48, 61, 79 ][active]);
                repaint();
            }
            if (b.hasAttribute("data-build")) {
                page.querySelector(".site-build-status").textContent = "✓ Demo built successfully · 3 components ready";
                b.textContent = ui.rerun + " ↗";
            }
            if (b.hasAttribute("data-program")) {
                for (const tab of page.querySelectorAll("[data-program]")) tab.setAttribute("aria-pressed", String(tab === b));
                page.querySelector(".site-feature-copy").textContent = Number(b.dataset.program) ? "14:00 — 17:00 · Studio 04 · 开放参观" : "18:00 — 19:00 · Gallery 02 · 免费开放";
            }
        });
        on(page, "pointermove", e => {
            const r = page.getBoundingClientRect();
            page.style.setProperty("--mx", String((e.clientX - r.left) / r.width * 2 - 1));
            page.style.setProperty("--my", String((e.clientY - r.top) / r.height * 2 - 1));
        });
        on(page, "scroll", () => page.style.setProperty("--progress", String(page.scrollTop / Math.max(1, page.scrollHeight - page.clientHeight))));
        function frame(now) {
            if (now - last > 1e3 / 24) {
                const dt = last ? Math.min(.1, (now - last) / 1e3) : 0;
                last = now;
                if (playing && visible && !document.hidden) {
                    time += dt * (p.speed || 1);
                    repaint();
                }
            }
            raf = requestAnimationFrame(frame);
        }
        const observer = new IntersectionObserver(entries => visible = entries.some(e => e.isIntersecting));
        observer.observe(page);
        repaint();
        raf = requestAnimationFrame(frame);
        return {
            setPlaying(value) {
                playing = value;
                last = 0;
            },
            destroy() {
                abort.abort();
                observer.disconnect();
                cancelAnimationFrame(raf);
                host.replaceChildren();
            }
        };
    }
    window.CreativeWebsiteDesign = window.CreativeWebsiteDesign.concat(items);
    window.WebsiteDesignStudies = {
        mount: mount
    };
})();

/* W21 — editable foldable-screen study, inspired by jadon7/iphone-duo (MIT).
 * Original procedural model/UI: no Apple models, imagery or remote assets.
 * Interaction reference: iphone-duo by jadon7, shared by Ethan Wen. */ (() => {
    "use strict";
    const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
    function opening(t) {
        const x = (t % 12 + 12) % 12;
        return x < 2 ? 1 : x < 5 ? (1 + Math.cos((x - 2) / 3 * Math.PI)) / 2 : x < 7 ? 0 : x < 10 ? (1 - Math.cos((x - 7) / 3 * Math.PI)) / 2 : 1;
    }
    function rounded(T, w, h, r) {
        const s = new T.Shape, x = -w / 2, y = -h / 2;
        s.moveTo(x + r, y);
        s.lineTo(x + w - r, y);
        s.quadraticCurveTo(x + w, y, x + w, y + r);
        s.lineTo(x + w, y + h - r);
        s.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
        s.lineTo(x + r, y + h);
        s.quadraticCurveTo(x, y + h, x, y + h - r);
        s.lineTo(x, y + r);
        s.quadraticCurveTo(x, y, x + r, y);
        return s;
    }
    function texture(T, p, mode) {
        const canvas = document.createElement("canvas");
        canvas.width = 1200;
        canvas.height = 850;
        const c = canvas.getContext("2d");
        const g = c.createLinearGradient(0, 0, 0, 850);
        g.addColorStop(0, "#182a32");
        g.addColorStop(.55, "#384154");
        g.addColorStop(1, "#15282a");
        c.fillStyle = g;
        c.fillRect(0, 0, 1200, 850);
        for (let n = 0; n < 7; n++) {
            c.fillStyle = [ "#253e42", "#34434f", "#4c4b60", "#5c546c", "#645d70", "#43545e", "#31454b" ][n];
            c.beginPath();
            c.moveTo(0, 850);
            for (let x = 0; x <= 1200; x += 4) {
                const y = 360 + n * 55 + Math.sin(x * .005 + n * .7) * 55 + Math.sin(x * .011 + n) * 18;
                c.lineTo(x, y);
            }
            c.lineTo(1200, 850);
            c.fill();
        }
        if (mode === "launcher") {
            c.fillStyle = "#ffffffbb";
            c.beginPath();
            c.roundRect(58, 70, 425, 220, 35);
            c.fill();
            c.fillStyle = "#293830";
            c.font = "32px Arial";
            c.fillText("MONDAY", 88, 122);
            c.font = "68px Arial";
            c.fillText("21", 88, 209);
            c.font = "21px Arial";
            c.fillText("Make space for ideas.", 200, 205);
            const colors = [ "#7a957f", "#738cab", "#c19c72", "#aa8779", "#576c61", "#928da1" ];
            for (let row = 0; row < 3; row++) for (let col = 0; col < 6; col++) {
                const x = 80 + col * 185, y = 355 + row * 137;
                c.fillStyle = colors[(col + row) % 6];
                c.beginPath();
                c.roundRect(x, y, 76, 76, 19);
                c.fill();
                c.strokeStyle = "#fff";
                c.lineWidth = 4;
                c.beginPath();
                if (col % 3 === 0) c.arc(x + 38, y + 38, 17, 0, Math.PI * 2); else if (col % 3 === 1) {
                    c.moveTo(x + 22, y + 26);
                    c.lineTo(x + 54, y + 26);
                    c.lineTo(x + 54, y + 51);
                    c.lineTo(x + 22, y + 51);
                    c.closePath();
                } else {
                    c.moveTo(x + 23, y + 48);
                    c.lineTo(x + 37, y + 25);
                    c.lineTo(x + 55, y + 48);
                }
                c.stroke();
            }
        } else {
            const center = mode === "cover" ? 900 : 600, max = mode === "cover" ? 490 : 1030;
            c.fillStyle = "#f8f7ed";
            c.textAlign = "center";
            c.font = "24px Arial";
            c.fillText("A SMALL PERSONAL UNIVERSE", center, 94);
            c.font = "200 158px Arial";
            c.fillText("ORBIT", center, 245);
            c.font = '500 37px Arial,"PingFang SC",sans-serif';
            c.fillText(p.title || "Open to possibility", center, 695, max);
            c.font = '22px Arial,"PingFang SC",sans-serif';
            c.fillText(p.subtitle || "A little more room for everything.", center, 742, max);
        }
        c.fillStyle = p.accent || "#70866b";
        c.globalAlpha = .25;
        c.fillRect(0, 0, 1200, 850);
        c.globalAlpha = 1;
        c.fillStyle = "#fff";
        c.beginPath();
        c.roundRect(mode === "cover" ? 780 : 480, 812, 240, 7, 4);
        c.fill();
        const tex = new T.CanvasTexture(canvas);
        tex.colorSpace = T.SRGBColorSpace;
        tex.anisotropy = 4;
        return tex;
    }
    function create(T) {
        const scene = new T.Scene;
        scene.background = new T.Color("#f4f5f0");
        const camera = new T.PerspectiveCamera(32, 16 / 9, .1, 100);
        camera.position.set(0, .5, 16);
        camera.lookAt(0, 0, 0);
        scene.add(new T.HemisphereLight(16777215, 9147009, 3));
        for (const [x, y, z, power] of [ [ -7, 8, 10, 5 ], [ 7, 2, 3, 3 ], [ -4, -5, -4, 2 ] ]) {
            const l = new T.DirectionalLight(16777215, power);
            l.position.set(x, y, z);
            scene.add(l);
        }
        const phone = new T.Group;
        scene.add(phone);
        const hinge = new T.Group;
        hinge.position.z = .18;
        phone.add(hinge);
        const metal = new T.MeshStandardMaterial({
            color: "#c5c7c2",
            metalness: .72,
            roughness: .28
        }), edge = new T.MeshStandardMaterial({
            color: "#363d3b",
            metalness: .6,
            roughness: .24
        });
        const shellGeometry = new T.ExtrudeGeometry(rounded(T, 3.78, 5.54, .35), {
            depth: .2,
            bevelEnabled: true,
            bevelThickness: .045,
            bevelSize: .045,
            bevelSegments: 3,
            steps: 1,
            curveSegments: 16
        });
        shellGeometry.translate(0, 0, -.2);
        const screenShape = rounded(T, 3.64, 5.4, .27), screenGeometry = new T.ShapeGeometry(screenShape, 24);
        const position = screenGeometry.attributes.position;
        const uv = [];
        for (let j = 0; j < position.count; j++) uv.push(position.getX(j) / 3.64 + .5, position.getY(j) / 5.4 + .5);
        screenGeometry.setAttribute("uv", new T.Float32BufferAttribute(uv, 2));
        let map = null, coverMap = null, key = "";
        const uniforms = {
            fold: {
                value: 0
            }
        };
        const mats = [];
        function screen(parent, x, z, outer = false) {
            const shape = new T.Shape, w = 3.73, h = 5.4, rad = .26, l = -w / 2, rr = w / 2, bot = -h / 2, top = h / 2;
            if (!outer) {
                const a = x < 0 ? rad : 0, b = x > 0 ? rad : 0;
                shape.moveTo(l + a, bot);
                shape.lineTo(rr - b, bot);
                shape.quadraticCurveTo(rr, bot, rr, bot + b);
                shape.lineTo(rr, top - b);
                shape.quadraticCurveTo(rr, top, rr - b, top);
                shape.lineTo(l + a, top);
                shape.quadraticCurveTo(l, top, l, top - a);
                shape.lineTo(l, bot + a);
                shape.quadraticCurveTo(l, bot, l + a, bot);
            }
            const geo = outer ? screenGeometry : new T.ShapeGeometry(shape, 24);
            if (!outer) {
                const pos = geo.attributes.position, uv = [];
                for (let j = 0; j < pos.count; j++) uv.push(pos.getX(j) / w + .5, pos.getY(j) / h + .5);
                geo.setAttribute("uv", new T.Float32BufferAttribute(uv, 2));
            }
            const m = new T.MeshBasicMaterial({
                color: "white",
                toneMapped: false
            });
            m.onBeforeCompile = shader => {
                shader.uniforms.duoFold = uniforms.fold;
                shader.vertexShader = "varying vec2 duoUv;\n" + shader.vertexShader;
                shader.vertexShader = shader.vertexShader.replace("#include <begin_vertex>", "#include <begin_vertex>\nduoUv=uv;");
                shader.fragmentShader = "uniform float duoFold; varying vec2 duoUv;\n" + shader.fragmentShader;
                const left = x < 0 && !outer;
                shader.fragmentShader = shader.fragmentShader.replace("#include <map_fragment>", `#ifdef USE_MAP\nvec2 q=duoUv;\nfloat edge=${left ? "1.0-q.x" : "q.x"};\nfloat phase=${left ? "clamp(duoFold/1.5707963,0.0,1.0)" : outer ? "clamp((3.14159265-duoFold)/1.5707963,0.0,1.0)" : "0.0"};\n${outer ? "q.x=0.5+q.x*0.5;" : left ? "q.x=(q.x-1.0)*0.5*cos(duoFold)+0.5;" : "q.x=q.x*0.5+0.5;"}\nfloat blur=0.018*phase*pow(edge,1.35);\nvec4 col=vec4(0.0);\nfor(int n=-2;n<=2;n++){col+=texture2D(map,clamp(q+vec2(float(n)*blur,0.0),vec2(0.001),vec2(0.999)))*0.2;}\ndiffuseColor*=col;\ndiffuseColor.rgb*=1.0-clamp(phase*pow(edge,1.35)*1.8,0.0,1.0);\n#endif`);
            };
            m.userData.duoOuter = outer;
            m.customProgramCacheKey = () => `duo-${x}-${outer}`;
            const mesh = new T.Mesh(geo, m);
            mesh.position.set(outer ? x : Math.sign(x) * 1.868, 0, z);
            if (outer) mesh.rotation.y = Math.PI;
            parent.add(mesh);
            mats.push(m);
            return mesh;
        }
        for (const side of [ -1, 1 ]) {
            const parent = side < 0 ? hinge : phone, x = side * 1.91, z = side < 0 ? -.18 : 0;
            const body = new T.Mesh(shellGeometry, metal);
            body.position.set(x, 0, z);
            parent.add(body);
            const rim = new T.Mesh(new T.ShapeGeometry(rounded(T, 3.73, 5.49, .32), 24), edge);
            rim.position.set(x, 0, z + .048);
            parent.add(rim);
            screen(parent, x, z + .055);
        }
        const outer = screen(hinge, -1.91, -.44, true);
        const pin = new T.Mesh(new T.CylinderGeometry(.055, .055, 4.6, 16), metal);
        pin.position.z = -.02;
        phone.add(pin);
        const cameraBump = new T.Mesh(new T.CylinderGeometry(.32, .32, .08, 32), edge);
        cameraBump.rotation.x = Math.PI / 2;
        cameraBump.position.set(3.04, 1.92, -.26);
        phone.add(cameraBump);
        const lens = new T.Mesh(new T.CylinderGeometry(.22, .22, .09, 32), new T.MeshStandardMaterial({
            color: "#183139",
            metalness: .8,
            roughness: .12
        }));
        lens.rotation.x = Math.PI / 2;
        lens.position.copy(cameraBump.position);
        lens.position.z -= .04;
        phone.add(lens);
        function update(t, p, i = {}) {
            const next = JSON.stringify([ p.title, p.subtitle, p.accent, i.duoMode || "wallpaper" ]);
            if (next !== key) {
                key = next;
                map?.dispose();
                coverMap?.dispose();
                map = texture(T, p, i.duoMode || "wallpaper");
                coverMap = texture(T, p, i.duoMode === "launcher" ? "launcher" : "cover");
                for (const m of mats) {
                    m.map = m.userData.duoOuter ? coverMap : map;
                    m.needsUpdate = true;
                }
            }
            const progress = Number.isFinite(i.duoOpening) ? clamp(i.duoOpening) : opening(t), fold = (1 - progress) * Math.PI;
            uniforms.fold.value = fold;
            hinge.rotation.y = fold;
            outer.visible = progress < .99;
            const scale = 1.25 / (1 + .32 * Math.sin(fold)) * (i.duoZoom || 1) * Math.min(1, (i.duoAspect || 1.78) / 1.2);
            phone.position.x = -1.91 * (1 - progress) * scale;
            phone.rotation.set(-.13 + (i.dragY || 0) * .7, -.18 + (i.dragX || 0) * .8, 0);
            phone.scale.setScalar(scale);
            camera.aspect = 16 / 9;
            camera.updateProjectionMatrix();
        }
        return {
            scene: scene,
            camera: camera,
            update: update
        };
    }
    const item = {
        id: "W21",
        name: "Duo · 折叠屏交互",
        family: "website",
        category: "product-data",
        duration: 12,
        accent: "#70866b",
        description: "A procedural foldable-screen product study with opening, rotation, zoom, and display modes.",
        interaction: "Auto fold; drag to rotate; scroll to zoom; use the generated page slider and display modes.",
        site: {
            kind: "duo"
        },
        create: create,
        defaults: {
            title: "Open to possibility",
            subtitle: "A little more room for everything.",
            accent: "#70866b",
            intensity: .6,
            seed: 42
        },
        overlay(c, t, p, i = {}) {
            if (i.duoUi) return;
            c.fillStyle = "#29342b";
            c.font = '500 28px Arial,"PingFang SC",sans-serif';
            c.fillText(p.title, 42, 52, 800);
            c.fillStyle = "#6c766b";
            c.font = "13px Arial";
            c.fillText("FOLD / EXPLORE", 42, 80);
            c.textAlign = "right";
            c.fillText("INTERACTIVE STUDY", 1158, 630);
            c.textAlign = "left";
        }
    };
    function mount(host, item, p, options = {}) {
        const abort = new AbortController, signal = abort.signal;
        const locale = (document.documentElement.lang || "en").toLowerCase().split("-")[0], ui = {
            zh: {
                preview: "Duo 折叠屏交互预览",
                wallpaper: "壁纸",
                launcher: "桌面",
                reset: "重置视角",
                opening: "开合",
                angle: "折叠角度",
                hint: "拖动旋转 · 滚轮缩放 · 按播放恢复自动开合",
                error: "预览暂不可用："
            },
            fr: {
                preview: "Aperçu interactif du Duo pliable",
                wallpaper: "Fond",
                launcher: "Accueil",
                reset: "Réinitialiser",
                opening: "Ouverture",
                angle: "Angle de pliage",
                hint: "Faire glisser pour tourner · Molette pour zoomer · Lecture pour reprendre",
                error: "Aperçu indisponible : "
            },
            ja: {
                preview: "Duo 折りたたみ操作プレビュー",
                wallpaper: "壁紙",
                launcher: "ホーム",
                reset: "視点をリセット",
                opening: "開閉",
                angle: "折りたたみ角度",
                hint: "ドラッグで回転 · ホイールでズーム · 再生で自動開閉",
                error: "プレビューを表示できません: "
            },
            ko: {
                preview: "Duo 폴더블 인터랙션 미리보기",
                wallpaper: "배경",
                launcher: "홈",
                reset: "시점 초기화",
                opening: "열림",
                angle: "접힘 각도",
                hint: "드래그 회전 · 휠 확대 · 재생 시 자동 열림",
                error: "미리보기를 사용할 수 없습니다: "
            }
        }[locale] || {
            preview: "Duo foldable interaction preview",
            wallpaper: "Wallpaper",
            launcher: "Home",
            reset: "Reset view",
            opening: "Opening",
            angle: "Fold angle",
            hint: "Drag to rotate · Scroll to zoom · Play to resume auto fold",
            error: "Preview unavailable: "
        };
        host.innerHTML = `<style>.duo-page{height:100%;background:#f4f5f0;color:#29342b;display:flex;flex-direction:column;overflow:auto;padding:0 20px 16px;container-type:inline-size}.duo-page .duo-canvas{display:block;width:100%;min-height:210px;height:0;flex:1;object-fit:contain;touch-action:none}.duo-controls{width:min(680px,100%);margin:0 auto;display:flex;align-items:center;gap:18px;border:1px solid #dfe3d9;border-radius:20px;background:#ffffffcf;padding:15px 20px;font:12px Arial,sans-serif}.duo-controls .duo-mode{display:flex;gap:4px}.duo-controls button{color:#394036;background:transparent;border:0;border-radius:8px;padding:8px 12px;font:inherit;cursor:pointer}.duo-controls button[aria-pressed=true]{background:#e1e6db!important;color:#263623}.duo-controls label{flex:1;display:flex;gap:10px;align-items:center;white-space:nowrap}.duo-controls input{width:100%;min-width:50px;accent-color:#718269}.duo-controls output{min-width:35px;font-variant-numeric:tabular-nums}.duo-credit{display:flex;justify-content:space-between;gap:10px;width:min(680px,100%);margin:10px auto 0;font:10px Arial,sans-serif;color:#757e72}.duo-credit a{color:inherit}@container(max-width:580px){.duo-controls{flex-wrap:wrap;padding:12px;gap:8px}.duo-controls label{flex-basis:100%}.duo-page .duo-canvas{min-height:230px}.duo-credit{flex-wrap:wrap}}</style><div class="duo-page"><canvas class="duo-canvas" width="1200" height="675" aria-label="${ui.preview}"></canvas><div class="duo-controls"><div class="duo-mode"><button aria-pressed="true" data-mode="wallpaper">${ui.wallpaper}</button><button aria-pressed="false" data-mode="launcher">${ui.launcher}</button></div><button data-reset>${ui.reset}</button><label>${ui.opening} <input type="range" min="0" max="180" value="180" step="1" aria-label="${ui.angle}"><output>180°</output></label></div><div class="duo-credit"><span>${ui.hint}</span></div><p class="duo-error" role="status"></p></div>`;
        const canvas = host.querySelector("canvas"), range = host.querySelector("input"), out = host.querySelector("output"), input = {
            ...CreativeRuntime.input(),
            duoMode: "wallpaper",
            duoZoom: 1,
            duoUi: true
        };
        let t = 0, last = 0, raf = 0, playing = !matchMedia("(prefers-reduced-motion: reduce)").matches, dirty = true, drag = null, closed = false;
        const resize = new ResizeObserver(() => {
            const r = canvas.getBoundingClientRect();
            if (r.width > 0 && r.height > 0) {
                canvas.width = Math.round(r.width * 1.5);
                canvas.height = Math.round(r.height * 1.5);
                input.duoAspect = r.width / r.height;
                dirty = true;
            }
        });
        resize.observe(canvas);
        const on = (e, k, f, o = {}) => e.addEventListener(k, f, {
            ...o,
            signal: signal
        });
        on(range, "input", () => {
            input.duoOpening = Number(range.value) / 180;
            playing = false;
            options.onPlaybackChange?.(false);
            out.textContent = range.value + "°";
            dirty = true;
        });
        on(host, "click", e => {
            const b = e.target.closest("button");
            if (!b) return;
            if (b.dataset.mode) {
                input.duoMode = b.dataset.mode;
                host.querySelectorAll("[data-mode]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
                dirty = true;
            }
            if (b.hasAttribute("data-reset")) {
                input.dragX = input.dragY = 0;
                input.duoZoom = 1;
                dirty = true;
            }
        });
        on(canvas, "pointerdown", e => {
            drag = {
                x: e.clientX,
                y: e.clientY,
                dx: input.dragX,
                dy: input.dragY
            };
            canvas.setPointerCapture(e.pointerId);
        });
        on(canvas, "pointermove", e => {
            if (!drag) return;
            const r = canvas.getBoundingClientRect();
            input.dragX = clamp(drag.dx + (e.clientX - drag.x) / r.width * 4, -3, 3);
            input.dragY = clamp(drag.dy + (e.clientY - drag.y) / r.height * 3, -1.5, 1.5);
            dirty = true;
        });
        on(canvas, "pointerup", () => drag = null);
        on(canvas, "pointercancel", () => drag = null);
        on(canvas, "wheel", e => {
            e.preventDefault();
            input.duoZoom = clamp(input.duoZoom - e.deltaY * .001, .7, 1.5);
            dirty = true;
        }, {
            passive: false
        });
        function frame(now) {
            if (closed) return;
            const dt = last ? Math.min(.1, (now - last) / 1e3) : 0;
            if (now - last > 1e3 / 30) {
                last = now;
                if (!document.hidden && (playing || dirty)) {
                    if (playing) t = (t + dt * (.4 + (p.intensity ?? .6) * 1.2)) % 12;
                    try {
                        CreativeRuntime.render(item, canvas, t, p, input);
                        const angle = Math.round((input.duoOpening ?? opening(t)) * 180);
                        range.value = angle;
                        out.textContent = angle + "°";
                        canvas.dataset.angle = angle;
                        canvas.dataset.frame = String(Math.round(t * 60));
                        dirty = false;
                    } catch (e) {
                        playing = false;
                        host.querySelector(".duo-error").textContent = ui.error + e.message;
                        dirty = false;
                    }
                }
            }
            raf = requestAnimationFrame(frame);
        }
        raf = requestAnimationFrame(frame);
        return {
            setPlaying(value) {
                playing = value;
                if (value && Number.isFinite(input.duoOpening)) {
                    t = 2 + Math.acos(2 * input.duoOpening - 1) / Math.PI * 3;
                    delete input.duoOpening;
                }
                dirty = true;
                last = 0;
            },
            destroy() {
                closed = true;
                resize.disconnect();
                abort.abort();
                cancelAnimationFrame(raf);
                host.replaceChildren();
                CreativeRuntime.clear();
            }
        };
    }
    window.CreativeWebsiteDesign.push(item);
    const siteMount = window.WebsiteDesignStudies.mount;
    window.WebsiteDesignStudies.mount = (host, item, p, options) => item.id === "W21" ? mount(host, item, p, options) : siteMount(host, item, p, options);
    window.DuoStudy = {
        opening: opening
    };
})();
