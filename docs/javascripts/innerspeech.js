/* Interactive figures of the Inner Speech Dataset docs.
 *
 * Every figure is a <div data-viz="..."> in the Markdown pages; this script
 * draws it. No external libraries. Colours come from CSS custom properties in
 * stylesheets/extra.css, so the figures follow the light/dark switch.
 */
(function () {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";

  function svg(tag, attrs, parent) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v !== undefined && v !== null) node.setAttribute(k, v);
    }
    if (parent) parent.appendChild(node);
    return node;
  }

  function text(parent, x, y, content, attrs) {
    const node = svg("text", Object.assign({ x, y }, attrs || {}), parent);
    node.textContent = content;
    return node;
  }

  function html(tag, attrs, content) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v !== undefined && v !== null) node.setAttribute(k, v);
    }
    if (content !== undefined) node.innerHTML = content;
    return node;
  }

  function esc(value) {
    return String(value).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  }

  /* --------------------------- tooltip --------------------------- */

  let tooltip = null;
  function showTip(event, content) {
    if (!tooltip) {
      tooltip = html("div", { class: "is-tooltip", role: "tooltip" });
      document.body.appendChild(tooltip);
    }
    tooltip.innerHTML = content;
    tooltip.classList.add("is-visible");
    const pad = 14;
    const rect = tooltip.getBoundingClientRect();
    let x = event.clientX + pad;
    let y = event.clientY + pad;
    if (x + rect.width > window.innerWidth - 8) x = event.clientX - rect.width - pad;
    if (y + rect.height > window.innerHeight - 8) y = event.clientY - rect.height - pad;
    tooltip.style.left = Math.max(8, x) + "px";
    tooltip.style.top = Math.max(8, y) + "px";
  }
  function hideTip() {
    if (tooltip) tooltip.classList.remove("is-visible");
  }

  /* -------------------- shared protocol facts -------------------- */

  const CONDITIONS = [
    { key: "pronounced", label: "Pronounced speech", short: "Pronounced", css: "pron" },
    { key: "inner", label: "Inner speech", short: "Inner", css: "inner" },
    { key: "visualized", label: "Visualized condition", short: "Visualized", css: "vis" },
  ];

  const CODE_NAMES = {
    11: "protocol start", 12: "protocol end", 13: "baseline start", 14: "baseline end",
    15: "run start", 16: "run end", 17: "control question",
    21: "pronounced run", 22: "inner run", 23: "visualized run",
    31: "cue up", 32: "cue down", 33: "cue right", 34: "cue left",
    42: "concentration (trial start)", 44: "action", 45: "relax", 46: "rest",
    51: "rest between runs", 61: "answer up", 62: "answer down", 63: "answer right",
    64: "answer left", 65536: "spurious trigger",
  };

  /* Draw the screen the participant saw in one interval (64 x 48 box). */
  function drawScreen(parent, x, y, w, h, kind) {
    const g = svg("g", { transform: `translate(${x},${y})` }, parent);
    svg("rect", { width: w, height: h, rx: 5, fill: "var(--is-screen)", stroke: "var(--is-border)" }, g);
    const cx = w / 2;
    const cy = h / 2;
    if (kind === "triangle") {
      const s = h * 0.36;
      svg("path", {
        d: `M${cx} ${cy - s} L${cx + s * 1.05} ${cy + s * 0.75} L${cx - s * 1.05} ${cy + s * 0.75} Z`,
        fill: "none", stroke: "#fff", "stroke-width": 1.6, "stroke-linejoin": "round",
      }, g);
      svg("circle", { cx, cy: cy + 2, r: 2, fill: "#fff" }, g);
    } else if (kind === "circle") {
      svg("circle", { cx, cy, r: 2.6, fill: "#fff" }, g);
    } else if (kind === "blue") {
      svg("circle", { cx, cy, r: 3.2, fill: "var(--is-relax)" }, g);
    } else if (kind === "word") {
      const t = text(g, cx, cy + 4, "Inner speech", { "text-anchor": "middle" });
      t.setAttribute("style", "fill:#fff;font-size:8.5px");
    }
    return g;
  }

  /* ------------------------ trial timeline ------------------------ */

  const INTERVALS = [
    {
      key: "concentration", name: "Concentration", start: 0, end: 0.5, code: "42", screen: "circle",
      text: "A white circle appears at the centre of the screen. The participant fixes the gaze on it and must not blink until the trial ends.",
    },
    {
      key: "cue", name: "Cue", start: 0.5, end: 1.0, code: "31–34", screen: "triangle",
      text: "A white triangle points up, down, right or left: the class (word) of the trial. The code tells which: 31 up, 32 down, 33 right, 34 left.",
    },
    {
      key: "action", name: "Action", start: 1.0, end: 3.5, code: "44", screen: "circle",
      text: "The triangle disappears and the participant performs the task: says the word aloud (pronounced speech), repeats it with the inner voice (inner speech) or mentally moves the circle in that direction (visualized condition). This is the interval most analyses use.",
    },
    {
      key: "relax", name: "Relax", start: 3.5, end: 4.5, code: "45", screen: "blue",
      text: "The circle turns blue: stop the task, but keep the gaze fixed and do not blink yet.",
    },
    {
      key: "rest", name: "Rest", start: 4.5, end: 6.5, code: "46", screen: "blank", variable: true,
      text: "The circle disappears and the participant may blink. The rest lasts 1.5 to 2 s; then the next trial starts with a new concentration interval.",
    },
  ];

  function trialTimeline(root) {
    const W = 700;
    const left = 104;
    const right = 18;
    const tMax = 6.5;
    const x = (t) => left + (t / tMax) * (W - left - right);

    const frame = html("div", { class: "is-scroll" });
    const s = svg("svg", { viewBox: `0 0 ${W} 282`, role: "img", "aria-label": "Timeline of one trial: concentration 0.5 s, cue 0.5 s, action 2.5 s, relax 1 s, rest 1.5 to 2 s" }, frame);
    const info = html("div", { class: "is-info", "aria-live": "polite" });
    const defaultInfo = "<b>Hover or tap an interval</b> to see what the participant saw and did. Times are from the start of the trial (top axis) and from the cue (bottom axis, the time axis of the epoch files).";
    info.innerHTML = defaultInfo;

    const segs = svg("g", {}, s);
    const yScreen = 8;
    const yBar = 74;
    const barH = 34;

    // interval bars, screens and labels
    const groups = INTERVALS.map((iv) => {
      const g = svg("g", { class: "is-seg is-hit", tabindex: 0, role: "button", "aria-label": `${iv.name} interval` }, segs);
      const x0 = x(iv.start);
      const x1 = x(iv.end);
      const w = x1 - x0;
      svg("rect", { x: x0, y: 0, width: w, height: 140, fill: "transparent" }, g);
      const sw = Math.min(62, w - 6);
      drawScreen(g, x0 + (w - sw) / 2, yScreen, sw, 48, iv.screen);
      const isAction = iv.key === "action";
      const bar = svg("rect", {
        x: x0 + 1, y: yBar, width: w - 2, height: barH, rx: 4,
        fill: isAction ? "var(--is-highlight)" : "var(--is-surface-2)",
        "fill-opacity": isAction ? 0.22 : 1,
        stroke: isAction ? "var(--is-highlight)" : "var(--is-border)",
      }, g);
      if (iv.variable) {
        // the last 0.25 s of the rest is only sometimes present
        svg("rect", { x: x(6.0), y: yBar + 1, width: x(6.5) - x(6.0) - 2, height: barH - 2, fill: "var(--is-surface)", opacity: 0.55 }, g);
      }
      const dur = iv.variable ? "1.5–2 s" : `${(iv.end - iv.start).toFixed(1).replace(".0", "")} s`;
      text(g, x0 + w / 2, yBar + 15, iv.code, { "text-anchor": "middle", class: "t-strong" });
      text(g, x0 + w / 2, yBar + 28, dur, { "text-anchor": "middle", class: "t-muted" });
      // the two short intervals get their names on separate rows
      const row = iv.key === "cue" ? 2 : 1;
      const anchor = iv.key === "concentration" ? "start" : "middle";
      const lx = anchor === "start" ? x0 + 1 : x0 + w / 2;
      text(g, lx, yBar + barH + (row === 1 ? 15 : 29), iv.name, { "text-anchor": anchor, class: "t-strong" });
      return { g, iv, bar };
    });

    function activate(item) {
      segs.classList.add("is-dim");
      groups.forEach((o) => o.g.classList.toggle("is-active", o === item));
      const iv = item.iv;
      const span = iv.variable ? "4.5 to 6.0–6.5 s" : `${iv.start} to ${iv.end} s`;
      const cue = iv.variable ? "4.0 to 5.5–6.0 s" : `${(iv.start - 0.5).toFixed(1)} to ${(iv.end - 0.5).toFixed(1)} s`;
      info.innerHTML = `<b>${iv.name}</b> · trigger <code>${iv.code}</code> · trial time ${span} · from the cue ${cue}<br>${esc(iv.text)}`;
    }
    function reset() {
      segs.classList.remove("is-dim");
      groups.forEach((o) => o.g.classList.remove("is-active"));
      info.innerHTML = defaultInfo;
    }
    groups.forEach((o) => {
      o.g.addEventListener("mouseenter", () => activate(o));
      o.g.addEventListener("focus", () => activate(o));
      o.g.addEventListener("click", () => activate(o));
      o.g.addEventListener("mouseleave", reset);
      o.g.addEventListener("blur", reset);
    });

    // axes
    function axis(y, label, offset, ticks) {
      svg("line", { x1: x(0), x2: x(tMax), y1: y, y2: y, class: "axis" }, s);
      text(s, left - 12, y + 4, label, { "text-anchor": "end", class: "t-muted" });
      ticks.forEach((t) => {
        svg("line", { x1: x(t), x2: x(t), y1: y, y2: y + 4, class: "axis" }, s);
        const v = t - offset;
        text(s, x(t), y + 16, (Math.abs(v) < 1e-9 ? 0 : v).toString(), { "text-anchor": "middle" });
      });
    }
    const ticks = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6];
    axis(150, "trial time (s)", 0, ticks);
    axis(186, "from the cue (s)", 0.5, ticks);
    // cue marker
    svg("line", { x1: x(0.5), x2: x(0.5), y1: 176, y2: 186, stroke: "var(--is-ink)", "stroke-width": 2 }, s);

    // brackets
    function bracket(y, t0, t1, label, color) {
      svg("path", {
        d: `M${x(t0)} ${y - 5} V${y} H${x(t1)} V${y - 5}`,
        fill: "none", stroke: color, "stroke-width": 2, "stroke-linejoin": "round",
      }, s);
      text(s, x(t0) + 4, y + 15, label, { class: "t-strong" });
    }
    bracket(226, 0, 4.5, "Epoch in the *-epo.fif files: −0.5 to 4.0 s from the cue (1153 samples)", "var(--is-ink-2)");
    bracket(262, 1.0, 3.5, "EMG control window", "var(--is-highlight)");

    root.appendChild(frame);
    root.appendChild(info);
  }

  /* ----------------------- session structure ----------------------- */

  function sessionStructure(root) {
    const W = 700;
    const left = 4;
    const right = 10;
    // approximate durations in seconds (a full session lasts about 1600 s)
    const parts = [
      { kind: "baseline", label: "Baseline", dur: 15, codes: "13 → 14", text: "15 s of rest with the eyes open, at the start of every session (codes 13 and 14). Stored in baseline-epo.fif and used as the reference of the EMG control." },
      { kind: "gap", dur: 8 },
      { kind: "run", cond: 0, label: "Run 1", dur: 250, codes: "15 · 21 … 16", text: "Pronounced speech: the participant says the word aloud. 40 trials, no control questions." },
      { kind: "break", dur: 60 },
      { kind: "run", cond: 1, label: "Run 2", dur: 265, q: [7, 19, 31], codes: "15 · 22 … 16", text: "Inner speech: 40 trials. After a few random trials a control question asks for the direction of the last cue (code 17, answers 61–64)." },
      { kind: "break", dur: 60 },
      { kind: "run", cond: 1, label: "Run 3", dur: 265, q: [11, 26], codes: "15 · 22 … 16", text: "Inner speech: 40 trials with random control questions." },
      { kind: "break", dur: 60 },
      { kind: "run", cond: 2, label: "Run 4", dur: 265, q: [5, 22, 34], codes: "15 · 23 … 16", text: "Visualized condition: the participant mentally moves the circle in the direction of the cue. 40 trials with random control questions." },
      { kind: "break", dur: 60 },
      { kind: "run", cond: 2, label: "Run 5", dur: 265, q: [15, 29], codes: "15 · 23 … 16", text: "Visualized condition: 40 trials with random control questions." },
    ];
    const total = parts.reduce((a, p) => a + p.dur, 0);
    const scale = (W - left - right) / total;

    const frame = html("div", { class: "is-scroll" });
    const s = svg("svg", { viewBox: `0 0 ${W} 136`, role: "img", "aria-label": "One session: a 15 s baseline, then five runs of 40 trials: pronounced, inner, inner, visualized, visualized, with one-minute breaks" }, frame);
    const info = html("div", { class: "is-info", "aria-live": "polite" });
    const defaultInfo = "<b>Hover or tap a block.</b> Every session has the same structure; only the number of trials per run changes in some third sessions.";
    info.innerHTML = defaultInfo;

    const segs = svg("g", {}, s);
    let cursor = left;
    const yBar = 34;
    const barH = 40;
    const items = [];
    parts.forEach((p) => {
      const w = p.dur * scale;
      const x0 = cursor;
      cursor += w;
      if (p.kind === "gap") return;
      if (p.kind === "break") {
        const g = svg("g", { class: "is-seg is-hit", tabindex: 0, role: "button", "aria-label": "Break between runs" }, segs);
        svg("rect", { x: x0, y: yBar - 20, width: w, height: barH + 50, fill: "transparent" }, g);
        svg("line", { x1: x0 + 4, x2: x0 + w - 4, y1: yBar + barH / 2, y2: yBar + barH / 2, stroke: "var(--is-ink-3)", "stroke-dasharray": "3 3" }, g);
        text(g, x0 + w / 2, yBar + barH + 18, "51", { "text-anchor": "middle", class: "t-muted" });
        items.push({ g, html: "<b>Break between runs</b> · code <code>51</code><br>About one minute of rest. The next run starts with code 15 and the run type (21, 22 or 23); the screen announces the condition for 3 s." });
        return;
      }
      const g = svg("g", { class: "is-seg is-hit", tabindex: 0, role: "button", "aria-label": p.label }, segs);
      svg("rect", { x: x0, y: 0, width: w, height: 100, fill: "transparent" }, g);
      if (p.kind === "baseline") {
        svg("rect", { x: x0, y: yBar, width: w, height: barH, rx: 3, fill: "var(--is-ink-3)" }, g);
        svg("path", { d: `M${x0 + w / 2} ${yBar + barH + 2} V${yBar + barH + 26}`, stroke: "var(--is-ink-3)" }, g);
        text(g, x0, yBar + barH + 38, "Baseline 15 s (13 → 14)", { class: "t-strong" });
        items.push({ g, html: `<b>Baseline</b> · codes <code>13</code> → <code>14</code><br>${esc(p.text)}` });
        return;
      }
      const c = CONDITIONS[p.cond];
      svg("rect", { x: x0, y: yBar, width: w, height: barH, rx: 4, fill: `var(--is-${c.css})` }, g);
      // 40 trial ticks
      for (let i = 1; i < 40; i++) {
        const tx = x0 + (i * w) / 40;
        svg("line", { x1: tx, x2: tx, y1: yBar + 6, y2: yBar + barH - 6, stroke: "var(--is-surface)", "stroke-opacity": 0.45, "stroke-width": 1 }, g);
      }
      (p.q || []).forEach((i) => {
        const qx = x0 + (i * w) / 40;
        svg("path", { d: `M${qx} ${yBar - 7} l4 4 l-4 4 l-4 -4 Z`, fill: "var(--is-ink)" }, g);
      });
      text(g, x0, yBar - 8, `${p.label} · ${c.short}`, { class: "t-strong" });
      text(g, x0, yBar + barH + 18, p.codes, { class: "t-muted" });
      items.push({ g, html: `<b>${p.label}: ${c.label}</b> · codes <code>${p.codes}</code><br>${esc(p.text)}` });
    });

    // legend for the question marker
    const lg = svg("g", {}, s);
    svg("path", { d: `M${W - 228} ${122} l4 4 l-4 4 l-4 -4 Z`, fill: "var(--is-ink)" }, lg);
    text(lg, W - 218, 130, "control question (17) and answer (61–64)", { class: "t-muted" });

    function activate(item) {
      segs.classList.add("is-dim");
      items.forEach((o) => o.g.classList.toggle("is-active", o === item));
      info.innerHTML = item.html;
    }
    function reset() {
      segs.classList.remove("is-dim");
      items.forEach((o) => o.g.classList.remove("is-active"));
      info.innerHTML = defaultInfo;
    }
    items.forEach((o) => {
      o.g.addEventListener("mouseenter", () => activate(o));
      o.g.addEventListener("focus", () => activate(o));
      o.g.addEventListener("click", () => activate(o));
      o.g.addEventListener("mouseleave", reset);
      o.g.addEventListener("blur", reset);
    });

    root.appendChild(frame);
    root.appendChild(info);
  }

  /* ------------------------ sessions overview ------------------------ */

  const SESSION_NOTES = {
    "1-1": "Most control questions of all sessions (45). After this session sub-01 found them too many, so fewer were asked from then on. sub-01 and sub-10 pressed a key by accident at the first two questions of session 1.",
    "1-3": "Shorter session (100 trials, 20 per run). The .bdf file ends with an incomplete 1 s data record: recent MNE versions drop it, so the recording reads as 969 s.",
    "3-1": "The participant performed the second inner speech run (trials 80–119) as visualized condition. The derivatives carry the corrected label: 40 inner and 120 visualized trials.",
    "3-3": "Shorter session (100 trials). To balance session 1, three runs were inner speech and one visualized. The baseline is highly contaminated (paper).",
    "6-3": "Shorter session (140 trials, 28 per run).",
    "8-2": "The baseline is highly contaminated (paper).",
    "8-3": "Shorter session (100 trials, 20 per run).",
    "10-1": "A spurious trigger overlaps the end of the baseline. Events shorter than 2 ms are ignored when reading, which also drops the baseline end; the correction re-inserts it. sub-01 and sub-10 pressed a key by accident at the first two questions of session 1.",
  };

  const METRICS = [
    {
      key: "trials", label: "Trials",
      value: (s) => s.trials,
      fmt: (s) => String(s.trials),
      describe: "Trials per session (200 when complete: 40 per run).",
    },
    {
      key: "emg", label: "EMG-tagged",
      value: (s) => s.emg_tagged,
      fmt: (s) => String(s.emg_tagged),
      describe: "Inner speech and visualized trials tagged by the EMG control (mouth movement above the baseline mean + 3 SD).",
    },
    {
      key: "corrections", label: "Event corrections",
      value: (s) => (s.corrections ? inserted(s).length : null),
      fmt: (s) => (s.corrections ? String(inserted(s).length) : "–"),
      describe: "Missing triggers re-inserted by the event correction (the spurious code 65536 is ignored and not counted).",
    },
    {
      key: "answers", label: "Control answers",
      value: (s) => s.answers_wrong,
      fmt: (s) => `${s.answers_right}/${s.answers_wrong}`,
      describe: "Right / wrong answers to the attention questions; the colour shows the wrong ones.",
    },
    {
      key: "time", label: "Recording time",
      value: (s) => s.recording_time,
      fmt: (s) => minutes(s.recording_time),
      describe: "Length of the raw recording.",
    },
  ];

  function inserted(s) {
    return (s.corrections || []).filter((c) => c.action !== "ignored");
  }

  function minutes(sec) {
    const m = Math.floor(sec / 60);
    const r = String(sec % 60).padStart(2, "0");
    return `${m}:${r}`;
  }

  function level(value, max) {
    if (value === null || value === undefined) return -1;
    if (max <= 0 || value <= 0) return 0;
    return Math.min(4, 1 + Math.floor((value / max) * 3.999));
  }

  function sessionsOverview(root) {
    const src = root.getAttribute("data-src");
    root.innerHTML = '<p class="is-figure__sub">Loading the session summary…</p>';
    fetch(src)
      .then((r) => {
        if (!r.ok) throw new Error(r.status);
        return r.json();
      })
      .then((data) => drawSessions(root, data.sessions))
      .catch(() => {
        root.innerHTML = '<p class="is-figure__sub">The session summary could not be loaded. The same numbers are in the table below.</p>';
      });
  }

  function drawSessions(root, sessions) {
    root.innerHTML = "";
    const byKey = new Map(sessions.map((s) => [`${s.subject}-${s.session}`, s]));
    let metric = METRICS[0];
    let selected = sessions[0];

    // totals
    const totalTrials = sessions.reduce((a, s) => a + s.trials, 0);
    const tagged = sessions.reduce((a, s) => a + s.emg_tagged, 0);
    const inspected = sessions.reduce((a, s) => a + s.conditions.inner.trials + s.conditions.visualized.trials, 0);
    const totals = html("div", { class: "is-kv" });
    totals.innerHTML =
      `<div><b>${totalTrials.toLocaleString("en")}</b><span>trials in ${sessions.length} sessions</span></div>` +
      `<div><b>${tagged}</b><span>EMG-tagged (${((100 * tagged) / inspected).toFixed(1)} % of inner + visualized)</span></div>` +
      `<div><b>${sessions.filter((s) => s.trials < 200).length}</b><span>shorter third sessions</span></div>`;
    root.appendChild(totals);

    const controls = html("div", { class: "is-segmented", role: "group", "aria-label": "Value shown in the grid" });
    METRICS.forEach((m) => {
      const b = html("button", { type: "button", "aria-pressed": String(m === metric) }, m.label);
      b.addEventListener("click", () => {
        metric = m;
        controls.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
        paint();
      });
      controls.appendChild(b);
    });
    root.appendChild(controls);

    const wrap = html("div", { class: "is-sessions" });
    const left = html("div");
    const describe = html("p", { class: "is-figure__sub" });
    const grid = html("div", { class: "is-grid", role: "grid", "aria-label": "Sessions by subject" });
    left.appendChild(describe);
    left.appendChild(grid);
    const scale = html("div", { class: "is-scale" });
    left.appendChild(scale);
    const detail = html("div", { class: "is-detail", "aria-live": "polite" });
    wrap.appendChild(left);
    wrap.appendChild(detail);
    root.appendChild(wrap);

    grid.appendChild(html("div", { class: "head" }, ""));
    [1, 2, 3].forEach((b) => grid.appendChild(html("div", { class: "head" }, `ses-0${b}`)));
    const cells = [];
    for (let n = 1; n <= 10; n++) {
      grid.appendChild(html("div", { class: "row-head" }, `sub-${String(n).padStart(2, "0")}`));
      [1, 2, 3].forEach((b) => {
        const s = byKey.get(`${n}-${b}`);
        const cell = html("button", { type: "button", class: "is-cell", "aria-pressed": "false" });
        if (!s) {
          cell.disabled = true;
          cell.textContent = "";
        } else {
          cell.addEventListener("click", () => {
            select(s);
            // on narrow screens the details are below the grid
            if (window.matchMedia("(max-width: 52em)").matches) {
              detail.scrollIntoView({ behavior: "smooth", block: "nearest" });
            }
          });
          cells.push({ cell, s });
        }
        grid.appendChild(cell);
      });
    }

    function paint() {
      describe.textContent = metric.describe;
      const values = sessions.map(metric.value).filter((v) => v !== null);
      const max = Math.max(...values);
      cells.forEach(({ cell, s }) => {
        const v = metric.value(s);
        const lvl = level(v, max);
        cell.className = `is-cell lvl-${lvl}`;
        const note = SESSION_NOTES[`${s.subject}-${s.session}`];
        cell.innerHTML = esc(metric.fmt(s)) + (note ? '<span class="flag" aria-hidden="true">●</span>' : "");
        cell.setAttribute("aria-label", `sub-${String(s.subject).padStart(2, "0")} ses-0${s.session}: ${metric.label} ${metric.fmt(s)}${note ? ", has a note" : ""}`);
        cell.setAttribute("aria-pressed", String(s === selected));
      });
      scale.innerHTML =
        `<span>0</span>` +
        [0, 1, 2, 3, 4].map((l) => `<i class="lvl-${l}"></i>`).join("") +
        `<span>${metric.key === "time" ? minutes(max) : max}</span>` +
        `<span style="margin-left:auto">● note on the session</span>`;
    }

    function select(s) {
      selected = s;
      cells.forEach(({ cell, s: t }) => cell.setAttribute("aria-pressed", String(t === s)));
      const sub = `sub-${String(s.subject).padStart(2, "0")}`;
      const ses = `ses-0${s.session}`;
      const note = SESSION_NOTES[`${s.subject}-${s.session}`];
      let out = `<h4>${sub} · ${ses}</h4>`;
      out += `<div class="meta">${s.age} years, ${s.gender === "F" ? "female" : "male"} · recording ${minutes(s.recording_time)} min</div>`;
      out += `<div class="is-kv"><div><b>${s.trials}</b><span>trials</span></div>` +
        `<div><b>${s.emg_tagged}</b><span>EMG-tagged</span></div>` +
        `<div><b>${s.answers_right}/${s.answers_wrong}</b><span>answers right/wrong</span></div></div>`;
      detail.innerHTML = out;
      detail.appendChild(conditionBar(s));
      let rest = `<p style="margin:.4rem 0 0">Classes: ${Object.entries(s.classes).map(([k, v]) => `${k} ${v}`).join(" · ")}</p>`;
      if (s.corrections) {
        const ins = inserted(s);
        rest += `<p style="margin:.5rem 0 0"><b>Event corrections</b>: ${ins.length ? "" : "none besides ignoring the spurious trigger 65536."}</p>`;
        if (ins.length) {
          rest += "<ul>" + ins.map((c) => `<li>inserted <code>${c.code}</code> ${esc(CODE_NAMES[c.code] || "")} at sample ${c.sample.toLocaleString("en")}${c.code >= 31 && c.code <= 34 ? " (class inferred from the class balance)" : ""}</li>`).join("") + "</ul>";
        }
      } else {
        rest += '<p class="is-note">This summary was made from the files of version 2.1.2 for this session (events.dat, report.pkl), which do not list the event corrections.</p>';
      }
      if (note) rest += `<p class="is-note">${esc(note)}</p>`;
      detail.insertAdjacentHTML("beforeend", rest);
    }

    function conditionBar(s) {
      const W = 420;
      const H = 16;
      const node = svg("svg", { viewBox: `0 0 ${W} ${H}`, preserveAspectRatio: "none", style: `height:${H}px`, role: "img", "aria-label": CONDITIONS.map((c) => `${c.label} ${s.conditions[c.key].trials} trials`).join(", ") });
      let x0 = 0;
      const legend = html("div", { class: "is-legend" });
      CONDITIONS.forEach((c) => {
        const n = s.conditions[c.key].trials;
        const t = s.conditions[c.key].emg_tagged;
        const w = (n / s.trials) * W;
        if (n > 0) {
          const r = svg("rect", { x: x0 + 1, y: 0, width: Math.max(0, w - 2), height: H, rx: 3, fill: `var(--is-${c.css})`, class: "is-hit" }, node);
          r.addEventListener("mousemove", (e) => showTip(e, `<b>${c.label}</b><br>${n} trials${c.key === "pronounced" ? "" : `<br><span class="muted">${t} EMG-tagged</span>`}`));
          r.addEventListener("mouseleave", hideTip);
        }
        x0 += w;
        const tagged = c.key === "pronounced" ? "" : `&nbsp;<span style="color:var(--is-ink-3)">(${t} tagged)</span>`;
        legend.insertAdjacentHTML("beforeend", `<span><i class="is-swatch ${c.css}"></i>${c.short}&nbsp;<b>${n}</b>${tagged}</span>`);
      });
      const box = html("div");
      box.appendChild(node);
      box.appendChild(legend);
      return box;
    }

    paint();
    select(selected);
  }

  /* -------------------------- file explorer -------------------------- */

  const FILES = [
    {
      name: "ds003626/", dir: true, children: [
        { name: "dataset_description.json", tag: "BIDS", desc: "Name, authors, licence (CC0), DOI and how to cite the dataset.", anchor: "#top-level-files" },
        { name: "participants.tsv", tag: "BIDS", desc: "One row per participant: age, gender and handedness (all right-handed). <code>participants.json</code> describes the columns.", code: "pd.read_csv(root / \"participants.tsv\", sep=\"\\t\")", anchor: "#top-level-files" },
        { name: "task-innerspeech_eeg.json", tag: "BIDS", desc: "Recording settings that hold for every session: BioSemi ActiveTwo, 1024 Hz, 128 EEG + 4 EOG + 2 EMG + 2 reference channels, 50 Hz power line.", anchor: "#top-level-files" },
        { name: "task-innerspeech_events.json", tag: "BIDS", desc: "Meaning of every trigger code and of the columns of the raw <code>events.tsv</code> files.", anchor: "../events/" },
        {
          name: "sub-01/ses-01/eeg/", dir: true, children: [
            { name: "sub-01_ses-01_task-innerspeech_eeg.bdf", tag: "raw · ~700 MB", desc: "The continuous BioSemi recording of the whole session: 128 EEG channels (A1–D32), 8 external channels (EXG1–EXG8) and the Status channel with the trigger codes, at 1024 Hz. About 27 minutes per full session.", code: "raw = mne.io.read_raw_bdf(path, preload=True)\n# or: innerspeech.data_extractions.extract_subject_from_bdf(root, 1, 1)", anchor: "#raw-recordings" },
            { name: "sub-01_ses-01_task-innerspeech_events.tsv", tag: "BIDS", desc: "Every trigger as recorded, with <code>onset</code>, <code>sample</code>, <code>value</code> (code), <code>trial_type</code> (code name) and the run's <code>condition</code>. Not corrected: missing triggers are still missing here.", code: "pd.read_csv(path, sep=\"\\t\")", anchor: "#raw-recordings" },
            { name: "sub-01_ses-01_task-innerspeech_channels.tsv", tag: "BIDS", desc: "Type, units and placement of every channel, including what each EXG electrode records.", anchor: "#channels" },
            { name: "sub-01_ses-01_task-innerspeech_eeg.json", tag: "BIDS", desc: "Recording duration of this session (the shared settings are in the top-level file).", anchor: "#raw-recordings" },
          ],
        },
        { name: "sub-02/ … sub-10/", dir: true, muted: true, desc: "Ten participants × three sessions = 30 recordings." },
        {
          name: "derivatives/", dir: true, children: [
            { name: "dataset_description.json", tag: "BIDS", desc: "Describes the processing that made the derivatives.", anchor: "#derivatives" },
            { name: "events.json", tag: "BIDS", desc: "Meaning of the columns of the derivatives' <code>events.tsv</code> files.", anchor: "#trial-table-eventstsv" },
            {
              name: "sub-01/ses-01/", dir: true, children: [
                { name: "sub-01_ses-01_eeg-epo.fif", tag: "~236 MB", desc: "Preprocessed EEG trials: <b>[trials × 128 × 1153]</b>, 256 Hz, −0.5 to 4.0 s from the cue. Re-referenced to the ear lobes, 0.5–100 Hz band-pass, 50 Hz notch, ICA-cleaned.", code: "epochs = mne.read_epochs(path)\nX = epochs.get_data()   # (200, 128, 1153)", anchor: "#epoch-files" },
                { name: "sub-01_ses-01_exg-epo.fif", tag: "~15 MB", desc: "The 8 external channels (ear lobes, EOG, EMG) of the same trials: <b>[trials × 8 × 1153]</b>. Same processing without ICA, baseline-corrected with the 0.5 s before the cue.", anchor: "#epoch-files" },
                { name: "sub-01_ses-01_baseline-epo.fif", tag: "~4 MB", desc: "The 15 s baseline of the session: <b>[1 × 136 × 3841]</b> (128 EEG + 8 EXG channels).", anchor: "#epoch-files" },
                { name: "sub-01_ses-01_events.tsv", tag: "from 2.2.0", desc: "<b>One row per trial</b>, in the order of the epochs: <code>sample</code>, <code>onset</code>, <code>class</code>, <code>condition</code>, <code>session</code>, <code>cue_inferred</code> and the EMG control results.", code: "from innerspeech.derivatives_io import load_events_table\nload_events_table(root / \"derivatives\", 1, 1)", anchor: "#trial-table-eventstsv" },
                { name: "sub-01_ses-01_report.json", tag: "from 2.2.0", desc: "Session information: age, gender, recording time, answers to the control questions, EMG control results and the list of event corrections.", code: "from innerspeech.derivatives_io import load_report\nload_report(root / \"derivatives\", 1, 1)", anchor: "#session-report-reportjson" },
                { name: "sub-01_ses-01_events.dat", tag: "legacy", desc: "The first four columns of <code>events.tsv</code> as a NumPy array (format of versions up to 2.1.2).", code: "load_events(root / \"derivatives\", 1, 1)  # (n_trials, 4)", anchor: "#legacy-files" },
                { name: "sub-01_ses-01_report.pkl", tag: "legacy", desc: "The report as a pickled dict (format of versions up to 2.1.2).", anchor: "#legacy-files" },
              ],
            },
          ],
        },
      ],
    },
  ];

  function fileExplorer(root) {
    const wrap = html("div", { class: "is-explorer" });
    const tree = html("ul", { class: "is-tree", role: "tree" });
    const panel = html("div", { class: "is-file-panel", "aria-live": "polite" });
    const buttons = [];

    function show(item, button) {
      buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
      let out = `<h4>${esc(item.name)}</h4><p>${item.desc || ""}</p>`;
      if (item.code) out += `<pre><code>${esc(item.code)}</code></pre>`;
      if (item.anchor) out += `<p><a href="${item.anchor}">More about this file →</a></p>`;
      panel.innerHTML = out;
    }

    function build(items, parent) {
      items.forEach((item) => {
        const li = html("li", { role: "treeitem" });
        const shown = item.name.replace(/^sub-01_ses-01_/, "…_");
        const b = html("button", { type: "button", "aria-pressed": "false", class: item.dir ? "dir" : "", title: item.name }, esc(shown));
        if (item.tag) b.insertAdjacentHTML("beforeend", `<span class="tag">${esc(item.tag)}</span>`);
        if (item.desc) {
          b.addEventListener("click", () => show(item, b));
          buttons.push(b);
        } else {
          b.disabled = true;
        }
        li.appendChild(b);
        if (item.children) {
          const ul = html("ul", { role: "group" });
          build(item.children, ul);
          li.appendChild(ul);
        }
        parent.appendChild(li);
      });
    }
    build(FILES, tree);
    wrap.appendChild(html("div", { class: "is-tree-wrap" })).appendChild(tree);
    wrap.appendChild(panel);
    root.appendChild(wrap);
    const firstButton = buttons.find((b) => b.title.endsWith("_eeg-epo.fif"));
    if (firstButton) firstButton.click();
  }

  /* ----------------------------- boot ----------------------------- */

  const VIZ = {
    "trial-timeline": trialTimeline,
    "session-structure": sessionStructure,
    sessions: sessionsOverview,
    "file-explorer": fileExplorer,
  };

  function init() {
    document.querySelectorAll("[data-viz]").forEach((root) => {
      if (root.dataset.drawn) return;
      const draw = VIZ[root.dataset.viz];
      if (!draw) return;
      root.dataset.drawn = "1";
      root.innerHTML = "";
      draw(root);
    });
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(init);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
