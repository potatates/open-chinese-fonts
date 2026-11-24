// Small helpers for PostHog events (PostHog itself loads from
// src/components/posthog.astro). If PostHog is missing or blocked, these do nothing.

export function track(event: string, properties?: Record<string, unknown>) {
  window.posthog?.capture(event, properties);
}

// Send an event only the first time it happens on this page
const sentOnce = new Set<string>();
export function trackOnce(event: string, properties?: Record<string, unknown>, key = event) {
  if (sentOnce.has(key)) return;
  sentOnce.add(key);
  track(event, properties);
}

// "Someone typed their own preview text" — only that they did, never the text.
// Once per page for each box. Call it from an input listener; text the page
// fills in itself (shuffle, clear) doesn't count.
export function trackPreviewTyped(e: Event, where: string) {
  if (e.isTrusted) trackOnce("preview_text_typed", { where }, `preview:${where}`);
}

// Search: send what was searched once typing has paused, so "思", "思源", "思源黑"
// don't each become an event. results() is read when the event is sent.
export function searchTracker(where: string, results: () => number) {
  let timer: ReturnType<typeof setTimeout>;
  let last = "";
  return (query: string) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      const q = query.trim().slice(0, 50);
      if (!q || q === last) return;
      last = q;
      const n = results();
      track("font_searched", { where, query: q, results: n, no_results: n === 0 });
    }, 1200);
  };
}
