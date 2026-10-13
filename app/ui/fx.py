"""Small, isolated interaction layer: a restrained cursor ring and smooth in-page anchor scrolling.

One idempotent script, injected once per browser page (guarded by `window.__ssFx`). It only runs for fine pointers
without a reduced-motion preference, never hides the native cursor, never captures events (pointer-events:none),
and does all per-frame work with a single `transform` write inside requestAnimationFrame, with no Streamlit reruns.
"""
from __future__ import annotations

import streamlit as st

_JS = """
(() => {
  if (window.__ssFx) return;
  window.__ssFx = true;
  const mq = (q) => window.matchMedia && window.matchMedia(q).matches;
  if (!mq('(pointer: fine)') || mq('(prefers-reduced-motion: reduce)')) return;
  const ring = document.createElement('div');
  ring.className = 'ss-cursor';
  ring.setAttribute('aria-hidden', 'true');
  const dot = document.createElement('i'), halo = document.createElement('b');   // no HTML literals: Streamlit's sanitiser breaks them
  ring.append(dot, halo);
  document.body.appendChild(ring);
  let x = -100, y = -100, hx = -100, hy = -100, raf = 0;
  const HOVER = 'a,button,[role="tab"],[role="switch"],[role="checkbox"],summary,label,[data-baseweb="select"],[data-testid="stPageLink-NavLink"],.ss-slot:not(.free),.ss-pick';
  const TEXT = 'input,textarea,[contenteditable="true"]';
  const tick = () => {
    hx += (x - hx) * 0.2; hy += (y - hy) * 0.2;
    dot.style.transform = 'translate3d(' + x + 'px,' + y + 'px,0)';
    halo.style.transform = 'translate3d(' + hx + 'px,' + hy + 'px,0)';
    raf = (Math.abs(x - hx) + Math.abs(y - hy) > 0.3) ? requestAnimationFrame(tick) : 0;
  };
  window.addEventListener('pointermove', (e) => {
    if (e.pointerType && e.pointerType !== 'mouse') return;
    x = e.clientX; y = e.clientY;
    ring.classList.add('on');
    const t = e.target instanceof Element ? e.target : null;
    ring.classList.toggle('text', !!(t && t.closest(TEXT)));
    ring.classList.toggle('link', !!(t && t.closest(HOVER)) && !(t && t.closest(TEXT)));
    if (!raf) raf = requestAnimationFrame(tick);
  }, { passive: true });
  window.addEventListener('pointerdown', () => ring.classList.add('down'), { passive: true });
  window.addEventListener('pointerup', () => ring.classList.remove('down'), { passive: true });
  document.addEventListener('mouseleave', () => ring.classList.remove('on'));
})();
"""


def inject_fx() -> None:
    """Render the cursor script (no layout space). Safe to call on every run: the script guards itself."""
    st.html(f"<script>{_JS}</script>", unsafe_allow_javascript=True)
