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
