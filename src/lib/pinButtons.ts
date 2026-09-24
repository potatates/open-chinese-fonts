// Keeps every pin button on the page in sync with the pinned list.
import { fonts, displayWeight } from "./fonts";
import { getPins, isFull, isPinned, MAX_PINS, onPinsChange, togglePin } from "./pins";

function sync() {
  for (const btn of document.querySelectorAll<HTMLButtonElement>("[data-pin]")) {
    const pinned = isPinned(btn.dataset.pin!);
    const full = !pinned && isFull();
    btn.setAttribute("aria-pressed", String(pinned));
    btn.disabled = full;
    btn.title = full ? `最多钉选 ${MAX_PINS} 款，请先取消一款` : "";
    btn.querySelector("[data-pin-label]")!.textContent = pinned ? "已钉选" : full ? "已满" : "钉选";
  }
  // The header's "对比" link shows how many fonts are pinned
  const count = getPins().length;
  document.querySelectorAll<HTMLElement>("[data-pin-count]").forEach((el) => {
    el.textContent = count ? String(count) : "";
    el.hidden = !count;
  });
}

export function initPinButtons() {
  document.addEventListener("click", (e) => {
    const btn = (e.target as Element).closest<HTMLButtonElement>("[data-pin]");
    if (!btn) return;
    const id = btn.dataset.pin!;
    const font = fonts.find((f) => f.id === id)!;
    // Pin the weight currently on screen (a card's pressed tag, the detail preview…)
    const holder = btn.closest<HTMLElement>("[data-current-weight]");
    const weight = Number(holder?.dataset.currentWeight) || displayWeight(font.weights);
    togglePin(id, weight);
  });
  onPinsChange(sync);
  sync();
}
