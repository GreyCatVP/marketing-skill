"""Pieces shared by the templates that draw their own frames (3d.html with WebGL, pixel.html on a
canvas), and the caption helper the narrated templates use. build.py and the style modules
(scene3d.py, pixel.py) import from here.

A drawn page is a narrated page whose backgrounds are drawn instead of photographed: a <canvas
class="art"> behind the text, and one empty <div class="shot" data-shot="..."> per shot that says
what to draw from its --in time until the next shot's. The text stays HTML on top, so captions
synced to a voice, sound cues, and the layout lint all work the same as on any other page.
"""


def chunked(text, start, step=0.24, max_words=4, max_chars=22):
    """Caption chunks the way captions.js builds them from a voice clip, at a steady reading pace,
    so the template shows what a narrated render looks like before any voice is recorded."""
    words = text.split()
    chunks, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        nxt = words[i + 1] if i + 1 < len(words) else None
        joined = " ".join(words[j] for j in cur)
        if nxt is None or w[-1] in ".,!?;:" or len(cur) >= max_words or len(joined) + 1 + len(nxt) > max_chars:
            chunks.append(cur)
            cur = []
    out = []
    for k, c in enumerate(chunks):
        t_in = start + c[0] * step
        t_out = start + chunks[k + 1][0] * step if k + 1 < len(chunks) else start + len(words) * step + 0.5
        ws = " ".join(f'<i style="--in:{start + j * step:.2f}s; --done:{start + (j + 1) * step:.2f}s">{words[j]}</i>' for j in c)
        out.append(f'<span class="cc" style="--in:{t_in:.2f}s; --out:{t_out:.2f}s">{ws}</span>')
    return " ".join(out)


# The timeline every drawn page runs: reads the .shot elements, builds each shot with the page's
# own SHOTS (async, so textures and fonts can load), and draws the right one for any time.
# Expects SHOTS (name -> async (el, shot) => view) and draw(view, localTime, shot) defined
# before it. A view may return events ({ land: 0.9 }): moments in the shot, in seconds from
# its start, which become CSS times on the element (--land) so data-sfx can cue sounds on them.
TIMELINE_JS = r"""
// ---- the timeline: one .shot element per shot, each running until the next one starts
const seconds = (v) => { v = (v || '').trim(); return v.endsWith('ms') ? parseFloat(v) / 1000 : parseFloat(v); };
const total = parseFloat(document.body.dataset.duration) || 0;
const timeline = [...document.querySelectorAll('.shot')]
  .map((el) => ({ el, type: el.dataset.shot, in: seconds(getComputedStyle(el).getPropertyValue('--in')) || 0 }))
  .sort((a, b) => a.in - b.in);
timeline.forEach((s, i) => {
  s.dur = Math.max(0.1, (timeline[i + 1] ? timeline[i + 1].in : total) - s.in);
  s.first = s.in <= 0.001; // on screen at frame 0, the cover: shown settled, without an entrance
});
let ready = false;
window.renderReady = (async () => {
  const problems = [];
  for (const s of timeline) {
    if (!SHOTS[s.type]) { problems.push(`unknown shot "${s.type}" (known: ${Object.keys(SHOTS).join(', ')})`); continue; }
    try {
      s.view = await SHOTS[s.type](s.el, s);
      for (const [name, at] of Object.entries(s.view.events || {})) s.el.style.setProperty(`--${name}`, `${(s.in + at).toFixed(2)}s`);
    } catch (e) {
      problems.push(`shot "${s.type}" at ${s.in}s: ${e.message || e}`);
    }
  }
  ready = true;
  if (problems.length) throw new Error(problems.join('; '));
})();
window.renderFrame = (t) => {
  if (!ready || !timeline.length) return;
  let i = 0;
  while (i + 1 < timeline.length && timeline[i + 1].in <= t + 1e-6) i++;
  document.body.dataset.shot = String(i);
  if (timeline[i].view) draw(timeline[i].view, Math.max(0, t - timeline[i].in), timeline[i]);
};
// Opened in a browser rather than rendered (render.js drives the page through WebDriver), it
// plays in real time alongside the CSS animations.
if (!navigator.webdriver) {
  window.renderReady.catch((e) => console.warn(e.message)).then(() => {
    const tick = () => { window.renderFrame(Math.min(total, (document.timeline.currentTime || 0) / 1000)); requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
  });
}
"""

# The narrated layout, as in narrated.html: the hook at the top of the first scene, captions low in
# the safe area, and a CTA caption at the top of the last.
NARRATED_CSS = """
  .glow { display: none; }
  .art { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; }
  .shot { display: none; }
  .scene.narr { justify-content: flex-end; padding-bottom: 30px; }
  .narr > .hook, .narr > .end { margin-bottom: auto; }
  .hook { font-size: 70px; line-height: 1.4; }
  .narr .say { min-height: 220px; }
"""


def drawn_body(canvas, shots, lines, hook, cta):
    """The body of a drawn narrated page. `shots` are (start, name, attrs) and `lines` (start, text);
    each line is a scene running until the next one, the first with the hook, the last with the CTA."""
    out = [f"  {canvas}", '  <div class="art-scrim" data-lint="off"></div>', "",
           "  <!-- the shots: what's drawn, and from when (see the comment above) -->"]
    for start, name, attrs in shots:
        out.append(f'  <div class="shot" data-shot="{name}" style="--in:{start}s"{attrs}></div>')
    for k, (start, text) in enumerate(lines):
        nxt = lines[k + 1][0] if k + 1 < len(lines) else None
        span = f"{start}–{nxt}s" if nxt is not None else f"{start}s–end"
        parts = []
        if k == 0:
            parts.append(f'    <div class="cap hook"><span>{hook}</span></div>')
        if nxt is None:
            parts.append(f'    <div class="end"><div class="cap hl pop" style="--in:{start}s" data-sfx="chime"><span>{cta}</span></div></div>')
        parts.append(f'    <div class="say auto" style="--voice:{start}s">{chunked(text, start)}</div>')
        style = f' style="--out:{nxt - 0.15:.2f}s"' if nxt is not None else ""
        out.append(f"\n  <!-- line {k + 1}, {span} -->\n  <div class=\"scene narr center\"{style}>\n" + "\n".join(parts) + "\n  </div>")
    return "\n".join(out) + "\n"
