/* Signalbox reading station interactions.
   Native controls, keyboard use, Escape and focus return, no autoplay, no
   network requests beyond the static pages and the optional Mermaid CDN. */
(() => {
  "use strict";
  const root = document.getElementById("sbx-station");
  if (!root) return;

  const esc = (value) => String(value).replace(/[&<>"']/g, (ch) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]
  ));

  /* ---- Reading-margin TOC: open sidebar on desktop, collapsible on narrow.
     A native <details> gives keyboard/touch behavior for free; we only choose
     the default open state per viewport and keep it in sync while resizing. */
  const tocDetails = [...root.querySelectorAll("details.sx-toc")];
  if (tocDetails.length) {
    const wide = window.matchMedia("(min-width: 561px)");
    const syncToc = () => tocDetails.forEach((d) => {
      if (wide.matches) d.setAttribute("open", "");
      else d.removeAttribute("open");
    });
    syncToc();
    wide.addEventListener("change", syncToc);
  }

  /* ---- Build-time workbench receipt ---- */
  const scenarioData = root.querySelector("[data-scenario-data]");
  let scenarios = [];
  try {
    scenarios = JSON.parse(scenarioData ? scenarioData.textContent : "[]");
  } catch (_e) {
    scenarios = [];
  }
  const receipt = root.querySelector("[data-receipt]");
  const scenarioButtons = [...root.querySelectorAll("[data-scenario-button]")];

  const renderScenario = (index) => {
    const item = scenarios[index];
    if (!item || !receipt) return;
    scenarioButtons.forEach((button, i) => button.setAttribute("aria-pressed", String(i === index)));
    const verdict = item.passed ? "expected judgment matched" : "expected judgment did not match";
    const expected = JSON.stringify(item.expected, null, 2);
    const actual = JSON.stringify(item.actual, null, 2);
    receipt.innerHTML =
      "<h4>" + esc(item.label) + ' <span class="sx-mono sx-small">' + esc(item.id) + "</span></h4>" +
      '<p class="sx-small sx-muted">' + esc(item.blurb) + "</p>" +
      '<p><span class="sx-match" data-verdict="' + (item.passed ? "match" : "mismatch") + '">' +
        esc(verdict) + "</span></p>" +
      '<p class="sx-label">EXPECTED</p><pre>' + esc(expected) + "</pre>" +
      '<p class="sx-label">ACTUAL · scripts.replay.replay_case</p><pre>' + esc(actual) + "</pre>";
  };
  scenarioButtons.forEach((button, i) => button.addEventListener("click", () => renderScenario(i)));
  if (scenarioButtons.length) renderScenario(0);

  /* ---- Postcard teaching journeys: authored selection and steps only.
     The question this interaction asks is "which prewritten letter did the
     reader choose?", not "is a real path reachable?" No probes or fetches. */
  const postcardData = root.querySelector("[data-postcard-data]");
  const postcardSection = root.querySelector("#sx-postcards");
  let postcards = null;
  try {
    postcards = JSON.parse(postcardData ? postcardData.textContent : "null");
  } catch (_e) {
    postcards = null;
  }
  if (postcards && postcardSection) {
    const targets = new Map(postcards.targets.map((item) => [item.id, item]));
    const conditions = new Map(postcards.conditions.map((item) => [item.id, item]));
    const journeys = new Map(postcards.journeys.map((item) => [item.id, item]));
    const enhanced = postcardSection.querySelector("[data-postcard-enhanced]");
    const nextButton = postcardSection.querySelector("[data-postcard-next]");
    const resetButton = postcardSection.querySelector("[data-postcard-reset]");
    const articleLink = postcardSection.querySelector("[data-postcard-article]");
    const stage = postcardSection.querySelector("[data-postcard-stage]");
    const route = postcardSection.querySelector("[data-postcard-route]");
    const result = postcardSection.querySelector("[data-postcard-result]");
    const targetLabel = postcardSection.querySelector("[data-postcard-target-label]");
    const conditionLabel = postcardSection.querySelector("[data-postcard-condition-label]");
    const availability = postcardSection.querySelector("[data-postcard-availability]");
    const targetButtons = [...postcardSection.querySelectorAll("[data-postcard-target]")];
    const conditionButtons = [...postcardSection.querySelectorAll("[data-postcard-condition]")];
    const progress = postcardSection.querySelector("[data-postcard-progress]");
    const seal = postcardSection.querySelector("[data-postcard-seal]");
    let targetId = "tailnet-host";
    let conditionId = "normal";
    // -1 is the sealed, unsent letter. Every click visits one authored stop.
    let stepIndex = -1;

    const selectedJourney = () => journeys.get(targetId + "-" + conditionId);
    const renderStep = () => {
      const journey = selectedJourney();
      if (!journey) return;
      const steps = journey.steps;
      const ready = stepIndex < 0;
      const complete = stepIndex === steps.length - 1;
      const stopped = complete && journey.outcome === "stopped";
      stage.dataset.outcome = ready ? "ready" : complete ? journey.outcome : "transit";
      targetLabel.textContent = targets.get(journey.target_ref).label;
      conditionLabel.textContent = conditions.get(journey.condition_ref).label;
      seal.textContent = ready ? "待寄" : stopped ? "受阻" : complete ? "已送达" : "在途";
      progress.textContent = "邮路进度 · " + (stepIndex + 1) + " / " + steps.length;
      route.innerHTML = steps.map((step, index) => {
        const state = index === stepIndex && stopped ? "stop"
          : index < stepIndex ? "done"
          : index === stepIndex ? "current" : "waiting";
        return '<div class="sx-postcard-stop" role="listitem" data-state="' + state + '"'
          + (index === stepIndex ? ' aria-current="step"' : '') + '>'
          + '<span class="sx-postcard-stamp" aria-hidden="true">' + esc(step.stamp) + "</span>"
          + "<b>" + esc(step.label) + "</b></div>";
      }).join("");
      const current = steps[stepIndex];
      result.innerHTML = '<span class="sx-postcard-kicker">'
        + esc(ready ? "READY TO POST" : stopped ? "LETTER STOPPED" : complete ? "LETTER DELIVERED" : "IN TRANSIT")
        + "</span><h4>" + esc(current ? current.label : journey.title) + "</h4>"
        + "<p>" + esc(current ? current.detail : journey.summary) + "</p>"
        + (complete
          ? "<p class=\"sx-postcard-caveat\"><strong>" + esc(journey.result)
            + "</strong> " + esc(journey.caveat) + "</p>"
          : "");
      nextButton.textContent = ready ? "封好了，寄出 →"
        : complete ? (stopped ? "信暂存这里 · 再寄一次 ↻" : "信已送达 · 再寄一次 ↻")
        : "继续下一站 →";
      const article = journey.article;
      articleLink.href = article.source.slice(0, -3) + ".html#" + article.anchor;
      articleLink.textContent = article.label + " ↗";
    };
    const syncConditions = () => {
      conditionButtons.forEach((button) => {
        const condition = conditions.get(button.dataset.postcardCondition);
        const applies = condition.targets.includes(targetId);
        button.disabled = !applies;
        button.setAttribute("aria-disabled", String(!applies));
        button.setAttribute("aria-pressed", String(
          applies && button.dataset.postcardCondition === conditionId
        ));
      });
      availability.textContent = "旧 NAS 用 source-preserving gateway；LAN 回程缺失只对这个模式出现。";
    };
    const select = (nextTarget, nextCondition) => {
      targetId = nextTarget;
      conditionId = nextCondition;
      stepIndex = -1;
      targetButtons.forEach((button) => button.setAttribute(
        "aria-pressed", String(button.dataset.postcardTarget === targetId)
      ));
      syncConditions();
      const journey = selectedJourney();
      if (!journey) {
        availability.textContent = "这组不在教学信的范围里，请换一个能适用的条件。";
        return;
      }
      renderStep();
    };
    targetButtons.forEach((button) => button.addEventListener("click", () => {
      let nextCondition = conditionId;
      if (!conditions.get(nextCondition).targets.includes(button.dataset.postcardTarget)) {
        nextCondition = "normal";
      }
      select(button.dataset.postcardTarget, nextCondition);
    }));
    conditionButtons.forEach((button) => button.addEventListener("click", () => {
      const nextCondition = button.dataset.postcardCondition;
      if (!conditions.get(nextCondition).targets.includes(targetId)) return;
      select(targetId, nextCondition);
    }));
    nextButton.addEventListener("click", () => {
      const journey = selectedJourney();
      if (!journey) return;
      stepIndex = stepIndex === journey.steps.length - 1 ? 0 : stepIndex + 1;
      renderStep();
    });
    resetButton.addEventListener("click", () => {
      select(targetId, conditionId);
      nextButton.focus();
    });
    enhanced.dataset.ready = "true";
    postcardSection.dataset.ready = "true";
    select(targetId, conditionId);
  }

  /* ---- Dispatch dialog: cipher, key wrap, solved note ---- */
  const dialog = root.querySelector("dialog.sx-dispatch");
  const cipher = "VWLOO JURZLQJ";
  const plainTarget = "STILL GROWING";
  let key = 0;
  let opener = null;

  const renderCipher = () => {
    if (!dialog) return;
    const plain = cipher.replace(/[A-Z]/g, (letter) =>
      String.fromCharCode(65 + ((letter.charCodeAt(0) - 65 - key + 26) % 26))
    );
    dialog.querySelector("[data-key-value]").textContent = String(key).padStart(2, "0");
    dialog.querySelector("[data-decoded]").textContent = plain;
    const solved = plain === plainTarget;
    dialog.querySelector("[data-secret-note]").hidden = !solved;
    dialog.dataset.solved = String(solved);
  };

  const openDialog = (trigger) => {
    if (!dialog) return;
    opener = trigger || document.activeElement;
    if (typeof dialog.showModal === "function") dialog.showModal();
    else dialog.setAttribute("open", "");
    dialog.querySelector("[data-key-up]").focus({ preventScroll: true });
  };
  const closeDialog = () => {
    if (!dialog) return;
    if (typeof dialog.close === "function") dialog.close();
    else dialog.removeAttribute("open");
    if (opener && typeof opener.focus === "function") opener.focus({ preventScroll: true });
  };

  root.querySelectorAll("[data-open-dispatch]").forEach((button) =>
    button.addEventListener("click", () => openDialog(button))
  );
  const closeButton = root.querySelector("[data-close-dispatch]");
  if (closeButton) closeButton.addEventListener("click", closeDialog);
  if (dialog) {
    dialog.addEventListener("cancel", (event) => { event.preventDefault(); closeDialog(); });
    dialog.querySelector("[data-key-up]").addEventListener("click", () => { key = (key + 1) % 26; renderCipher(); });
    dialog.querySelector("[data-key-down]").addEventListener("click", () => { key = (key + 25) % 26; renderCipher(); });
    renderCipher();
  }
  root.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && dialog && dialog.hasAttribute("open")) closeDialog();
  });

  /* ---- Cat quote cycle with source link ---- */
  const catNotes = [
    "这卷纸带，先借我玩一下。",
    "这一封，留给愿意多看一眼的人。",
    "And all its circuits close in thee.",
  ];
  const catButton = root.querySelector("[data-cat-button]");
  const catNote = root.querySelector("[data-cat-note]");
  const catSource = root.querySelector("[data-cat-source]");
  let catVisit = 0;
  if (catButton) {
    catButton.addEventListener("click", () => {
      const index = catVisit % catNotes.length;
      if (catNote) catNote.textContent = catNotes[index];
      if (catSource) catSource.hidden = index !== 2;
      catVisit += 1;
    });
  }

  /* ---- Morse callsign toggle ---- */
  const morse = "... .. --. -. .- .-.. -... --- -..-";
  const callsign = root.querySelector("[data-callsign]");
  const callsignButton = root.querySelector("[data-callsign-button]");
  let callsignDecoded = false;
  if (callsignButton && callsign) {
    callsignButton.addEventListener("click", () => {
      callsignDecoded = !callsignDecoded;
      callsign.textContent = callsignDecoded ? "S I G N A L B O X" : morse;
      callsignButton.textContent = callsignDecoded ? "折回电码" : "译出呼号";
      callsignButton.setAttribute("aria-pressed", String(callsignDecoded));
    });
  }

  /* ---- Copyable code blocks, added only after JavaScript runs ---- */
  const copyTimers = new WeakMap();
  root.querySelectorAll(".sx-content pre").forEach((pre) => {
    const code = pre.querySelector("code");
    if (!code || code.classList.contains("sbx-mermaid-source")) return;
    let pending = false;

    const languageClass = [...code.classList].find((name) => name.startsWith("language-"));
    const language = (languageClass ? languageClass.slice("language-".length) : "code").toUpperCase();
    const figure = document.createElement("figure");
    figure.className = "sx-code-block";
    const bar = document.createElement("figcaption");
    bar.className = "sx-code-bar";
    const languageLabel = document.createElement("span");
    languageLabel.className = "sx-code-language";
    languageLabel.textContent = language;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "sx-copy-button";
    button.textContent = "复制";
    button.setAttribute("aria-label", "复制代码");
    const feedback = document.createElement("span");
    feedback.className = "sx-copy-feedback";
    feedback.setAttribute("role", "status");
    feedback.setAttribute("aria-live", "polite");
    feedback.setAttribute("aria-atomic", "true");
    const hint = document.createElement("p");
    hint.className = "sx-copy-hint";
    hint.hidden = true;
    hint.textContent = "复制未完成。代码已选中，请按 ⌘C（Mac）或 Ctrl+C 手动复制。";

    const setState = (state, buttonText, announcement) => {
      button.dataset.state = state;
      button.setAttribute("aria-busy", String(state === "pending"));
      button.setAttribute("aria-disabled", String(state === "pending"));
      button.textContent = buttonText;
      feedback.textContent = announcement;
    };

    const selectCode = () => {
      const selection = window.getSelection ? window.getSelection() : null;
      if (!selection || !document.createRange) return;
      const range = document.createRange();
      range.selectNodeContents(code);
      selection.removeAllRanges();
      selection.addRange(range);
    };

    button.addEventListener("click", async () => {
      if (pending) return;
      pending = true;
      const priorTimer = copyTimers.get(button);
      if (priorTimer) clearTimeout(priorTimer);
      hint.hidden = true;
      setState("pending", "复制中…", "正在复制代码。");
      try {
        if (!navigator.clipboard || typeof navigator.clipboard.writeText !== "function") {
          throw new Error("clipboard unavailable");
        }
        await navigator.clipboard.writeText(code.textContent);
        setState("success", "已复制", "代码已复制到剪贴板。");
        copyTimers.set(button, setTimeout(() => {
          setState("idle", "复制", "");
        }, 2400));
      } catch (_error) {
        selectCode();
        hint.hidden = false;
        setState("failure", "重试复制", "复制失败，代码已选中，请手动复制。");
      } finally {
        pending = false;
      }
    });

    bar.append(languageLabel, feedback, button);
    pre.replaceWith(figure);
    figure.append(bar, pre, hint);
  });

  /* ---- Progressive Mermaid rendering from a pinned public CDN ---- */
  const mermaidBlocks = [...root.querySelectorAll("code.sbx-mermaid-source")];
  if (mermaidBlocks.length && "noModule" in HTMLScriptElement.prototype) {
    import("https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs")
      .then(({ default: mermaid }) => {
        mermaid.initialize({ startOnLoad: false, securityLevel: "strict", theme: "neutral" });
        mermaidBlocks.forEach((block, i) => {
          const source = block.textContent;
          const pre = block.closest("pre");
          if (!pre) return;
          // Move the raw source under an accessible native disclosure and
          // place the rendered graph first.
          const details = document.createElement("details");
          details.className = "sx-mermaid-source";
          const summary = document.createElement("summary");
          summary.textContent = "查看 Mermaid 源码";
          details.appendChild(summary);
          const holder = document.createElement("div");
          holder.className = "sx-mermaid-rendered";
          holder.tabIndex = 0;
          holder.setAttribute("role", "region");
          holder.setAttribute("aria-label", "图解，宽图可横向滚动");
          mermaid.render("sbx-mermaid-" + i, source).then(({ svg }) => {
            holder.innerHTML = svg;
            const diagram = holder.querySelector("svg");
            diagram.style.minWidth = diagram.viewBox.baseVal.width + "px";
            pre.replaceWith(details);
            details.appendChild(pre);
            details.insertAdjacentElement("beforebegin", holder);
            const hint = document.createElement("p");
            hint.className = "sx-small sx-muted";
            hint.textContent = "宽图可横向滚动；下方可展开源码。";
            holder.insertAdjacentElement("afterend", hint);
          }).catch(() => { /* keep the readable code fallback */ });
        });
      })
      .catch(() => { /* offline: readable source stays visible */ });
  }
})();
