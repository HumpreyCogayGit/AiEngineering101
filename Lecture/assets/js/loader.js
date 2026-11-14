/* AI Engineer Course — first-visit loader: a slowly turning wire-mesh brain with signals running along its wires.
   Shown once per browser session (the first page opened), lifted as soon as the page has loaded and a short
   minimum has passed, skipped with a click or Esc, and never shown when the system asks for reduced motion.
   Loaded synchronously in <head> so the page never flashes before it; the page lays out underneath meanwhile. */
(function () {
  "use strict";
  // Apply the saved light/dark choice before first paint (app.js runs later, deferred).
  try {
    const theme = JSON.parse(localStorage.getItem("aic:theme"));
    if (theme === "light" || theme === "dark") document.documentElement.dataset.theme = theme;
  } catch { /* ignore */ }
  try {
    if (sessionStorage.getItem("aic:loader") === "1") return;
    sessionStorage.setItem("aic:loader", "1");
  } catch { return; } // no session storage: never risk showing it on every page
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const root = document.documentElement;
  root.classList.add("booting");
  const MIN_MS = 2600, MAX_MS = 5500;
  const started = performance.now();

  // ---------------------------------------------------------------- brain geometry (side view, front to the left)
  // x: -1 front .. +1 back, y: -0.8 top .. +0.85 bottom of the stem, z: depth.
  const crest = [[-.96,.02],[-.91,-.17],[-.8,-.35],[-.64,-.51],[-.45,-.63],[-.22,-.71],[.02,-.74],[.26,-.7],[.49,-.61],
    [.7,-.47],[.86,-.29],[.95,-.08],[.91,.11],[.74,.22],[-.89,.16],[-.72,.23],[-.54,.19]];
  const lateral = [[-.78,-.14,.34],[-.66,-.34,.38],[-.46,-.45,.44],[-.64,.02,.4],[-.44,-.18,.48],[-.22,-.52,.45],
    [.02,-.55,.47],[.25,-.5,.44],[-.16,-.27,.54],[.12,-.28,.54],[.36,-.3,.48],[.58,-.34,.38],[.76,-.16,.34],
    [.62,-.06,.46],[.78,.06,.32],[.54,.14,.42],[-.48,.14,.38],[-.5,.29,.32],[-.32,.37,.36],[-.28,.16,.48],
    [-.08,.38,.38],[-.04,.18,.5],[.16,.32,.38],[.24,.14,.48]];
  const cerebellum = [[.26,.28,.04],[.44,.26,.24],[.64,.28,.18],[.77,.37,.04],[.72,.47,.22],[.54,.57,.26],
    [.34,.56,.2],[.22,.44,.26],[.48,.41,.34]];
  const nodes = [];
  const add = (x, y, z, part) => nodes.push({ x, y, z, part, sx: 0, sy: 0, sz: 0, s: 1, glow: 0, links: [] });
  crest.forEach(([x, y]) => add(x, y, 0.02, "cortex"));
  lateral.forEach(([x, y, z]) => { add(x, y, z, "cortex"); add(x, y, -z, "cortex"); });
  cerebellum.forEach(([x, y, z]) => { add(x, y, z, "cerebellum"); if (z > .05) add(x, y, -z, "cerebellum"); });
  const stemRings = [[.34, .04, .13], [.52, .1, .1], [.69, .16, .075], [.84, .21, .055]].map(([y, cx, r]) =>
    [0, 1, 2, 3].map((i) => {
      const a = Math.PI / 4 + (i * Math.PI) / 2;
      add(cx + Math.cos(a) * r, y, Math.sin(a) * r, "stem");
      return nodes.length - 1;
    }));

  const edges = [];
  const link = (a, b) => {
    if (a === b || nodes[a].links.some((l) => l.to === b)) return;
    const e = { a, b, heat: 0 };
    edges.push(e);
    nodes[a].links.push({ to: b, e });
    nodes[b].links.push({ to: a, e });
  };
  // Each node links to its nearest neighbours in the same part; no wires across the Sylvian fissure.
  nodes.forEach((n, i) => {
    if (n.part === "stem") return;
    nodes
      .map((m, j) => ({ j, d: Math.hypot(n.x - m.x, n.y - m.y, n.z - m.z), m }))
      .filter(({ j, d, m }) => j !== i && m.part === n.part && d < 0.43 &&
        !(n.x < -.25 && m.x < -.25 && ((n.y < -.02 && m.y > .22) || (m.y < -.02 && n.y > .22))))
      .sort((p, q) => p.d - q.d).slice(0, 4)
      .forEach(({ j }) => link(i, j));
  });
  stemRings.forEach((ring, r) => ring.forEach((idx, i) => {
    link(idx, ring[(i + 1) % 4]);
    if (r < stemRings.length - 1) link(idx, stemRings[r + 1][i]);
  }));
  // Attach the cerebellum and the stem to the cortex above them.
  const nearest = (idx, part) => nodes.reduce((best, m, j) => (m.part !== part ? best :
    (Math.hypot(nodes[idx].x - m.x, nodes[idx].y - m.y, nodes[idx].z - m.z) <
     Math.hypot(nodes[idx].x - nodes[best].x, nodes[idx].y - nodes[best].y, nodes[idx].z - nodes[best].z) ? j : best)),
    nodes.findIndex((m) => m.part === part));
  stemRings[0].forEach((idx) => { link(idx, nearest(idx, "cortex")); link(idx, nearest(idx, "cerebellum")); });
  nodes.forEach((n, i) => { if (n.part === "cerebellum" && n.y < .3) link(i, nearest(i, "cortex")); });

  // ---------------------------------------------------------------- signals
  const pulses = [];
  function fire(i, hops, from) {
    const n = nodes[i];
    n.glow = 1;
    if (hops <= 0 || pulses.length > 60) return;
    const options = n.links.filter((l) => l.to !== from);
    const count = hops > 3 && Math.random() < .5 ? 2 : 1;
    for (let k = 0; k < count && options.length; k++) {
      const l = options.splice(Math.floor(Math.random() * options.length), 1)[0];
      pulses.push({ from: i, to: l.to, e: l.e, t: 0, speed: 1.6 + Math.random() * 1.2, hops: hops - 1 });
    }
  }

  // ---------------------------------------------------------------- overlay + drawing
  let overlay, canvas, ctx, raf = 0, w = 0, h = 0, colors;
  function readColors() {
    const cs = getComputedStyle(root);
    colors = { wire: cs.getPropertyValue("--muted").trim() || "#5a6469",
               accent: cs.getPropertyValue("--accent").trim() || "#0b6e6e" };
  }
  function size() {
    const r = canvas.getBoundingClientRect(), dpr = Math.min(devicePixelRatio || 1, 2);
    w = r.width; h = r.height;
    canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  let last = 0, spawn = 0;
  function frame(now) {
    const dt = Math.min(.05, (now - (last || now)) / 1000);
    last = now;
    const t = (now - started) / 1000;
    const ry = -0.35 + Math.sin(t * 0.7) * 0.55, rx = 0.12;
    const cy = Math.cos(ry), sy = Math.sin(ry), cx = Math.cos(rx), sx = Math.sin(rx);
    const scale = Math.min(w / 2.3, h / 1.85), ox = w / 2, oy = h * 0.45;
    for (const n of nodes) {
      const x1 = n.x * cy - n.z * sy, z1 = n.z * cy + n.x * sy;
      const y2 = n.y * cx - z1 * sx, z2 = z1 * cx + n.y * sx;
      n.s = 3.2 / (3.2 - z2);
      n.sx = ox + x1 * scale * n.s; n.sy = oy + y2 * scale * n.s; n.sz = z2;
      n.glow = Math.max(0, n.glow - dt * 1.6);
    }
    spawn += dt;
    if (spawn > 0.11) { spawn = 0; fire(Math.floor(Math.random() * nodes.length), 5, -1); }
    for (let i = pulses.length - 1; i >= 0; i--) {
      const p = pulses[i];
      p.t += dt * p.speed;
      p.e.heat = 1;
      if (p.t >= 1) { pulses.splice(i, 1); fire(p.to, p.hops, p.from); }
    }

    ctx.clearRect(0, 0, w, h);
    ctx.lineCap = "round";
    const depth = (z) => Math.max(0, Math.min(1, (z + .65) / 1.3)); // 0 far .. 1 near
    for (const e of edges) {
      const a = nodes[e.a], b = nodes[e.b], d = depth((a.sz + b.sz) / 2);
      e.heat = Math.max(0, e.heat - dt * 1.2);
      ctx.globalAlpha = 0.12 + d * 0.38 + e.heat * 0.35;
      ctx.strokeStyle = e.heat > .05 ? colors.accent : colors.wire;
      ctx.lineWidth = (0.6 + d * 0.7) * a.s;
      ctx.beginPath(); ctx.moveTo(a.sx, a.sy); ctx.lineTo(b.sx, b.sy); ctx.stroke();
    }
    for (const n of nodes) {
      const d = depth(n.sz);
      ctx.globalAlpha = 0.3 + d * 0.6;
      ctx.fillStyle = n.glow > .05 ? colors.accent : colors.wire;
      ctx.beginPath(); ctx.arc(n.sx, n.sy, (1.3 + d * 1.2 + n.glow * 2.2) * n.s, 0, Math.PI * 2); ctx.fill();
    }
    ctx.fillStyle = colors.accent;
    for (const p of pulses) {
      const a = nodes[p.from], b = nodes[p.to];
      for (let k = 0; k < 4; k++) { // head plus a short fading tail
        const tt = Math.max(0, p.t - k * 0.06);
        ctx.globalAlpha = 1 - k * 0.25;
        ctx.beginPath();
        ctx.arc(a.sx + (b.sx - a.sx) * tt, a.sy + (b.sy - a.sy) * tt, (2.6 - k * 0.5) * a.s, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    ctx.globalAlpha = 1;
    raf = requestAnimationFrame(frame);
  }

  let lifted = false;
  function lift() {
    if (lifted) return;
    lifted = true;
    root.classList.remove("booting");
    removeEventListener("keydown", onKey);
    if (!overlay) return;
    overlay.classList.add("lifting");
    setTimeout(() => { cancelAnimationFrame(raf); overlay.remove(); }, 480);
  }
  const onKey = (e) => { if (e.key === "Escape") lift(); };
  addEventListener("keydown", onKey);

  function mount() {
    if (lifted) return;
    overlay = document.createElement("div");
    overlay.className = "boot-loader";
    overlay.setAttribute("role", "status");
    overlay.innerHTML = `<canvas aria-hidden="true"></canvas><p>AI Engineering: Zero to 40</p><small>Loading. Click to skip.</small>`;
    overlay.addEventListener("click", lift);
    document.body.append(overlay);
    canvas = overlay.querySelector("canvas");
    ctx = canvas.getContext("2d");
    readColors();
    size();
    addEventListener("resize", size);
    raf = requestAnimationFrame(frame);
  }
  document.addEventListener("DOMContentLoaded", mount);

  // Lift once everything (scripts, fonts, images) has loaded and the minimum has passed; never wait past MAX_MS.
  const ready = new Promise((res) => addEventListener("load", res))
    .then(() => (document.fonts ? document.fonts.ready : null));
  ready.then(() => setTimeout(lift, Math.max(0, MIN_MS - (performance.now() - started))));
  setTimeout(lift, MAX_MS);
})();
