import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

// Resolve repo paths relative to this test file (web/tests/ -> repo root is ../..).
const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..', '..');
const read = (rel) => readFileSync(join(repoRoot, rel), 'utf8');

// ---------------------------------------------------------------------------
// Task 1 — index.html: semantic board skeleton + branding head
// ---------------------------------------------------------------------------

const html = read('web/public/index.html');

test('index.html: browser tab title is exactly the branded em-dash title (D-14)', () => {
  assert.match(html, /<title>PAC-MAN — Leaderboard<\/title>/);
});

test('index.html: wordmark present with PAC-MAN text', () => {
  assert.match(html, /class="wordmark"/);
  assert.match(html, /<h1 class="wordmark">PAC-MAN<\/h1>/);
});

test('index.html: tab bar exposes both tabs with stable ids + data-scope hooks', () => {
  assert.match(html, /id="tabbar"/);
  assert.match(html, /id="tab-all"/);
  assert.match(html, /id="tab-week"/);
  assert.match(html, /data-scope="all"/);
  assert.match(html, /data-scope="week"/);
});

test('index.html: tab labels are verbatim in-game copy (D-12)', () => {
  assert.ok(html.includes('>All Time<'), 'All Time label present');
  assert.ok(html.includes('>This Week<'), 'This Week label present');
});

test('index.html: All Time tab carries tab--active on load (D-08 default), not This Week', () => {
  const allTabMatch = html.match(/<button id="tab-all"[^>]*>/);
  assert.ok(allTabMatch, '#tab-all button element exists');
  assert.match(allTabMatch[0], /tab--active/);

  const weekTabMatch = html.match(/<button id="tab-week"[^>]*>/);
  assert.ok(weekTabMatch, '#tab-week button element exists');
  assert.doesNotMatch(weekTabMatch[0], /tab--active/);
});

test('index.html: subtitle slot is present and hidden by default (D-09)', () => {
  const subMatch = html.match(/<p id="subtitle"[^>]*>/);
  assert.ok(subMatch, '#subtitle element exists');
  assert.match(subMatch[0], /\bhidden\b/);
});

test('index.html: board region exists and is seeded with the verbatim Loading line (D-12)', () => {
  assert.match(html, /id="board"/);
  assert.ok(html.includes('Loading...'), 'seed Loading... state message present');
});

test('index.html: refresh control present with verbatim Refresh copy (D-10)', () => {
  const refreshMatch = html.match(/<button id="refresh"[^>]*>Refresh<\/button>/);
  assert.ok(refreshMatch, '#refresh button with text Refresh exists');
});

test('index.html: hint region present', () => {
  assert.match(html, /id="hint"/);
});

test('index.html: Open Graph image is the absolute 1200x630 preview url (D-13)', () => {
  assert.ok(
    html.includes('property="og:image" content="https://pacman-firebase.web.app/og-preview.png"'),
    'absolute og:image url present',
  );
  assert.match(html, /property="og:image:width" content="1200"/);
  assert.match(html, /property="og:image:height" content="630"/);
});

test('index.html: Twitter Card is summary_large_image with the same absolute image', () => {
  assert.match(html, /name="twitter:card" content="summary_large_image"/);
  assert.ok(
    html.includes('name="twitter:image" content="https://pacman-firebase.web.app/og-preview.png"'),
    'absolute twitter:image url present',
  );
});

test('index.html: references styles.css, app.js (module) and favicon.svg', () => {
  assert.match(html, /<link rel="stylesheet" href="styles\.css">/);
  assert.match(html, /<script type="module" src="app\.js"><\/script>/);
  assert.match(html, /href="favicon\.svg"/);
});

// ---------------------------------------------------------------------------
// Task 2 — Firebase Hosting config + ESM marker
// ---------------------------------------------------------------------------

test('firebase.json: valid JSON, hosting.public points at web/public', () => {
  const cfg = JSON.parse(read('firebase.json'));
  assert.equal(cfg.hosting.public, 'web/public');
});

test('firebase.json: ignore excludes firebase.json itself', () => {
  const cfg = JSON.parse(read('firebase.json'));
  assert.ok(Array.isArray(cfg.hosting.ignore), 'ignore is an array');
  assert.ok(cfg.hosting.ignore.includes('firebase.json'), 'ignore drops firebase.json');
});

test('firebase.json: hosting-only — no functions/rewrites-to-backend blocks', () => {
  const cfg = JSON.parse(read('firebase.json'));
  assert.equal(cfg.functions, undefined, 'no functions block');
  assert.equal(cfg.hosting.rewrites, undefined, 'no rewrites block');
});

test('.firebaserc: default project pins pacman-firebase (D-15)', () => {
  const rc = JSON.parse(read('.firebaserc'));
  assert.equal(rc.projects.default, 'pacman-firebase');
});

test('web/package.json: ESM type marker with no dependencies block (D-01 no build step)', () => {
  const pkg = JSON.parse(read('web/package.json'));
  assert.equal(pkg.type, 'module');
  assert.equal(pkg.dependencies, undefined, 'no dependencies block');
});
