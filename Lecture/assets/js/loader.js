/* AI Engineer Course — first-visit loader in three acts: points fly in and build a wire-mesh brain, signals run
   along its wires while it slowly turns, then the brain bursts and its neurons fly out to assemble a wireframe of
   the page that is waiting underneath, which fades into the real page.
   Shown once per browser session (the first page opened), finished as soon as the page has loaded and a short
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
  const MIN_MS = 3200, MAX_MS = 6000; // when the finale may start / must start
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

  // ---------------------------------------------------------------- build-up
  // Every point flies in from one of a few random origins around the brain, starting at a random moment and
  // accelerating (ease-in) until it lands. Wires appear as their two ends arrive; signals start once all have landed.
  const BUILD_STAGGER = 0.9, BUILD_FLIGHT = 0.7, BUILD_TOTAL = BUILD_STAGGER + BUILD_FLIGHT; // seconds
  const easeIn = (p) => p * p * p;
  const origins = Array.from({ length: 6 }, (_, i) => {
    const a = (i / 6) * Math.PI * 2 + Math.random() * 0.8, r = 0.95 + Math.random() * 0.3; // just inside the frame
    return { x: Math.cos(a) * r, y: Math.sin(a) * r * 0.8, z: (Math.random() - 0.5) * 1.6 };
  });
  nodes.forEach((n) => {
    const o = origins[Math.floor(Math.random() * origins.length)];
    n.fx = o.x + (Math.random() - 0.5) * 0.3;
    n.fy = o.y + (Math.random() - 0.5) * 0.3;
    n.fz = o.z + (Math.random() - 0.5) * 0.3;
    n.delay = Math.random() * BUILD_STAGGER;
    n.k = 0;          // 0 = not started .. 1 = landed (eased)
    n.landed = false;
  });

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
  // The canvas covers the whole viewport (the finale needs all of it); the brain is drawn inside `stage`.
  let overlay, canvas, stageEl, ctx, raf = 0, w = 0, h = 0, colors;
  let stage = { x: 0, y: 0, w: 0, h: 0 }, ox = 0, oy = 0;
  function readColors() {
    const cs = getComputedStyle(root);
    colors = { wire: cs.getPropertyValue("--muted").trim() || "#5a6469",
               accent: cs.getPropertyValue("--accent").trim() || "#0b6e6e" };
  }
  function size() {
    const r = canvas.getBoundingClientRect(), s = stageEl.getBoundingClientRect();
    const dpr = Math.min(devicePixelRatio || 1, 2);
    w = r.width; h = r.height;
    stage = { x: s.left - r.left, y: s.top - r.top, w: s.width, h: s.height };
    canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  const clamp01 = (v) => Math.max(0, Math.min(1, v));

  // ---------------------------------------------------------------- finale: burst, then build the page
  // The brain tightens for a moment (CHARGE), bursts, and every neuron flies to a spot on the real page's layout,
  // read from the DOM underneath: one bar per line of text, outlines for boxes, filled pills for buttons. Each
  // piece is drawn as its neurons arrive, top of the page first, so the overlay can fade straight into the page.
  const CHARGE = 0.24, BURST = 0.7, FLIGHT = 0.6, WIPE = 0.3, FINALE_MS = 1950;
  let finaleAt = 0, parts = null, blocks = [];

  function collectBlocks() {
    const out = [];
    const inView = (r) => r.width > 3 && r.height > 3 && r.bottom > 0 && r.top < h && r.right > 0 && r.left < w;
    const mine = (el) => !el.closest(".boot-loader");
    const TEXT = "h1,h2,h3,h4,p,li,dt,dd,summary,pre code,.topbar a,.sidebar a,.toc a,th,td,label";
    for (const el of document.querySelectorAll(".topbar,.sidebar,pre,table,.callout,img,svg,button,.btn.secondary")) {
      const r = el.getBoundingClientRect();
      if (mine(el) && inView(r) && !el.closest("pre svg, a svg, button svg"))
        out.push({ kind: "box", x: r.left, y: r.top, w: r.width, h: r.height });
    }
    for (const el of document.querySelectorAll(".btn:not(.secondary)")) {
      const r = el.getBoundingClientRect();
      if (mine(el) && inView(r)) out.push({ kind: "pill", x: r.left, y: r.top, w: r.width, h: r.height });
    }
    const range = document.createRange();
    for (const el of document.querySelectorAll(TEXT)) {
      if (!mine(el) || !inView(el.getBoundingClientRect())) continue;
      if (el.parentElement.closest(TEXT) || el.closest(".btn,button")) continue; // an ancestor already covers it
      const cs = getComputedStyle(el), fs = parseFloat(cs.fontSize) || 16;
      const strong = /^H[1-4]$/.test(el.tagName);
      range.selectNodeContents(el);
      const lines = []; // one merged rect per line of text
      for (const r of range.getClientRects()) {
        if (r.width < 2 || r.height < 2) continue;
        const mid = r.top + r.height / 2;
        const line = lines.find((l) => Math.abs(l.mid - mid) < fs * 0.5);
        if (line) { line.x1 = Math.min(line.x1, r.left); line.x2 = Math.max(line.x2, r.right); }
        else lines.push({ mid, x1: r.left, x2: r.right });
      }
      const th = fs * (strong ? 0.62 : 0.5);
      for (const l of lines) {
        const r = { left: l.x1, right: l.x2, top: l.mid - th / 2, bottom: l.mid + th / 2, width: l.x2 - l.x1, height: th };
        if (inView(r)) out.push({ kind: "bar", strong, x: r.left, y: r.top, w: r.width, h: th });
      }
    }
    for (const b of out) b.t = 0.28 + 0.62 * clamp01((b.y + b.h / 2) / h) + Math.random() * 0.05; // top first
    return out;
  }

  function burst() {
    blocks = collectBlocks();
    const reach = Math.hypot(w, h) * 0.36;
    parts = [];
    nodes.forEach((n, i) => {
      for (let c = 0; c < 2; c++) { // each neuron splits in two
        const a = Math.atan2(n.sy - oy, n.sx - ox) + (Math.random() - 0.5) * 1.1;
        const d = (0.25 + Math.random()) * reach;
        const p = { x0: n.sx, y0: n.sy, dx: Math.cos(a) * d, dy: Math.sin(a) * d, x: n.sx, y: n.sy,
                    r: (1.6 + Math.random() * 1.4) * (c ? 0.75 : 1), node: c ? -1 : i, tx: 0, ty: 0, t0: 0, home: false };
        const b = blocks.length ? blocks[parts.length % blocks.length] : null;
        if (b) {
          const u = Math.random();
          p.tx = b.x + u * b.w; p.ty = b.y + (b.kind === "bar" ? 0.5 : Math.random()) * b.h;
          p.t0 = b.t - 0.35 + u * 0.2; p.home = true;
        }
        parts.push(p);
      }
    });
  }

  function roundRect(x, y, bw, bh, r) {
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(x, y, bw, bh, Math.min(r, bw / 2, bh / 2)); else ctx.rect(x, y, bw, bh);
  }

  function drawFinale(e) { // e: seconds since the burst
    const pe = clamp01(e / BURST), out = 1 - (1 - pe) ** 3;
    ctx.clearRect(0, 0, w, h);
    ctx.lineCap = "round";
    // the page, piece by piece
    for (const b of blocks) {
      const g = clamp01((e - b.t - 0.2) / WIPE);
      if (g <= 0) continue;
      const grow = 1 - (1 - g) ** 2;
      if (b.kind === "bar") {
        ctx.globalAlpha = b.strong ? 0.55 : 0.26;
        ctx.fillStyle = colors.wire;
        roundRect(b.x, b.y, b.w * grow, b.h, b.h / 2); ctx.fill();
      } else if (b.kind === "pill") {
        ctx.globalAlpha = 0.7 * g;
        ctx.fillStyle = colors.accent;
        roundRect(b.x, b.y, b.w * grow, b.h, 5); ctx.fill();
      } else {
        ctx.fillStyle = ctx.strokeStyle = colors.wire;
        ctx.lineWidth = 1;
        roundRect(b.x + .5, b.y + .5, b.w * grow, b.h, 4);
        ctx.globalAlpha = 0.05 * g; ctx.fill();
        ctx.globalAlpha = 0.35 * g; ctx.stroke();
      }
    }
    // shock ring
    if (pe < 1) {
      ctx.globalAlpha = (1 - pe) * 0.4;
      ctx.strokeStyle = colors.accent;
      ctx.lineWidth = 1 + (1 - pe) * 3;
      ctx.beginPath(); ctx.arc(ox, oy, 12 + out * Math.hypot(w, h) * 0.5, 0, Math.PI * 2); ctx.stroke();
    }
    for (const p of parts) {
      const k = p.home ? clamp01((e - p.t0) / FLIGHT) : 0;
      const kk = k < .5 ? 4 * k * k * k : 1 - ((-2 * k + 2) ** 3) / 2;
      p.x = (p.x0 + p.dx * out) * (1 - kk) + p.tx * kk;
      p.y = (p.y0 + p.dy * out) * (1 - kk) + p.ty * kk;
    }
    // the wires stretch and snap
    const snap = 1 - e / 0.22;
    if (snap > 0) {
      ctx.strokeStyle = colors.accent;
      ctx.lineWidth = 1;
      ctx.globalAlpha = snap * 0.6;
      ctx.beginPath();
      for (const ed of edges) {
        const a = parts[ed.a * 2], b = parts[ed.b * 2];
        ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
      }
      ctx.stroke();
    }
    ctx.fillStyle = colors.accent;
    for (const p of parts) {
      // neurons dissolve into the piece they land on; ones without a target fade as they fly off
      const fade = p.home ? 1 - clamp01((e - p.t0 - FLIGHT) / 0.22) : 1 - pe;
      if (fade <= 0) continue;
      ctx.globalAlpha = (0.55 + 0.45 * (1 - pe)) * fade;
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r * (1 + (1 - pe) * 1.3), 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
  }

  let last = 0, spawn = 0, mountedAt = 0;
  function frame(now) {
    const dt = Math.min(.05, (now - (last || now)) / 1000);
    last = now;
    const t = (now - started) / 1000;
    const bt = (now - mountedAt) / 1000; // time since the loader appeared
    const f = finaleAt ? (now - finaleAt) / 1000 : -1; // seconds into the finale
    if (f >= CHARGE) {
      if (!parts) burst();
      drawFinale(f - CHARGE);
      raf = requestAnimationFrame(frame);
      return;
    }
    const charge = f < 0 ? 0 : (f / CHARGE) ** 2; // 0..1: the brain tightens and lights up before it bursts
    const ry = -0.35 + Math.sin(t * 0.7) * 0.55, rx = 0.12;
    const cy = Math.cos(ry), sy = Math.sin(ry), cx = Math.cos(rx), sx = Math.sin(rx);
    const scale = Math.min(stage.w / 2.3, stage.h / 1.85) * (1 - 0.16 * charge);
    ox = stage.x + stage.w / 2; oy = stage.y + stage.h * 0.45;
    for (const n of nodes) {
      const p = Math.max(0, Math.min(1, (bt - n.delay) / BUILD_FLIGHT));
      n.k = p > 0 ? Math.max(0.001, easeIn(p)) : 0;
      if (p === 1 && !n.landed) { n.landed = true; n.glow = 1; } // small flash on landing
      const x = n.fx + (n.x - n.fx) * n.k, y = n.fy + (n.y - n.fy) * n.k, z = n.fz + (n.z - n.fz) * n.k;
      const x1 = x * cy - z * sy, z1 = z * cy + x * sy;
      const y2 = y * cx - z1 * sx, z2 = z1 * cx + y * sx;
      n.s = 3.2 / (3.2 - Math.max(-2, Math.min(2, z2)));
      n.sx = ox + x1 * scale * n.s; n.sy = oy + y2 * scale * n.s; n.sz = z2;
      n.glow = Math.max(charge, n.glow - dt * 1.6);
    }
    spawn += dt;
    if (bt > BUILD_TOTAL && spawn > 0.11) { spawn = 0; fire(Math.floor(Math.random() * nodes.length), 5, -1); }
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
      const built = Math.max(0, Math.min(1, (Math.min(a.k, b.k) - 0.8) / 0.2)); // only once both ends have nearly landed
      if (built <= 0) continue;
      e.heat = Math.max(charge, e.heat - dt * 1.2);
      ctx.globalAlpha = (0.12 + d * 0.38 + e.heat * 0.35) * built;
      ctx.strokeStyle = e.heat > .05 ? colors.accent : colors.wire;
      ctx.lineWidth = (0.6 + d * 0.7) * a.s;
      ctx.beginPath(); ctx.moveTo(a.sx, a.sy); ctx.lineTo(b.sx, b.sy); ctx.stroke();
    }
    for (const n of nodes) {
      if (n.k <= 0) continue;
      const d = depth(Math.max(-.65, Math.min(.65, n.sz)));
      ctx.globalAlpha = (0.3 + d * 0.6) * (0.35 + 0.65 * n.k);
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
    overlay.innerHTML = `<canvas aria-hidden="true"></canvas><div class="boot-stage"></div><p>AI Engineering: Building with LLMs</p><small>Loading. Click to skip.</small>`;
    overlay.addEventListener("click", lift);
    document.body.append(overlay);
    canvas = overlay.querySelector("canvas");
    stageEl = overlay.querySelector(".boot-stage");
    ctx = canvas.getContext("2d");
    readColors();
    size();
    addEventListener("resize", size);
    mountedAt = performance.now();
    raf = requestAnimationFrame(frame);
  }
  document.addEventListener("DOMContentLoaded", mount);

  // Play the finale, then lift. It waits for the brain to finish building; the lift itself runs on a timer so a
  // background tab (where animation frames pause) still gets its page.
  function finale() {
    if (lifted || finaleAt) return;
    if (!overlay || !w) return lift();
    const wait = mountedAt + (BUILD_TOTAL + 0.6) * 1000 - performance.now();
    if (wait > 0) return void setTimeout(finale, wait);
    finaleAt = performance.now();
    overlay.classList.add("finale");
    setTimeout(lift, FINALE_MS);
  }

  // Start it once everything (scripts, fonts, images) has loaded and the minimum has passed; never wait past MAX_MS.
  const ready = new Promise((res) => addEventListener("load", res))
    .then(() => (document.fonts ? document.fonts.ready : null));
  ready.then(() => setTimeout(finale, Math.max(0, MIN_MS - (performance.now() - started))));
  setTimeout(finale, MAX_MS);
})();
