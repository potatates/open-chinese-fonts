// Draws the pinned-fonts tray (list + pairing preview) into every element
// with [data-pin-tray], and runs the slim bar used on phones/detail pages.
import { fonts, WEIGHT_NAMES } from "./fonts";
import { getPins, MAX_PINS, onPinsChange, setPins, unpin } from "./pins";
import { loadFont } from "./fontLoader";

const byId = new Map(fonts.map((f) => [f.id, f]));

// A classic title + body pair (public domain), so the pairing preview reads
// like a real page: 刘禹锡《陋室铭》
const PAIR_TITLE = "陋室铭";
const PAIR_BODY =
  "山不在高，有仙则名。水不在深，有龙则灵。斯是陋室，惟吾德馨。苔痕上阶绿，草色入帘青。谈笑有鸿儒，往来无白丁。";

let previewText = "";

// Your own edits to the pairing text (null = use the default)
const PAIR_TEXT_KEY = "pin-pair-text";
let pairText: { title: string | null; body: string | null } = (() => {
  try {
    return JSON.parse(localStorage.getItem(PAIR_TEXT_KEY) ?? "") ?? { title: null, body: null };
  } catch {
    return { title: null, body: null };
  }
})();
function savePairText() {
  try {
    localStorage.setItem(PAIR_TEXT_KEY, JSON.stringify(pairText));
  } catch {
    /* ignore */
  }
}
const PAIR_KEY = "pin-pair";
let pair: { head: string; body: string } = (() => {
  try {
    return JSON.parse(localStorage.getItem(PAIR_KEY) ?? "") ?? { head: "", body: "" };
  } catch {
    return { head: "", body: "" };
  }
})();

/** Pages call this so the tray shows the text you're previewing. */
export function setTrayText(text: string) {
  previewText = text.trim();
  renderAll();
}

// ---- Fonts: remember loaded families so re-drawing the tray doesn't flicker
const ready = new Map<string, string>();

// subset=true requests only these exact characters (tiny, for fixed text);
// subset=false loads the whole sliced font, for text you can edit.
function applyFont(node: HTMLElement, id: string, weight: number, text: string, subset = true) {
  const key = subset ? `${id}|${weight}|${text}` : `${id}|${weight}|full`;
  node.style.fontWeight = String(weight);
  const known = ready.get(key);
  if (known) {
    node.style.fontFamily = `"${known}", var(--font-ui)`;
    node.dataset.state = "ready";
    return;
  }
  node.dataset.state = "idle";
  node.dataset.key = key;
  loadFont(byId.get(id)!, weight, text, { subset })
    .then((family) => {
      ready.set(key, family);
      if (node.dataset.key !== key) return;
      node.style.fontFamily = `"${family}", var(--font-ui)`;
      node.dataset.state = "ready";
    })
    .catch(() => (node.dataset.state = "error"));
}

// Tiny helper for building elements: el("p", { class: "x" }, "text", child…)
function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attrs: Record<string, string> = {},
  ...children: (Node | string)[]
): HTMLElementTagNameMap[K] {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  node.append(...children);
  return node;
}

// After a pin is removed, fill the empty role with a font that isn't
// already playing the other role (so title and body don't become the same).
function validPair(ids: string[]) {
  const other = (taken: string) => ids.find((id) => id !== taken) ?? ids[0];
  if (!ids.includes(pair.head)) pair.head = other(pair.body);
  if (!ids.includes(pair.body)) pair.body = other(pair.head);
}

function savePair() {
  try {
    localStorage.setItem(PAIR_KEY, JSON.stringify(pair));
  } catch {
    /* ignore */
  }
}

const resetButton = () =>
  el("button", { type: "button", class: "tray-link", "data-pair-reset": "" }, "恢复默认文字");

function fontSelect(role: "head" | "body", label: string, ids: string[]) {
  const select = el("select", { "data-pair-role": role });
  for (const id of ids) {
    const opt = el("option", { value: id }, byId.get(id)!.name.zh);
    if (pair[role] === id) opt.selected = true;
    select.append(opt);
  }
  return el("label", { class: "pair-role caption" }, label, select);
}

