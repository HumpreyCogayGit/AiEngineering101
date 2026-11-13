/* AI Engineer Course — page chrome: top bar, sidebar, TOC, progress, checklists, code, diagrams. */
(function () {
  "use strict";
  const COURSE = window.COURSE;
  const body = document.body;
  const ROOT = body.dataset.root || "./";            // "../" on lecture pages
  const CURRENT = Number(body.dataset.lecture || 0);  // 0 = not a lecture page
  const ALL = COURSE.modules.flatMap((m) => m.lectures);
  const pad = (n) => String(n).padStart(3, "0");
  const lectureHref = (n) => `${ROOT}lectures/lec${pad(n)}.html`;
  const exerciseHref = (n) => `${ROOT}../EXER${pad(n)}/README.md`;

  // ------------------------------------------------------------ storage (always optional)
  const store = {
    get(key, fallback) {
      try { const v = localStorage.getItem("aic:" + key); return v === null ? fallback : JSON.parse(v); }
      catch { return fallback; }
    },
    set(key, value) { try { localStorage.setItem("aic:" + key, JSON.stringify(value)); } catch { /* ignore */ } },
  };
  const completed = () => new Set(store.get("completed", []));
  function setCompleted(n, done) {
    const s = completed();
    done ? s.add(n) : s.delete(n);
    store.set("completed", [...s]);
    refreshProgress();
  }

  // ------------------------------------------------------------ theme
  const savedTheme = store.get("theme", null);
  if (savedTheme) document.documentElement.dataset.theme = savedTheme;
  const isDark = () =>
    document.documentElement.dataset.theme === "dark" ||
    (!document.documentElement.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);

  // ------------------------------------------------------------ build chrome
  const main = document.querySelector("main");
  const topbar = document.createElement("header");
  topbar.className = "topbar";
  topbar.innerHTML = `
    <button class="icon-btn menu-btn" aria-label="Open navigation">☰</button>
    <a class="brand" href="${ROOT}index.html">AI Engineer <span>Zero to Hero</span></a>
    <div class="spacer"></div>
    <div class="progress" title="Lectures marked complete">
      <span class="progress-text"></span><div class="progress-bar"><i></i></div>
    </div>
    <button class="icon-btn theme-btn" aria-label="Toggle dark mode">◐</button>`;

  const sidebar = document.createElement("nav");
  sidebar.className = "sidebar";
  sidebar.setAttribute("aria-label", "Course navigation");
  let nav = `<div class="top-links">
      <a href="${ROOT}index.html">🏠 Course home</a>
      <a href="${ROOT}setup.html">⚙️ Setup guide</a>
      <a href="${ROOT}glossary.html">📖 Glossary</a></div>`;
  for (const m of COURSE.modules) {
    nav += `<h4>${m.title}</h4>`;
    for (const l of m.lectures) {
      nav += `<a href="${lectureHref(l.n)}" data-n="${l.n}" class="${l.n === CURRENT ? "active" : ""}">
        <span class="num">${pad(l.n)}</span><span>${l.title}</span></a>`;
    }
  }
  sidebar.innerHTML = nav;

  const layout = document.createElement("div");
  layout.className = "layout";
  const content = document.createElement("div");
  content.className = "content";
  main.parentNode.insertBefore(layout, main);
  layout.append(sidebar, content);
  content.append(main);
  body.prepend(topbar);

  topbar.querySelector(".menu-btn").addEventListener("click", () => body.classList.toggle("nav-open"));
  main.addEventListener("click", () => body.classList.remove("nav-open"));
  topbar.querySelector(".theme-btn").addEventListener("click", () => {
    const next = isDark() ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    store.set("theme", next);
    renderDiagrams(true);
  });
  const activeLink = sidebar.querySelector("a.active");
  if (activeLink) activeLink.scrollIntoView({ block: "center" });

  // ------------------------------------------------------------ progress
  function refreshProgress() {
    const done = completed();
    const count = ALL.filter((l) => done.has(l.n)).length;
    topbar.querySelector(".progress-text").textContent = `${count}/${ALL.length}`;
    topbar.querySelector(".progress-bar > i").style.width = `${(100 * count) / ALL.length}%`;
    document.querySelectorAll("[data-n]").forEach((a) => a.classList.toggle("done", done.has(Number(a.dataset.n))));
    document.querySelectorAll("[data-progress]").forEach((el) => (el.textContent = `${count} of ${ALL.length}`));
    const btn = document.querySelector(".complete-btn");
    if (btn) {
      const isDone = done.has(CURRENT);
      btn.textContent = isDone ? "✓ Completed" : "Mark lecture as complete";
      btn.classList.toggle("secondary", isDone);
    }
  }

  // ------------------------------------------------------------ lecture page extras
  if (CURRENT) {
    const info = ALL.find((l) => l.n === CURRENT);
    const module = COURSE.modules.find((m) => m.lectures.includes(info));
    document.title = `${pad(CURRENT)} · ${info.title} — AI Engineer Course`;

    // header chips
    const header = main.querySelector(".lecture-header");
    if (header && !header.querySelector(".meta")) {
      const meta = document.createElement("div");
      meta.className = "meta";
      meta.innerHTML = `<span class="chip">⏱ ~${info.minutes} min</span>
        <span class="chip">🧪 <a href="${exerciseHref(CURRENT)}">EXER${pad(CURRENT)}</a></span>
        <span class="chip">▶ <code>uv run python EXER${pad(CURRENT)}/check.py</code></span>`;
      header.append(meta);
      const kicker = header.querySelector(".kicker");
      if (kicker && !kicker.textContent.trim()) kicker.textContent = `${module.title} · Lecture ${pad(CURRENT)}`;
    }

    // completion + pager
    const idx = ALL.indexOf(info);
    const prev = ALL[idx - 1], next = ALL[idx + 1];
    const footer = document.createElement("div");
    footer.innerHTML = `
      <div class="complete-box">
        <div><strong>Finished the exercise?</strong><br><span class="lede" style="font-size:15px">
          All checks passing in <code>EXER${pad(CURRENT)}/check.py</code>? Mark it complete.</span></div>
        <button class="btn complete-btn"></button>
      </div>
      <nav class="pager">
        ${prev ? `<a class="prev" href="${lectureHref(prev.n)}"><small>← Previous</small>${pad(prev.n)} · ${prev.title}</a>` : ""}
        ${next ? `<a class="next" href="${lectureHref(next.n)}"><small>Next →</small>${pad(next.n)} · ${next.title}</a>` : ""}
      </nav>`;
    main.append(footer);
    footer.querySelector(".complete-btn").addEventListener("click", () => setCompleted(CURRENT, !completed().has(CURRENT)));

    // on-page table of contents
    const sections = [...main.querySelectorAll("h2[id], section[id] > h2")];
    if (sections.length > 2) {
      const toc = document.createElement("aside");
      toc.className = "toc";
      toc.innerHTML = "<h5>On this page</h5>" + sections.map((h) => {
        const id = h.id || h.parentElement.id;
        return `<a href="#${id}" data-target="${id}">${h.textContent}</a>`;
      }).join("");
      content.append(toc);
      const links = [...toc.querySelectorAll("a")];
      const observer = new IntersectionObserver((entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            links.forEach((a) => a.classList.toggle("active", a.dataset.target === e.target.id));
          }
        }
      }, { rootMargin: "-20% 0px -70% 0px" });
      sections.forEach((h) => observer.observe(h.id ? h : h.parentElement));
    }
  }

  // ------------------------------------------------------------ home page module list
  const moduleList = document.getElementById("module-list");
  if (moduleList) {
    moduleList.innerHTML = COURSE.modules.map((m) => {
      const mins = m.lectures.reduce((a, l) => a + l.minutes, 0);
      return `<div class="module-card"><h3>${m.title}<small>${m.lectures.length} lectures · ~${Math.round(mins / 60 * 10) / 10} h</small></h3><ol>` +
        m.lectures.map((l) => `<li><a href="${lectureHref(l.n)}" data-n="${l.n}"><span class="num">EXER${pad(l.n)}</span>${l.title}</a></li>`).join("") +
        "</ol></div>";
    }).join("");
    const totalMin = ALL.reduce((a, l) => a + l.minutes, 0);
    document.querySelectorAll("[data-total-hours]").forEach((el) => (el.textContent = Math.round(totalMin / 60)));
    document.querySelectorAll("[data-total-lectures]").forEach((el) => (el.textContent = ALL.length));
    const done = completed();
    const nextUp = ALL.find((l) => !done.has(l.n)) || ALL[0];
    const cont = document.getElementById("continue-link");
    if (cont) { cont.href = lectureHref(nextUp.n); cont.textContent = done.size ? `Continue: ${pad(nextUp.n)} · ${nextUp.title} →` : "Start with Lecture 001 →"; }
  }

  // ------------------------------------------------------------ success-criteria checklists (persisted)
  document.querySelectorAll("ul.checklist").forEach((ul, listIndex) => {
    const key = `check:${CURRENT || location.pathname}:${listIndex}`;
    const state = store.get(key, {});
    [...ul.children].forEach((li, i) => {
      const box = document.createElement("input");
      box.type = "checkbox";
      box.checked = !!state[i];
      li.classList.toggle("checked", box.checked);
      box.addEventListener("change", () => {
        state[i] = box.checked;
        li.classList.toggle("checked", box.checked);
        store.set(key, state);
      });
      li.prepend(box);
    });
  });

  // ------------------------------------------------------------ code: highlight + copy
  document.querySelectorAll("pre > code").forEach((code) => {
    if (window.hljs) window.hljs.highlightElement(code);
    const btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.type = "button";
    btn.textContent = "Copy";
    btn.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(code.innerText); btn.textContent = "Copied!"; }
      catch { btn.textContent = "Select & copy"; }
      setTimeout(() => (btn.textContent = "Copy"), 1500);
    });
    code.parentElement.append(btn);
  });

  // ------------------------------------------------------------ diagrams
  const diagrams = [...document.querySelectorAll(".mermaid")];
  diagrams.forEach((d) => (d.dataset.src = d.textContent));
  function renderDiagrams(rerender) {
    if (!window.mermaid || !diagrams.length) return;
    window.mermaid.initialize({ startOnLoad: false, theme: isDark() ? "dark" : "neutral", securityLevel: "strict",
      fontFamily: getComputedStyle(body).fontFamily });
    diagrams.forEach((d) => { if (rerender) { d.removeAttribute("data-processed"); d.textContent = d.dataset.src; } });
    window.mermaid.run({ nodes: diagrams }).catch((e) => console.warn("mermaid:", e));
  }
  renderDiagrams(false);

  refreshProgress();
})();
