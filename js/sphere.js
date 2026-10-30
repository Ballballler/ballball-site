/* ========================================================================
   sphere.js —— 零依赖 3D 标签球
   思路参考 alexjcm/tag-sphere（Fibonacci 球面分布 + 旋转矩阵 + Z 深度投影），
   按需重写以支持：熟练度着色、暂停自动旋转、reduced-motion 降级、
   以及给屏幕阅读器用的纯文本副本。

   用法：
     const sphere = createTagSphere(containerEl, [
       { text: 'Python', level: 85, color: '#22d3ee' }, ...
     ], { radius: 150 });
   返回 { destroy, setTags }。
   ===================================================================== */

function createTagSphere(root, tags, options = {}) {
  const opt = Object.assign(
    {
      radius: 150,
      speed: 12, // 自转角速度（度/秒）。按时间积分，和屏幕刷新率无关
      decay: 0.94, // 拖拽惯性衰减（按帧折算）
      drag: 0.22, // 拖拽灵敏度
      maxFontSize: 17,
      minFontSize: 10,
    },
    options
  );
  const autoSpeed = (opt.speed * Math.PI) / 180; // 弧度/秒

  root.textContent = "";
  root.classList.add("sphere");
  root.style.setProperty("--sphere-size", `${opt.radius * 2}px`);

  const reduce =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // 屏幕阅读器与爬虫用的纯文本副本
  const srList = el("ul", { class: "sr-only" });
  (tags || []).forEach((t) => srList.appendChild(el("li", { text: t.text })));
  root.appendChild(srList);

  const stage = el("div", { class: "sphere__stage", "aria-hidden": "true" });
  root.appendChild(stage);

  let nodes = [];
  let points = [];
  let rotX = -0.18; // 初始略微俯视，球不会正对显得呆板
  let rotY = 0;
  let velX = 0; // 弧度/秒
  let velY = reduce ? 0 : autoSpeed; // 弧度/秒
  let dragging = false;
  let lastX = 0;
  let lastY = 0;
  let lastT = 0;
  let raf = null;

  function build(list) {
    stage.textContent = "";
    nodes = [];
    points = [];
    const n = Math.max(list.length, 1);
    const golden = Math.PI * (1 + Math.sqrt(5));

    list.forEach((tag, i) => {
      // Fibonacci 球面：纬度均匀、经度黄金角，避免极点堆积
      const phi = Math.acos(1 - (2 * (i + 0.5)) / n);
      const theta = golden * i;
      points.push({
        x: Math.sin(phi) * Math.cos(theta),
        y: Math.sin(phi) * Math.sin(theta),
        z: Math.cos(phi),
      });

      const node = el("span", { class: "sphere__tag", text: tag.text });
      if (tag.color) node.style.setProperty("--tag-color", tag.color);
      // level 越高，标签越亮、字号越大
      const weight = (tag.level || 60) / 100;
      node.style.setProperty("--tag-weight", weight.toFixed(2));
      stage.appendChild(node);
      nodes.push(node);
    });
  }

  function frame(now) {
    // 统一按秒积分：老写法是「每帧加 0.22 弧度」，60Hz 上等于 2 圈/秒，
    // 高刷屏还要再快一倍。改成 dt 积分后，转速只与 speed 有关。
    const dt = lastT && now ? Math.min(0.05, (now - lastT) / 1000) : 0;
    lastT = now || 0;

    if (!dragging && dt) {
      // 松手后从拖拽惯性平滑回到自转速度
      velY += (reduce ? 0 : autoSpeed - velY) * Math.min(1, dt * 3.2);
      velX *= Math.pow(opt.decay, dt * 60);
    }
    rotY += velY * dt;
    rotX += velX * dt;
    // 限制俯仰，避免球翻过头
    if (rotX > 1.2) {
      rotX = 1.2;
      velX = 0;
    } else if (rotX < -1.2) {
      rotX = -1.2;
      velX = 0;
    }

    const cx = Math.cos(rotX);
    const sx = Math.sin(rotX);
    const cy = Math.cos(rotY);
    const sy = Math.sin(rotY);
    const fov = opt.radius * 2.4;

    for (let i = 0; i < nodes.length; i += 1) {
      const p = points[i];
      // 先绕 Y 转，再绕 X 转
      const x1 = p.x * cy + p.z * sy;
      const z1 = -p.x * sy + p.z * cy;
      const y2 = p.y * cx - z1 * sx;
      const z2 = p.y * sx + z1 * cx;

      // 透视投影：z 越靠前越大越清晰
      const scale = fov / (fov + z2 * opt.radius);
      const px = x1 * opt.radius * scale;
      const py = y2 * opt.radius * scale;
      const depth = (z2 + 1) / 2; // 0 最远 → 1 最近

      const node = nodes[i];
      const size =
        opt.minFontSize + (opt.maxFontSize - opt.minFontSize) * (depth * 0.7 + 0.3);
      node.style.transform = `translate3d(${px.toFixed(2)}px, ${py.toFixed(
        2
      )}px, 0) scale(${scale.toFixed(3)})`;
      node.style.fontSize = `${size.toFixed(1)}px`;
      node.style.opacity = (0.28 + depth * 0.72).toFixed(3);
      node.style.zIndex = String(Math.round(depth * 100));
      // 后面的标签模糊一点，纵深感更强
      node.style.filter = depth < 0.35 ? "blur(0.6px)" : "none";
    }

    raf = requestAnimationFrame(frame);
  }

  function onDown(e) {
    dragging = true;
    lastX = e.clientX;
    lastY = e.clientY;
    root.classList.add("is-dragging");
    if (root.setPointerCapture && e.pointerId !== undefined) {
      try {
        root.setPointerCapture(e.pointerId);
      } catch (_) {
        /* 忽略 */
      }
    }
  }

  function onMove(e) {
    if (!dragging) return;
    const dx = e.clientX - lastX;
    const dy = e.clientY - lastY;
    lastX = e.clientX;
    lastY = e.clientY;
    const k = opt.drag * 0.02; // 每像素位移对应的弧度
    velY = dx * k * 60; // 惯性用「弧度/秒」，松手后自然衰减回自转
    velX = dy * k * 60;
    rotY += dx * k;
    rotX += dy * k;
  }

  function onUp() {
    dragging = false;
    root.classList.remove("is-dragging");
    // 松手后保留一部分速度做惯性，再慢慢回到自动旋转
    velX *= 0.4;
    velY *= 0.5;
  }

  root.addEventListener("pointerdown", onDown);
  window.addEventListener("pointermove", onMove);
  window.addEventListener("pointerup", onUp);
  window.addEventListener("pointercancel", onUp);

  // 键盘也能转：左右转 Y 轴，上下转 X 轴
  root.tabIndex = 0;
  root.setAttribute("role", "img");
  root.setAttribute("aria-label", `技能球：${(tags || []).map((t) => t.text).join("、")}`);
  root.addEventListener("keydown", (e) => {
    const step = 0.12;
    if (e.key === "ArrowLeft") rotY -= step;
    else if (e.key === "ArrowRight") rotY += step;
    else if (e.key === "ArrowUp") rotX -= step;
    else if (e.key === "ArrowDown") rotX += step;
    else return;
    e.preventDefault();
  });

  build(tags || []);
  frame();

  return {
    destroy() {
      if (raf) cancelAnimationFrame(raf);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onUp);
    },
    setTags(list) {
      build(list);
    },
  };
}
