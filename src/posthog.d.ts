// PostHog is loaded by src/components/posthog.astro (not bundled), so tell
// TypeScript that window.posthog may exist. It's missing when the token isn't
// set (npm run dev), which is why every call uses window.posthog?.capture(...).
interface Window {
  posthog?: { capture: (event: string, properties?: Record<string, unknown>) => void };
}
