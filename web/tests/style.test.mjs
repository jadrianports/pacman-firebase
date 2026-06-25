import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

// Resolve repo paths relative to this test file (web/tests/ -> repo root is ../..).
const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..', '..');
const path = (rel) => join(repoRoot, rel);
const read = (rel) => readFileSync(path(rel), 'utf8');

// ===========================================================================
// Plan 03 — Task 1: styles.css retro-arcade contract (07-UI-SPEC tokens)
// ===========================================================================

const css = read('web/public/styles.css');

test('styles.css: declares all five locked color tokens (UI-SPEC / settings.py COLOR_*)', () => {
  for (const hex of ['#000000', '#10102E', '#FFFF00', '#FFFFFF', '#808080']) {
    assert.ok(css.includes(hex), `styles.css must contain token ${hex}`);
  }
});

test('styles.css: defines a selector for every Plan 01 DOM hook', () => {
  for (const sel of [
    '.wordmark',
    '.tab',
    '.tab--active',
    '.subtitle',
    '.board',
    '.rank-row',
    '.rank-row--first',
    '.dots',
    '.state-msg',
    '.refresh',
    '.hint',
  ]) {
    assert.ok(css.includes(sel), `styles.css must style ${sel}`);
  }
});

test('styles.css: two-family type system — Press Start 2P + monospace stack (D-06)', () => {
  assert.ok(css.includes('Press Start 2P'), 'pixel display face must be declared');
  assert.ok(/monospace/.test(css), 'a monospace body stack must be present');
});

test('styles.css: self-hosts the pixel font via @font-face (D-16 zero third-party)', () => {
  assert.match(css, /@font-face/);
  assert.match(css, /fonts\/PressStart2P-Regular\.(woff2|ttf)/);
});

test('styles.css: responsive / mobile-first — at least one @media query', () => {
  assert.match(css, /@media/);
});

test('styles.css: .tab carries a 44px min-height touch target (WCAG 2.5.5)', () => {
  // Isolate the base .tab rule body and assert min-height resolves to 44px
  // (either literally `44px` or via the --touch token which is 44px).
  const tabRule = css.match(/\.tab\s*\{[^}]*\}/);
  assert.ok(tabRule, '.tab rule block must exist');
  assert.match(tabRule[0], /min-height:\s*(44px|var\(--touch\))/);
});

test('styles.css: .refresh carries a 44px min-height touch target (WCAG 2.5.5)', () => {
  const refreshRule = css.match(/\.refresh\s*\{[^}]*\}/);
  assert.ok(refreshRule, '.refresh rule block must exist');
  assert.match(refreshRule[0], /min-height:\s*(44px|var\(--touch\))/);
});

test('styles.css: --touch token (or literal) anchors the 44px target value', () => {
  assert.ok(css.includes('44px'), 'styles.css must reference the 44px touch value');
  assert.ok(
    /min-height/.test(css) && css.includes('44px'),
    'min-height must co-occur with the 44px touch target',
  );
});

test('styles.css: dot-leaders are pure-CSS pellets, not literal dot characters', () => {
  const dotsRule = css.match(/\.rank-row\s+\.dots\s*\{[^}]*\}/);
  assert.ok(dotsRule, '.rank-row .dots rule block must exist');
  assert.match(dotsRule[0], /radial-gradient|repeating-/);
});

test('styles.css: substantive stylesheet (>= 80 non-empty lines)', () => {
  const lines = css.split('\n').filter((l) => l.trim().length > 0);
  assert.ok(lines.length >= 80, `expected >= 80 non-empty lines, got ${lines.length}`);
});

test('styles.css: self-hosted font file is present on disk (no Google Fonts fetch)', () => {
  const ttf = existsSync(path('web/public/fonts/PressStart2P-Regular.ttf'));
  const woff2 = existsSync(path('web/public/fonts/PressStart2P-Regular.woff2'));
  assert.ok(ttf || woff2, 'a self-hosted Press Start 2P font file must exist under web/public/fonts/');
});

// ===========================================================================
// Plan 03 — Task 2: branding assets (favicon.svg + ~1200x630 og-preview.png)
// ===========================================================================

test('favicon.svg: exists and is a valid scalable SVG with a viewBox (D-14)', () => {
  assert.ok(existsSync(path('web/public/favicon.svg')), 'favicon.svg must exist');
  const svg = read('web/public/favicon.svg');
  assert.match(svg, /<svg/, 'favicon must have an <svg> root');
  assert.match(svg, /viewBox\s*=/, 'favicon must declare a viewBox so it scales in the tab');
});

test('favicon.svg: depicts Pac-Man in arcade yellow, no executable script', () => {
  const svg = read('web/public/favicon.svg');
  assert.ok(/#FFFF00/i.test(svg), 'Pac-Man disc must use accent yellow #FFFF00');
  assert.ok(!/<script/i.test(svg), 'favicon must contain no <script> (T-07-01)');
});

test('og-preview.png: exists and IHDR dimensions are 1200x630 (D-13)', () => {
  assert.ok(existsSync(path('web/public/og-preview.png')), 'og-preview.png must exist');
  const buf = readFileSync(path('web/public/og-preview.png'));
  // PNG signature check.
  assert.deepEqual(
    [...buf.subarray(0, 8)],
    [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a],
    'file must be a real PNG (signature)',
  );
  // IHDR: 4-byte big-endian width @ offset 16, height @ offset 20.
  const width = buf.readUInt32BE(16);
  const height = buf.readUInt32BE(20);
  if (width === 1200 && height === 630) {
    assert.ok(true);
  } else {
    // Allow any 1.91:1 card >= 1200px wide as a fallback (D-13 ~1200x630).
    const ratio = width / height;
    assert.ok(width >= 1200, `og width must be >= 1200, got ${width}`);
    assert.ok(ratio >= 1.9 && ratio <= 1.92, `og aspect must be ~1.91:1, got ${ratio.toFixed(3)}`);
  }
});

test('index.html: og:image / twitter:image resolve to the created og-preview.png', () => {
  const html = read('web/public/index.html');
  assert.match(html, /property="og:image"[^>]*content="[^"]*og-preview\.png"/);
  assert.match(html, /name="twitter:image"[^>]*content="[^"]*og-preview\.png"/);
});

test('index.html: favicon link resolves to the created favicon.svg', () => {
  const html = read('web/public/index.html');
  assert.match(html, /rel="icon"[^>]*href="favicon\.svg"/);
});
