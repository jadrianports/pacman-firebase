// PAC-MAN web leaderboard — behavioral core.
//
// A no-dependency ES module that consumes the live get_leaderboard Cloud Function
// and renders the This Week / All Time boards into the Plan 01 DOM contract
// (index.html). Mirrors menu.py:run_leaderboard logic and api_service.get_leaderboard
// fetch semantics, translated to browser fetch + DOM.
//
// Loaded in the browser via <script type="module" src="app.js">; imported by
// node:test (web/package.json type:module) to exercise the pure functions.

// Source-of-truth URL — a hardcoded mirror of settings.API_LEADERBOARD_URL (D-03).
// Intentionally public/non-secret: the read endpoint requires no key or signature
// (threat T-07-02 accepted).
export const LEADERBOARD_URL =
  "https://get-leaderboard-991339031546.asia-southeast1.run.app";

// Unique cache sentinel — "this scope has never been fetched". Distinct from the
// fetched values null (offline), [] (empty), and [...] (data).
export const UNFETCHED = Symbol("unfetched");

// ---------------------------------------------------------------------------
// State (live bindings — node:test reads these directly)
// ---------------------------------------------------------------------------

// Per-view lazy cache. null=offline, []=empty, [...]=data, UNFETCHED=not yet pulled.
export const views = { all: UNFETCHED, week: UNFETCHED };

// Default view on the web is All Time (D-08 — deliberate divergence from the
// in-game This Week default; do NOT "fix").
export let activeView = "all";

// Last-week champion slot, independent of the toggle cache (mirror menu.py:176).
export let lastWeek = UNFETCHED;

// Test-only: restore module state to its initial values for isolated assertions.
export function _resetState() {
  views.all = UNFETCHED;
  views.week = UNFETCHED;
  activeView = "all";
  lastWeek = UNFETCHED;
}

// ---------------------------------------------------------------------------
// Data layer — URL build, fetch→entries|null, last-week champion, lazy cache
// ---------------------------------------------------------------------------

// Build the scoped leaderboard URL, encoding the scope param (mirror of
// api_service's urlencode({'scope': scope})). Valid scopes: week | all | last_week.
export function buildLeaderboardUrl(scope) {
  return `${LEADERBOARD_URL}?${new URLSearchParams({ scope }).toString()}`;
}

// Fetch one scope. Returns the entries array on a 200 with {entries:[...]}, else
// null. This is the exact mirror of api_service.get_leaderboard's broad
// except-→-None contract: any non-ok response, network throw, or missing entries
// key yields the single offline sentinel (null) the render layer keys off.
// `fetch` is read from globalThis so node:test can stub it.
export async function fetchEntries(scope) {
  try {
    const resp = await globalThis.fetch(buildLeaderboardUrl(scope));
    if (!resp.ok) return null;
    const data = await resp.json();
    return Array.isArray(data?.entries) ? data.entries : null;
  } catch {
    return null;
  }
}

// Champion initials for the last-week subtitle (mirror menu.py:176-177).
export function lastWeekInitials(entries) {
  return entries?.[0]?.initials ?? null;
}

// Lazy per-view cache (D-11). Fetches a scope only once; stores the result
// (entries array, [], or null) and returns it. The first time This Week loads,
// also pull the last-week champion once so its subtitle is ready.
export async function loadView(scope) {
  if (views[scope] === UNFETCHED) {
    views[scope] = await fetchEntries(scope);
    if (scope === "week" && lastWeek === UNFETCHED) {
      lastWeek = await fetchEntries("last_week");
    }
  }
  return views[scope];
}
