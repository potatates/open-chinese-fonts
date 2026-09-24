// Pinned fonts: a small list (max 4) saved in the browser's localStorage,
// so it survives page changes and return visits — like a shopping cart.
// Every part of the site that shows pins listens for changes through
// onPinsChange(), so the tray, pin buttons and compare page stay in sync.
import { fonts } from "./fonts";

export interface Pin {
  id: string;
  weight: number;
}

export const MAX_PINS = 4;
const KEY = "pinned-fonts";
const EVENT = "pins-change";
const known = new Set(fonts.map((f) => f.id));

function read(): Pin[] {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) ?? "[]");
    if (!Array.isArray(raw)) return [];
    // Drop anything that's no longer in the catalog or looks broken
    return raw
      .filter((p) => p && known.has(p.id) && typeof p.weight === "number")
      .slice(0, MAX_PINS);
  } catch {
    return []; // storage can be blocked (private mode etc.) — pins just won't persist
  }
}

let pins: Pin[] = read();

export function getPins(): Pin[] {
  return pins.map((p) => ({ ...p }));
}

export function setPins(next: Pin[]) {
  const seen = new Set<string>();
  pins = next.filter((p) => known.has(p.id) && !seen.has(p.id) && seen.add(p.id)).slice(0, MAX_PINS);
  try {
    localStorage.setItem(KEY, JSON.stringify(pins));
  } catch {
    /* not saved, but still works for this page */
  }
  window.dispatchEvent(new CustomEvent(EVENT));
}

export const isPinned = (id: string) => pins.some((p) => p.id === id);
export const isFull = () => pins.length >= MAX_PINS;

/** Pin or unpin. Returns false if pinning was refused because the list is full. */
export function togglePin(id: string, weight: number): boolean {
  if (isPinned(id)) {
    setPins(pins.filter((p) => p.id !== id));
    return true;
  }
  if (isFull()) return false;
  setPins([...pins, { id, weight }]);
  return true;
}

export function unpin(id: string) {
  setPins(pins.filter((p) => p.id !== id));
}

export function setPinWeight(id: string, weight: number) {
  setPins(pins.map((p) => (p.id === id ? { ...p, weight } : p)));
}

export function onPinsChange(callback: () => void) {
  window.addEventListener(EVENT, callback);
  // Another tab changed the pins: reload them and notify
  window.addEventListener("storage", (e) => {
    if (e.key !== KEY) return;
    pins = read();
    callback();
  });
}
