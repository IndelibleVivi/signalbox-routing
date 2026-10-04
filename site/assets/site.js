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
