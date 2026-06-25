// node:test coverage for web/public/app.js — the page's behavioral core.
// Pure data/render functions are exercised with a stubbed globalThis.fetch.
// Run: node --test web/tests/app.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";

import {
  LEADERBOARD_URL,
  UNFETCHED,
  buildLeaderboardUrl,
  fetchEntries,
  lastWeekInitials,
  loadView,
  views,
  activeView,
  boardMarkup,
  formatScore,
  init,
  _resetState,
} from "../public/app.js";

const ORIGINAL_FETCH = globalThis.fetch;

function stubFetch(impl) {
  globalThis.fetch = impl;
}
function restoreFetch() {
  globalThis.fetch = ORIGINAL_FETCH;
}

// ---------------------------------------------------------------------------
// Task 1 — data layer: URL build, fetch→entries|null, last-week, lazy cache
// ---------------------------------------------------------------------------

test("LEADERBOARD_URL mirrors settings.API_LEADERBOARD_URL host (D-03)", () => {
  assert.ok(
    LEADERBOARD_URL.includes("get-leaderboard-991339031546"),
    "LEADERBOARD_URL must mirror the deployed get_leaderboard host"
  );
});

test("buildLeaderboardUrl encodes the scope param for all valid scopes", () => {
  assert.equal(
    buildLeaderboardUrl("all"),
    "https://get-leaderboard-991339031546.asia-southeast1.run.app?scope=all"
  );
  assert.equal(
    buildLeaderboardUrl("week"),
    "https://get-leaderboard-991339031546.asia-southeast1.run.app?scope=week"
  );
  assert.equal(
    buildLeaderboardUrl("last_week"),
    "https://get-leaderboard-991339031546.asia-southeast1.run.app?scope=last_week"
  );
});

test("fetchEntries returns the entries array on a 200 with {entries:[...]}", async () => {
  const rows = [{ initials: "BOB", score: 12345 }];
  stubFetch(async () => ({ ok: true, json: async () => ({ entries: rows }) }));
  try {
    assert.deepEqual(await fetchEntries("all"), rows);
  } finally {
    restoreFetch();
  }
});

test("fetchEntries returns null (offline sentinel) on a non-ok response", async () => {
  stubFetch(async () => ({ ok: false, json: async () => ({ entries: [] }) }));
  try {
    assert.equal(await fetchEntries("all"), null);
  } finally {
    restoreFetch();
  }
});

test("fetchEntries returns null when fetch rejects/throws (never throws)", async () => {
  stubFetch(async () => {
    throw new Error("network down");
  });
  try {
    assert.equal(await fetchEntries("week"), null);
  } finally {
    restoreFetch();
  }
});

test("fetchEntries returns null when the body has no entries key", async () => {
  stubFetch(async () => ({ ok: true, json: async () => ({ error: "boom" }) }));
  try {
    assert.equal(await fetchEntries("all"), null);
  } finally {
    restoreFetch();
  }
});

test("lastWeekInitials returns the champion / null for empty / null", () => {
  assert.equal(lastWeekInitials([{ initials: "BOB", score: 9 }]), "BOB");
  assert.equal(lastWeekInitials([]), null);
  assert.equal(lastWeekInitials(null), null);
});

test("initial state: activeView is 'all' (D-08) and both views UNFETCHED", () => {
  _resetState();
  // Re-import the live binding value via a fresh require is unnecessary in ESM:
  // `activeView` is a live binding, so it reflects the post-reset value.
  assert.equal(activeView, "all");
  assert.equal(views.all, UNFETCHED);
  assert.equal(views.week, UNFETCHED);
});

test("loadView caches per scope — a second call does not refetch", async () => {
  _resetState();
  const rows = [{ initials: "BOB", score: 5 }];
  stubFetch(async () => ({ ok: true, json: async () => ({ entries: rows }) }));
  const first = await loadView("all");
  assert.deepEqual(first, rows);

  // Swap in a fetch that would throw; the cached slot must be returned untouched.
  stubFetch(async () => {
    throw new Error("should not be called");
  });
  try {
    const second = await loadView("all");
    assert.deepEqual(second, first);
  } finally {
    restoreFetch();
  }
});

// ---------------------------------------------------------------------------
// Task 2 — render + interaction: state branches, rank rows, escaping, bootstrap
// ---------------------------------------------------------------------------

function countMatches(haystack, re) {
  return (haystack.match(re) || []).length;
}

test("boardMarkup(null, view) renders the verbatim offline line for both views", () => {
  for (const view of ["all", "week"]) {
    const html = boardMarkup(null, view);
    assert.match(html, /class="state-msg"/);
    assert.ok(
      html.includes("Could not connect to leaderboard."),
      `offline copy must be verbatim for view=${view}`
    );
  }
});

test("boardMarkup([], view) renders the view-specific verbatim empty line", () => {
  const week = boardMarkup([], "week");
  assert.match(week, /class="state-msg"/);
  assert.ok(week.includes("No scores yet this week. Be the first!"));

  const all = boardMarkup([], "all");
  assert.match(all, /class="state-msg"/);
  assert.ok(all.includes("No scores yet. Be the first!"));
});

test("boardMarkup(entries) renders one rank-row each; only rank 1 is --first", () => {
  const html = boardMarkup(
    [
      { initials: "BOB", score: 12345 },
      { initials: "AMY", score: 9000 },
    ],
    "all"
  );
  assert.equal(countMatches(html, /class="rank-row/g), 2, "one row per entry");
  assert.equal(
    countMatches(html, /rank-row--first/g),
    1,
    "exactly one rank-1 highlight"
  );
  // Rank 1 (BOB) carries the highlight; row 2 (AMY) does not.
  const firstRowIdx = html.indexOf("rank-row--first");
  assert.ok(firstRowIdx >= 0);
  assert.ok(html.indexOf("BOB") > firstRowIdx, "rank-1 row holds the top score");
  assert.ok(html.includes("AMY"));
  // Formatted score with thousands separators present.
  assert.ok(html.includes("12,345"));
});

test("boardMarkup escapes hostile initials — no live <img> element (T-07-01)", () => {
  const html = boardMarkup([{ initials: "<img src=x>", score: 1 }], "all");
  assert.ok(!html.includes("<img"), "raw <img must not appear in the markup");
  assert.ok(html.includes("&lt;img"), "hostile initials must be HTML-escaped");
});

test("formatScore applies en-US thousands separators and tolerates strings", () => {
  assert.equal(formatScore(12345), "12,345");
  assert.equal(formatScore("9000"), "9,000");
});

test("init() is inert without a document — no fetch at import/call time", async () => {
  let called = false;
  stubFetch(async () => {
    called = true;
    return { ok: true, json: async () => ({ entries: [] }) };
  });
  try {
    await init();
    assert.equal(called, false, "init must not fetch when document is undefined");
  } finally {
    restoreFetch();
  }
});