function renderTray(container: HTMLElement) {
  const pins = getPins();
  const parts: Node[] = [];

  const head = el("div", { class: "tray-head" }, el("h2", { class: "tray-title", tabindex: "-1" },"已钉选 ", el("span", { class: "caption" }, `${pins.length}/${MAX_PINS}`)));
  if (pins.length) head.append(el("button", { type: "button", class: "tray-link", "data-tray-clear": "" }, "清空"));
  parts.push(head);

  if (!pins.length) {
    parts.push(el("p", { class: "caption tray-empty" }, "点按字体上的「钉选」，它会一直显示在这里，方便边浏览边比较、看搭配。"));
  } else {
    const list = el("ol", { class: "pin-list" });
    for (const pin of pins) {
      const font = byId.get(pin.id)!;
      const text = previewText || font.name.zh;
      const specimen = el("p", { class: "pin-specimen", lang: "zh-Hans", "aria-hidden": "true" }, text);
      applyFont(specimen, pin.id, pin.weight, text);
      list.append(
        el(
          "li",
          { class: "pin-item" },
          specimen,
          el(
            "div",
            { class: "pin-meta" },
            el("a", { href: `/fonts/${pin.id}/` }, font.name.zh),
            el("span", { class: "caption" }, WEIGHT_NAMES[pin.weight] ?? String(pin.weight)),
            el("button", { type: "button", class: "pin-remove", "data-unpin": pin.id, "aria-label": `取消钉选 ${font.name.zh}` }, "×"),
          ),
        ),
      );
    }
    parts.push(list);
  }

  if (pins.length >= 2) {
    const ids = pins.map((p) => p.id);
    validPair(ids);
    const weightOf = (id: string) => pins.find((p) => p.id === id)!.weight;
    const title = pairText.title ?? (previewText || PAIR_TITLE);
    const body = pairText.body ?? PAIR_BODY;
    // contenteditable="plaintext-only" lets you type straight into the sample
    const editable = (role: string, label: string) => ({
      contenteditable: "plaintext-only",
      role: "textbox",
      "aria-label": label,
      spellcheck: "false",
      lang: "zh-Hans",
      "data-pair-edit": role,
    });
    const h = el("p", { class: "pair-head", ...editable("title", "搭配标题，可编辑") }, title);
    const b = el("p", { class: "pair-body", ...editable("body", "搭配正文，可编辑"), "aria-multiline": "true" }, body);
    // Until you edit the text, load only the characters shown (a few KB);
    // once edited, load the full font so anything you type can be drawn.
    applyFont(h, pair.head, weightOf(pair.head), title, pairText.title === null);
    applyFont(b, pair.body, weightOf(pair.body), body, pairText.body === null);
    const customized = pairText.title !== null || pairText.body !== null;
    parts.push(
      el(
        "section",
        { class: "pair", "aria-label": "搭配预览" },
        el(
          "div",
          { class: "pair-top" },
          el("h3", { class: "tray-subtitle" }, "搭配预览"),
          ...(customized ? [resetButton()] : []),
        ),
        el(
          "div",
          { class: "pair-roles" },
          fontSelect("head", "标题", ids),
          fontSelect("body", "正文", ids),
          el("button", { type: "button", class: "tray-link", "data-pair-swap": "" }, "⇄ 交换"),
        ),
        el("div", { class: "pair-sample" }, h, b),
      ),
    );
  }

  if (pins.length >= 2) {
    const qs = previewText ? `?t=${encodeURIComponent(previewText)}` : "";
    parts.push(el("a", { class: "tray-compare", href: `/compare/${qs}` }, "并排对比 →"));
  } else if (pins.length === 1) {
    parts.push(el("p", { class: "caption" }, "再钉选 1 款即可看搭配、并排对比。"));
  }

  container.replaceChildren(...parts);
}

