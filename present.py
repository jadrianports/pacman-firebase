"""Final on-screen present for Bold real play: blit the offscreen render surface to
the display with a screen-shake offset and a CRT overlay (scanlines + vignette), then
flip. Task 6 swaps in a zengl GL shader when a GL context is available; this overlay
path is the always-safe fallback.

Vignette deviation from brief: the brief's _vig used a single rounded-rect subtract
which only darkened extreme corners (~18% radius). This implementation draws concentric
border-rectangles with a quadratic alpha falloff to produce a smooth gradient that
darkens all four edges and fades cleanly to zero at ~28% depth toward the centre.

GL path (Task 6):
- try_init_crt(size) -> bool: attempt zengl context + CRT pipeline; True on success.
- present() routes through the GL shader when _gl is set, overlay otherwise.
- Any GL failure (init or per-frame) permanently sets _gl=None and falls through to
  the overlay path for the rest of the session. The game always runs.
"""
import pygame

import theme

_vignette = None

# zengl GL state — dict with keys ctx/texture/pipeline when initialised, else None.
_gl = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# CRT GLSL shaders
# ---------------------------------------------------------------------------

_VERT = """\
#version 330 core
out vec2 v_uv;
void main() {
    // Fullscreen triangle: 3 vertices cover the whole clip space.
    float x = float((gl_VertexID & 1) * 4 - 1);
    float y = float(((gl_VertexID >> 1) & 1) * 4 - 1);
    v_uv = vec2(x * 0.5 + 0.5, y * 0.5 + 0.5);
    gl_Position = vec4(x, y, 0.0, 1.0);
}
"""

_FRAG = """\
#version 330 core
uniform sampler2D Texture;
in vec2 v_uv;
out vec4 f_color;

const float BARREL   = 0.12;   // barrel-distortion strength
const float SCAN_DIM = 0.15;   // scanline darkening depth
const float BLOOM    = 0.04;   // horizontal phosphor-bloom weight

void main() {
    // --- Barrel distortion ---
    vec2 uv = v_uv * 2.0 - 1.0;
    float r2 = dot(uv, uv);
    uv *= 1.0 + BARREL * r2;
    uv = uv * 0.5 + 0.5;

    // Black outside the warped image boundary.
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        f_color = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    // --- Base colour ---
    vec3 col = texture(Texture, uv).rgb;

    // --- Scanlines: dim every third horizontal pixel row ---
    if (mod(gl_FragCoord.y, 3.0) < 1.0) {
        col *= (1.0 - SCAN_DIM);
    }

    // --- Mild phosphor bloom: 1-texel horizontal blur ---
    vec2 texel = 1.0 / vec2(textureSize(Texture, 0));
    col += texture(Texture, uv + vec2(texel.x, 0.0)).rgb * BLOOM;
    col += texture(Texture, uv - vec2(texel.x, 0.0)).rgb * BLOOM;

    f_color = vec4(col, 1.0);
}
"""


# ---------------------------------------------------------------------------
# GL initialisation
# ---------------------------------------------------------------------------

def try_init_crt(size):
    """Attempt to create a zengl context and build the CRT pipeline.

    Must be called AFTER ``pygame.display.set_mode(..., pygame.OPENGL|DOUBLEBUF)``.
    Returns True on success, False on any failure (headless, no GL driver, bad
    context, shader compile error, etc.). On failure ``_gl`` is set to None and
    the overlay path is used for the rest of the session.

    Second call after a successful first call returns True immediately (idempotent).
    """
    global _gl
    if _gl is not None:
        return True
    try:
        import zengl
        ctx = zengl.context()
        texture = ctx.image(size, 'rgba8unorm')
        pipeline = ctx.pipeline(
            vertex_shader=_VERT,
            fragment_shader=_FRAG,
            layout=[{'name': 'Texture', 'binding': 0}],
            resources=[{'type': 'sampler', 'binding': 0, 'image': texture}],
            framebuffer=None,   # render to the default (screen) framebuffer
            vertex_count=3,
        )
        _gl = {'ctx': ctx, 'texture': texture, 'pipeline': pipeline}
        return True
    except Exception:
        _gl = None
        return False


# ---------------------------------------------------------------------------
# Overlay helpers  (always-safe software path)
# ---------------------------------------------------------------------------

def _vig(size):
    """Build (and cache) a soft edge-darkening vignette overlay.

    Draws concentric 1-px border rectangles from the screen edge inward, each with
    a quadratic alpha falloff, so the edges are dark and the centre is fully
    transparent. The result is a proper border vignette rather than a corner-only
    effect.
    """
    global _vignette
    if _vignette is None or _vignette.get_size() != size:
        w, h = size
        v = pygame.Surface(size, pygame.SRCALPHA)
        v.fill((0, 0, 0, 0))
        depth = max(1, int(min(w, h) * 0.28))  # gradient reaches 28% inward
        for i in range(depth):
            t = 1.0 - i / depth                  # 1.0 at edge -> 0.0 at inner boundary
            alpha = int(100 * t * t)             # quadratic fade; max ~100 at outer edge
            pygame.draw.rect(v, (0, 0, 0, alpha), (i, i, w - 2 * i, h - 2 * i), 1)
        _vignette = v
    return _vignette


def _overlay_present(display, render_surface, shake_offset):
    """Software (overlay) present path — always safe, no GL required."""
    display.fill((0, 0, 0))
    display.blit(render_surface, shake_offset)
    size = display.get_size()
    display.blit(theme.scanline_overlay(size, spacing=3, alpha=40), (0, 0))
    display.blit(_vig(size), (0, 0))
    pygame.display.flip()


# ---------------------------------------------------------------------------
# Public present
# ---------------------------------------------------------------------------

def present(display, render_surface, shake_offset):
    """Blit ``render_surface`` to ``display`` at ``shake_offset``, apply CRT, flip.

    When a GL context was successfully initialised by ``try_init_crt``, the GL path
    (zengl CRT shader: barrel distortion + scanlines + phosphor bloom) is used and
    the pygame overlay path is skipped.  On any per-frame GL error the GL state is
    permanently discarded and the overlay path takes over for the rest of the session
    — so this function **never raises**.
    """
    global _gl
    if _gl is not None:
        try:
            ctx      = _gl['ctx']
            texture  = _gl['texture']
            pipeline = _gl['pipeline']
            ctx.new_frame()
            raw = pygame.image.tobytes(render_surface, 'RGBA', True)  # flipped for GL
            texture.write(raw)
            pipeline.render()
            ctx.end_frame()
            pygame.display.flip()
            return
        except Exception:
            _gl = None  # permanent fallback for the rest of the session

    # Software overlay path — fallback when GL is absent or failed mid-session.
    _overlay_present(display, render_surface, shake_offset)
