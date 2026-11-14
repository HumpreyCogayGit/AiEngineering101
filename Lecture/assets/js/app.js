/* AI Engineer Course — page chrome: top bar, sidebar, TOC, progress, quizzes, checklists, code, diagrams. */
(function () {
  "use strict";
  const COURSE = window.COURSE;
  const body = document.body;
  const ROOT = body.dataset.root || "./";            // "../" on lecture pages
  const CURRENT = Number(body.dataset.lecture || 0);  // 0 = not a lecture page
  const ALL = COURSE.modules.flatMap((m) => m.lectures);
  const pad = (n) => String(n).padStart(3, "0");
  const lectureHref = (n) => `${ROOT}lectures/lec${pad(n)}.html`;
  // Exercises live outside Lecture/, which is all GitHub Pages publishes. Opened from disk, link the local
  // README; served over http(s), link the exercise folder in the repository instead.
  const REPO = "https://github.com/HumpreyCogayGit/AiEngineering101/tree/main";
  const exerciseHref = (n) => location.protocol === "file:"
    ? `${ROOT}../EXER${pad(n)}/README.md`
    : `${REPO}/EXER${pad(n)}`;

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
  // Quiz scores live next to "completed": { "4": { score: 3, total: 4 }, ... }. They never gate completion.
  const quizScores = () => store.get("quiz", {});
  function setQuizScore(n, score, total) {
    const all = quizScores();
    all[n] = { score, total };
    store.set("quiz", all);
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
    <a class="brand" href="${ROOT}index.html">AI Engineering: Building with LLMs</a>
    <div class="spacer"></div>
    <div class="progress" title="Lectures marked complete">
      <span class="progress-text"></span><div class="progress-bar"><i></i></div>
    </div>
    <button class="icon-btn theme-btn" aria-label="Toggle dark mode">◐</button>`;

  const sidebar = document.createElement("nav");
  sidebar.className = "sidebar";
  sidebar.setAttribute("aria-label", "Course navigation");
  let nav = `<div class="top-links">
      <a href="${ROOT}index.html">Course home</a>
      <a href="${ROOT}setup.html">Setup guide</a>
      <a href="${ROOT}glossary.html">Glossary</a></div>`;
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
    const scores = quizScores();
    document.querySelectorAll("[data-quiz]").forEach((el) => {
      const s = scores[el.dataset.quiz];
      el.textContent = s ? `quiz ${s.score}/${s.total}` : "";
      el.title = s ? `Self-check quiz: ${s.score} of ${s.total} correct on your last attempt` : "";
      el.classList.toggle("full", !!s && s.score === s.total);
    });
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
    document.title = `Lecture ${CURRENT}: ${info.title} – AI Engineering: Building with LLMs`;

    // header: where you are (module link / position), then one plain sentence about time and the exercise
    const header = main.querySelector(".lecture-header");
    if (header && !header.querySelector(".meta")) {
      const crumb = document.createElement("p");
      crumb.className = "lecture-crumb";
      crumb.innerHTML = `<a href="${ROOT}index.html#module-${COURSE.modules.indexOf(module)}">${module.title}</a>
        <span aria-hidden="true">/</span> Lecture ${CURRENT} of ${ALL.length}`;
      header.prepend(crumb);
      const meta = document.createElement("p");
      meta.className = "meta";
      meta.innerHTML = `About ${info.minutes} minutes, plus exercise
        <a href="${exerciseHref(CURRENT)}">EXER${pad(CURRENT)}</a>. Check your work with
        <code>uv run python EXER${pad(CURRENT)}/check.py</code>.`;
      header.append(meta);
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
        ${prev ? `<a class="prev" href="${lectureHref(prev.n)}"><small>Previous</small><span class="pager-no">${pad(prev.n)}</span><span class="pager-title">${prev.title}</span></a>` : ""}
        ${next ? `<a class="next" href="${lectureHref(next.n)}"><small>Next</small><span class="pager-no">${pad(next.n)}</span><span class="pager-title">${next.title}</span></a>` : ""}
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
    moduleList.innerHTML = COURSE.modules.map((m, mi) => {
      const mins = m.lectures.reduce((a, l) => a + l.minutes, 0);
      const hours = Math.round(mins / 60 * 10) / 10;
      return `<section class="module" id="module-${mi}"><h3>${m.title}</h3>` +
        `<p class="module-meta">${m.lectures.length} lectures, about ${hours} ${hours === 1 ? "hour" : "hours"}</p><ol>` +
        m.lectures.map((l) => `<li><a href="${lectureHref(l.n)}" data-n="${l.n}"><span class="num">${pad(l.n)}</span><span class="title">${l.title}</span><span class="quiz-score" data-quiz="${l.n}"></span></a></li>`).join("") +
        "</ol></section>";
    }).join("");
    const totalMin = ALL.reduce((a, l) => a + l.minutes, 0);
    document.querySelectorAll("[data-total-hours]").forEach((el) => (el.textContent = Math.round(totalMin / 60)));
    document.querySelectorAll("[data-total-lectures]").forEach((el) => (el.textContent = ALL.length));
    const done = completed();
    const nextUp = ALL.find((l) => !done.has(l.n)) || ALL[0];
    const cont = document.getElementById("continue-link");
    if (cont) { cont.href = lectureHref(nextUp.n); cont.textContent = done.size ? `Continue with ${pad(nextUp.n)}: ${nextUp.title}` : "Start Lecture 001"; }
  }

  // ------------------------------------------------------------ self-check quiz (data in quizzes.js)
  // Text in quizzes.js is plain text; `backticks` become <code>.
  const esc = (t) => String(t).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const rich = (t) => esc(t).replace(/`([^`]+)`/g, "<code>$1</code>");
  const quizBox = document.getElementById("quiz-box");
  const QUIZ = (window.QUIZZES || {})[CURRENT];
  function renderQuiz() {
    let answered = 0, score = 0;
    const last = quizScores()[CURRENT];
    quizBox.innerHTML = `
      <p class="quiz-intro">${QUIZ.length} questions, about two minutes. It is for you, not a grade: your first
        choice counts, the explanation appears straight away, and nothing here blocks "Mark as complete".</p>
      <ol class="quiz"></ol>
      <div class="quiz-result"><span class="quiz-status">${last ? `Last attempt: ${last.score}/${last.total}` : ""}</span>
        <button class="btn secondary quiz-retry" type="button" hidden>Try again</button></div>`;
    const list = quizBox.querySelector(".quiz");
    const status = quizBox.querySelector(".quiz-status");
    const retry = quizBox.querySelector(".quiz-retry");
    retry.addEventListener("click", () => { renderQuiz(); quizBox.scrollIntoView({ block: "start" }); });

    QUIZ.forEach((item) => {
      const li = document.createElement("li");
      li.className = "quiz-q";
      // Shuffle the options so the position of the right answer says nothing.
      const order = item.options.map((_, i) => i);
      for (let i = order.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [order[i], order[j]] = [order[j], order[i]];
      }
      li.innerHTML = `<p class="quiz-text">${rich(item.q)}</p><div class="quiz-options"></div>
        <div class="quiz-why" aria-live="polite" hidden></div>`;
      const options = li.querySelector(".quiz-options");
      const why = li.querySelector(".quiz-why");
      order.forEach((i) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "quiz-opt";
        btn.innerHTML = rich(item.options[i]);
        btn.addEventListener("click", () => {
          const right = i === item.answer;
          [...options.children].forEach((b, pos) => {
            b.disabled = true;
            if (order[pos] === item.answer) b.classList.add("correct");
          });
          if (!right) btn.classList.add("wrong");
          li.classList.add(right ? "is-right" : "is-wrong");
          why.hidden = false;
          why.innerHTML = right
            ? `<strong>Correct.</strong> ${rich(item.why[i])}`
            : `<strong>Not quite.</strong> ${rich(item.why[i])}<br><strong>The answer:</strong> ${rich(item.options[item.answer])}. ${rich(item.why[item.answer])}`;
          answered += 1;
          if (right) score += 1;
          if (answered === QUIZ.length) {
            setQuizScore(CURRENT, score, QUIZ.length);
            status.textContent = `You got ${score} of ${QUIZ.length}.` +
              (score === QUIZ.length ? " The concept landed: on to the exercise." : " Re-read the parts you missed, then try again.");
            retry.hidden = false;
          } else {
            status.textContent = `${answered} of ${QUIZ.length} answered`;
          }
        });
        options.append(btn);
      });
      list.append(li);
    });
  }
  if (quizBox && QUIZ) renderQuiz();

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
