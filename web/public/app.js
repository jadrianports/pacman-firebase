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

// ---------------------------------------------------------------------------
// Render layer — three-way state branch + rank rows + escaping
// ---------------------------------------------------------------------------

// Verbatim empty-state copy per view (D-12, mirror menu.py:179-182).
const EMPTY_TEXT = {
  week: "No scores yet this week. Be the first!",
  all: "No scores yet. Be the first!",
};
const OFFLINE_TEXT = "Could not connect to leaderboard.";
const LOADING_TEXT = "Loading...";

// HTML-escape untrusted API data before it is written into #board. Defense in
// depth: the server already enforces ^[A-Z]{3}$ on initials, but we never trust
// raw API strings in markup (T-07-01 XSS mitigation).
function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// Score formatting — en-US thousands separators (D, Claude's discretion).
// Tolerates string scores; falls back to the raw (escaped at call site) value
// for anything non-numeric.
export function formatScore(n) {
  const num = Number(n);
  return Number.isFinite(num) ? num.toLocaleString("en-US") : String(n);
}

// Build the #board inner markup for the active view (mirror menu.py:222-242):
//   entries === null     -> offline line
//   entries.length === 0 -> view-specific empty line
//   else                 -> one rank-row <li> per entry, rank-1 gets rank-row--first
// Returns an HTML string built ENTIRELY from escaped values (no raw API data
// reaches innerHTML). The dot-leader is an empty span styled in CSS (Plan 03).
export function boardMarkup(entries, view) {
  if (entries === null) {
    return `<li class="state-msg">${OFFLINE_TEXT}</li>`;
  }
  if (entries.length === 0) {
    return `<li class="state-msg">${EMPTY_TEXT[view] ?? EMPTY_TEXT.all}</li>`;
  }
  return entries
    .map((entry, i) => {
      const cls = i === 0 ? "rank-row rank-row--first" : "rank-row";
      const rank = `${i + 1}.`;
      const initials = escapeHtml(entry?.initials);
      const score = escapeHtml(formatScore(entry?.score));
      return (
        `<li class="${cls}">` +
        `<span class="rank">${rank}</span>` +
        `<span class="initials">${initials}</span>` +
        `<span class="dots" aria-hidden="true"></span>` +
        `<span class="score">${score}</span>` +
        `</li>`
      );
    })
    .join("");
}

// ---------------------------------------------------------------------------
// Interaction layer — render active view, toggle, refresh, DOM bootstrap
// ---------------------------------------------------------------------------

function paintLoading() {
  const board = document.getElementById("board");
  if (board) board.innerHTML = `<li class="state-msg">${LOADING_TEXT}</li>`;
}

// Render the active view into the DOM: board content, tab highlight, and the
// last-week subtitle (This Week only, shown only when a champion exists — D-09).
export function renderActive() {
  const board = document.getElementById("board");
  if (board) board.innerHTML = boardMarkup(views[activeView], activeView);

  const tabAll = document.getElementById("tab-all");
  const tabWeek = document.getElementById("tab-week");
  if (tabAll && tabWeek) {
    tabAll.classList.toggle("tab--active", activeView === "all");
    tabWeek.classList.toggle("tab--active", activeView === "week");
    tabAll.setAttribute("aria-selected", String(activeView === "all"));
    tabWeek.setAttribute("aria-selected", String(activeView === "week"));
  }

  const subtitle = document.getElementById("subtitle");
  if (subtitle) {
    const champ = lastWeekInitials(lastWeek === UNFETCHED ? null : lastWeek);
    if (activeView === "week" && champ) {
      subtitle.textContent = `Last week: ${champ}`;
      subtitle.hidden = false;
    } else {
      subtitle.textContent = "";
      subtitle.hidden = true;
    }
  }
}

// Tab tap — switch the active view, lazily fetching it the first time (D-11).
export async function onTabClick(scope) {
  if (scope !== "all" && scope !== "week") return;
  activeView = scope;
  if (views[scope] === UNFETCHED) {
    paintLoading();
    await loadView(scope);
  }
  renderActive();
}

// Refresh — force-refetch ONLY the active view, leaving the other view's cache
// intact (D-10, independent degrade). On This Week also re-pull last-week.
export async function onRefresh() {
  views[activeView] = UNFETCHED;
  if (activeView === "week") lastWeek = UNFETCHED;
  paintLoading();
  await loadView(activeView);
  renderActive();
}

// DOM bootstrap — guarded so a non-browser import (node:test) is fully inert
// and never touches fetch. Wires the tab buttons (by data-scope) and Refresh,
// then loads the default All Time view (D-08).
export async function init() {
  if (typeof document === "undefined") return;

  for (const tab of document.querySelectorAll("#tabbar .tab")) {
    tab.addEventListener("click", () => onTabClick(tab.dataset.scope));
  }
  const refresh = document.getElementById("refresh");
  if (refresh) refresh.addEventListener("click", () => onRefresh());

  paintLoading();
  await loadView("all");
  renderActive();
}

// Self-guarded — inert when imported without a document.
init();