// ---- The slim bar (phones, and pages without a tray column)
function renderBar() {
  const bar = document.querySelector<HTMLElement>("[data-pin-bar]");
  if (!bar) return;
  const pins = getPins();
  bar.hidden = pins.length === 0;
  document.body.classList.toggle("has-pin-bar", pins.length > 0);
  bar.querySelector("[data-bar-count]")!.textContent = String(pins.length);
  bar.querySelector("[data-bar-names]")!.textContent = pins.map((p) => byId.get(p.id)!.name.zh).join(" · ");
  const compare = bar.querySelector<HTMLAnchorElement>("[data-bar-compare]")!;
  compare.hidden = pins.length < 2;
  compare.href = `/compare/${previewText ? `?t=${encodeURIComponent(previewText)}` : ""}`;
  if (!pins.length) setBarOpen(false);
}

function setBarOpen(open: boolean) {
  const toggle = document.querySelector<HTMLButtonElement>("[data-bar-toggle]");
  const panel = document.querySelector<HTMLElement>("#pin-bar-panel");
  if (!toggle || !panel) return;
  toggle.setAttribute("aria-expanded", String(open));
  panel.hidden = !open;
}

function renderAll() {
  // Re-drawing replaces the tray's elements, so remember where keyboard focus
  // was and put it back afterwards (otherwise it would jump to the page top).
  const active = document.activeElement as HTMLElement | null;
  const tray = active?.closest<HTMLElement>("[data-pin-tray]");
  let refocus: string | null = null;
  if (tray && active) {
    if (active.dataset.pairRole) refocus = `[data-pair-role="${active.dataset.pairRole}"]`;
    else if (active.dataset.pairEdit) refocus = `[data-pair-edit="${active.dataset.pairEdit}"]`;
    else if (active.hasAttribute("data-pair-swap")) refocus = "[data-pair-swap]";
    else refocus = ".tray-title"; // e.g. the × you pressed no longer exists
  }

  document.querySelectorAll<HTMLElement>("[data-pin-tray]").forEach(renderTray);
  renderBar();

  if (tray && refocus) tray.querySelector<HTMLElement>(refocus)?.focus();
}

export function initPinTray() {
  document.addEventListener("click", (e) => {
    const t = e.target as Element;
    const remove = t.closest<HTMLElement>("[data-unpin]");
    if (remove) return unpin(remove.dataset.unpin!);
    if (t.closest("[data-tray-clear]")) return setPins([]);
    if (t.closest("[data-pair-reset]")) {
      pairText = { title: null, body: null };
      savePairText();
      return renderAll();
    }
    if (t.closest("[data-pair-swap]")) {
      pair = { head: pair.body, body: pair.head };
      savePair();
      return renderAll();
    }
    const toggle = t.closest<HTMLButtonElement>("[data-bar-toggle]");
    if (toggle) setBarOpen(toggle.getAttribute("aria-expanded") !== "true");
  });
  // Typing in the pairing sample: remember it (without re-drawing, so the
  // cursor stays where it is). The browser fetches any new characters itself.
  document.addEventListener("input", (e) => {
    const field = (e.target as Element).closest<HTMLElement>("[data-pair-edit]");
    if (!field) return;
    const role = field.dataset.pairEdit as "title" | "body";
    const firstEdit = pairText[role] === null;
    pairText[role] = field.textContent ?? "";
    savePairText();
    if (firstEdit) {
      // Switch this sample from the few-characters subset to the full font
      const pins = getPins();
      const id = role === "title" ? pair.head : pair.body;
      const weight = pins.find((p) => p.id === id)?.weight ?? 400;
      applyFont(field, id, weight, pairText[role]!, false);
      field.dataset.state = "ready"; // keep what you're typing visible while it loads
    }
    // Offer "恢复默认文字" right away, without re-drawing the tray
    const top = field.closest(".pair")?.querySelector(".pair-top");
    if (top && !top.querySelector("[data-pair-reset]")) top.append(resetButton());
  });
  document.addEventListener("keydown", (e) => {
    const field = (e.target as Element).closest?.("[data-pair-edit='title']");
    if (field && e.key === "Enter") e.preventDefault(); // a title is one line
  });
  document.addEventListener("change", (e) => {
    const select = (e.target as Element).closest<HTMLSelectElement>("[data-pair-role]");
    if (!select) return;
    pair[select.dataset.pairRole as "head" | "body"] = select.value;
    savePair();
    renderAll();
  });
  // Escape closes the bar's panel
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") setBarOpen(false);
  });
  onPinsChange(renderAll);
  renderAll();
}
