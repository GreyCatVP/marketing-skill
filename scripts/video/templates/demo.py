"""The product demo for the 3D template (3d.html): the product's own screens, the way a launch
video shows them. A terminal types the real commands, an AI agent's session streams the steps a
skill takes, the real things it made float past, and a camera moves over all of it instead of
cutting. scene3d.py appends DEMO_JS to its engine, after the mascot, so a desk shot can push into
the monitor and hand the frame to the screen on it.

The screens are HTML, not WebGL: crisp text at any zoom, and cheap to render. Each one is laid
out once in a layer above the 3D canvas, hidden, and shown by its shot's frame(lt), which sets
what has been typed by then and where the camera is, so every frame is still a pure function of
time.
"""

DEMO_DOC = """    terminal  a terminal typing the product's real commands, the camera pushing
              in on the line being typed: data-lines="$ claude plugin
              marketplace add you/repo|Marketplace added" (a line starting
              "$ " is typed, the rest print as its output; | between lines).
              data-title names the window. Events: --type, --done.
    agent     an AI agent's session (Claude Code, Codex): data-ask is typed
              at its prompt, then data-steps stream in as its tool calls
              ("Web search(acme pricing)|Write(battlecard.md)"; a line
              starting "⎿" is the result of the step above it) and data-done
              ends it. data-doc="# Acme battlecard|- Pricing: ..." slides in
              the document it wrote, and the camera pans over to it. Show
              the steps the skill really takes. data-app names the agent
              (default Claude Code). Events: --type, --done.
    wall      the real things the product made, floating in the dark as the
              camera flies through them: data-items="assets/a.jpg,assets/
              b.jpg" (frames, thumbnails, screenshots; up to 24), with
              data-labels="promo,how-to" under them. Event: --done.
    player    a video player playing the user's real video or image
              (data-src, an .mp4 or a picture), the scrubber moving under
              it; data-title is its file name, data-aspect="16:9" a clip's
              shape, data-offset where in the clip to start. Event: --play.
    comments  the ending: a handwritten question (data-text) over a comment
              box whose placeholder types out data-ask, the call for
              comments. It shows no one's comments.
  These screen shots move from one to the next without a cut: the camera
  pushes through one into the next. A desk shot just before one shows it
  live on the monitor and pushes into it until the screen is the frame;
  data-mascot="no" leaves the room empty, as product videos do."""

DEMO_CSS = """  /* the product demo's screens (demo.py): laid out once, shown by their shot */
  .ui-layer { position: absolute; left: 0; top: 0; width: 100%; height: 100%; overflow: hidden; pointer-events: none; }
  .ui-shot { position: absolute; left: 0; top: 0; width: 100%; height: 100%; visibility: hidden; overflow: hidden; transform-origin: 0 0;
             background: radial-gradient(ellipse 85% 75% at 50% 40%, #1b1b21 0%, #0d0d10 58%, #060608 100%); }
  .ui-bokeh i { position: absolute; left: 0; top: 0; border-radius: 50%; background: radial-gradient(circle, rgba(255,255,255,.85), rgba(255,255,255,0) 70%); }
  .ui-bokeh i.a { background: radial-gradient(circle, var(--accent), transparent 70%); }
  .ui-world { position: absolute; left: 0; top: 0; width: 0; height: 0; transform-origin: 0 0; transform-style: preserve-3d; }
  .ui-win { position: absolute; border-radius: 18px; background: #111114; border: 1px solid #2a2a31; overflow: hidden;
            box-shadow: 0 50px 140px rgba(0,0,0,.7), 0 0 0 1px rgba(255,255,255,.03) inset; }
  .ui-bar { position: relative; height: 46px; display: flex; align-items: center; gap: 9px; padding: 0 20px; background: #19191e; border-bottom: 1px solid #25252b; }
  .ui-bar i { width: 13px; height: 13px; border-radius: 50%; background: #ff5f57; }
  .ui-bar i:nth-child(2) { background: #febc2e; }
  .ui-bar i:nth-child(3) { background: #28c840; }
  .ui-bar span { position: absolute; left: 0; right: 0; text-align: center; font: 500 18px Inter, sans-serif; color: #85848f; }
  .ui-body { position: absolute; left: 0; right: 0; top: 46px; bottom: 0; overflow: hidden; }
  .ui-scroll { padding: 26px 32px; font-family: "JetBrains Mono", "DejaVu Sans Mono", monospace; font-weight: 500; line-height: 1.55; color: #d9d8d3;
               white-space: pre-wrap; overflow-wrap: anywhere; }
  .ui-line { visibility: hidden; min-height: 1.55em; }
  .ui-line.cmd::before { content: "$ "; color: var(--accent); }
  .ui-line.ok { color: #84d6a0; }
  .ui-line.res { color: #7c7b86; padding-left: 1.6em; }
  .ui-line.ask { color: #fff; }
  .ui-line.ask::before { content: "> "; color: #7c7b86; }
  .ui-line.step .dot { color: #84d6a0; }
  .ui-line.step b { font-weight: 500; color: #fff; }
  .ui-line.done { color: var(--accent); margin-top: .5em; }
  .ui-line.spin { color: var(--accent); }
  .ui-caret { display: inline-block; width: .56em; height: 1.12em; background: #d9d8d3; vertical-align: -.2em; margin-left: .08em; }
  .ui-welcome { display: flex; gap: .7em; align-items: center; border: 2px solid var(--accent); border-radius: 12px; padding: .55em .9em; margin-bottom: 1.1em; color: #fff; }
  .ui-welcome b { color: var(--accent); font-weight: 500; }
  .ui-welcome span { margin-left: auto; color: #7c7b86; }
  .ui-doc { position: absolute; border-radius: 16px; background: #f5f3ee; color: #1c1c21; padding: 36px 40px; overflow: hidden;
            font: 500 25px/1.5 Inter, sans-serif; box-shadow: 0 60px 160px rgba(0,0,0,.75); }
  .ui-doc .h { font-weight: 800; font-size: 1.45em; line-height: 1.2; margin-bottom: .65em; letter-spacing: -.01em; }
  .ui-doc .p { margin-bottom: .45em; }
  .ui-doc .p.li { padding-left: 1.1em; text-indent: -1.1em; }
  .ui-doc .p.li::before { content: "•  "; color: var(--accent); }
  .ui-doc .p.sub { font-weight: 700; margin-top: .7em; }
  .ui-card { position: absolute; left: 0; top: 0; transform-origin: 50% 50%; }
  .ui-card img { display: block; width: 100%; height: 100%; object-fit: cover; border-radius: 14px; box-shadow: 0 34px 90px rgba(0,0,0,.65); }
  .ui-card span { position: absolute; left: 0; right: 0; top: 100%; margin-top: 14px; text-align: center; font: 600 22px Inter, sans-serif; color: #9796a1; }
  .ui-media { position: absolute; left: 0; top: 0; width: 100%; height: 100%; object-fit: contain; background: #000; }
  .ui-scrub { position: absolute; left: 28px; right: 28px; bottom: 26px; height: 6px; border-radius: 3px; background: #2c2c33; }
  .ui-scrub b { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 3px; background: var(--accent); }
  .ui-scrub i { position: absolute; top: -7px; width: 20px; height: 20px; margin-left: -10px; border-radius: 50%; background: #fff; }
  .ui-hand { position: absolute; left: 0; right: 0; text-align: center; font: 700 120px/1.1 "Caveat", cursive; color: #fff; }
  .ui-box { position: absolute; border-radius: 22px; background: #141418; border: 1px solid #2a2a31; padding: 30px 34px; box-shadow: 0 50px 140px rgba(0,0,0,.7);
            font: 500 30px/1.4 Inter, sans-serif; color: #8d8c97; }
  .ui-box .top { display: flex; justify-content: space-between; color: #fff; font-weight: 700; margin-bottom: 26px; }
  .ui-box .row { display: flex; gap: 22px; align-items: center; }
  .ui-box .av { width: 64px; height: 64px; border-radius: 50%; background: linear-gradient(135deg, var(--accent), #6b5cff); flex: none; }
  .ui-box .in { flex: 1; border-bottom: 2px solid #34343c; padding: 10px 0; color: #e9e8e4; white-space: nowrap; overflow: hidden; }
  .ui-box .ph { color: #6f6e79; }
  .ui-box .post { padding: 12px 26px; border-radius: 30px; background: #26262d; color: #77767f; font-weight: 700; }
"""

DEMO_JS = r"""
// ================= the product demo: the product's own screens, and a camera moving over them =================
const SCREEN_SHOTS = new Set(['terminal', 'agent', 'wall', 'player', 'comments']); // a desk before one pushes into it
const uiLayer = document.createElement('div');
uiLayer.className = 'ui-layer';
uiLayer.dataset.lint = 'off'; // the screens are the picture, like the canvas; the captions over them are checked
ART.after(uiLayer);
const escHtml = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const listOf = (s, sep = '|') => (s || '').split(sep).map((x) => x.trim()).filter(Boolean);
const FS = WIDE ? 25 : 29; // the screens' text size at zoom 1; the camera pushes in to read it

// The CSS matrix3d that maps a w x h box onto four points (top left, top right, bottom right,
// bottom left, in frame pixels): how a screen's page sits on a 3D monitor.
function quadMatrix(w, h, pts) {
  const rows = [], rhs = [];
  [[0, 0], [w, 0], [w, h], [0, h]].forEach(([x, y], i) => {
    const [u, v] = pts[i];
    rows.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); rhs.push(u);
    rows.push([0, 0, 0, x, y, 1, -v * x, -v * y]); rhs.push(v);
  });
  for (let c = 0; c < 8; c++) { // Gaussian elimination with partial pivoting
    let p = c;
    for (let r = c + 1; r < 8; r++) if (Math.abs(rows[r][c]) > Math.abs(rows[p][c])) p = r;
    [rows[c], rows[p]] = [rows[p], rows[c]]; [rhs[c], rhs[p]] = [rhs[p], rhs[c]];
    for (let r = 0; r < 8; r++) {
      if (r === c) continue;
      const f = rows[r][c] / rows[c][c];
      for (let j = c; j < 8; j++) rows[r][j] -= f * rows[c][j];
      rhs[r] -= f * rhs[c];
    }
  }
  const [a, b, c, d, e, f, g, hh] = rhs.map((v, i) => v / rows[i][i]);
  return `matrix3d(${[a, d, 0, g, b, e, 0, hh, 0, 0, 1, 0, c, f, 0, 1].join(',')})`;
}

// The camera over a screen: keys of [time, { x, y, z, zoom, rx, ry }] (the point it looks at in
// the screen's pixels, a dolly, a zoom, and a tilt in degrees), eased from one to the next, with
// a slow handheld sway on top so the frame is never quite still.
function camAt(keys, lt, sway = 1) {
  let i = 0;
  while (i + 1 < keys.length && keys[i + 1][0] <= lt) i++;
  const [t0, a] = keys[i];
  const [t1, b] = keys[Math.min(i + 1, keys.length - 1)];
  const k = t1 > t0 ? inOut((lt - t0) / (t1 - t0)) : 0;
  const v = (n, d) => lerp(a[n] ?? d, b[n] ?? a[n] ?? d, k);
  return {
    x: v('x', W / 2) + 5 * sway * Math.sin(lt * 0.41), y: v('y', H / 2) + 4 * sway * Math.sin(lt * 0.33 + 1), z: v('z', 0),
    zoom: v('zoom', 1), rx: v('rx', 0) + 0.45 * sway * Math.sin(lt * 0.5), ry: v('ry', 0) + 0.6 * sway * Math.sin(lt * 0.37 + 2), blur: 0,
  };
}

// One screen shot's page: a dark backdrop with soft out-of-focus lights that drift with the
// camera, and a world (in the frame's own pixels) the camera moves over. frame(lt) sets the
// page for that moment and returns the camera; show() draws it, alone or handing over to the
// next shot (arrive and leave run 0 to 1), or mapped onto a monitor (matrix).
function uiScreen(seed, frame) {
  const root = document.createElement('div');
  root.className = 'ui-shot';
  root.style.perspective = `${Math.round(Math.max(W, H) * 1.05)}px`;
  const bokeh = document.createElement('div');
  bokeh.className = 'ui-bokeh';
  const r = rng(seed * 31 + 7);
  const dots = [];
  for (let i = 0; i < 18; i++) {
    const d = document.createElement('i');
    const size = Math.round(14 + r() * 46);
    d.style.width = d.style.height = `${size}px`;
    d.style.opacity = (0.04 + r() * 0.12).toFixed(2);
    if (r() > 0.72) d.className = 'a';
    bokeh.append(d);
    dots.push({ d, x: r() * W * 1.3 - W * 0.15, y: r() * H * 1.3 - H * 0.15, depth: 0.12 + r() * 0.4, ph: r() * 6.28 });
  }
  const world = document.createElement('div');
  world.className = 'ui-world';
  root.append(bokeh, world);
  uiLayer.append(root);
  const place = (cam, lt) => {
    world.style.transform = `translate3d(${W / 2}px, ${H / 2}px, ${cam.z.toFixed(1)}px) rotateX(${cam.rx.toFixed(3)}deg) rotateY(${cam.ry.toFixed(3)}deg) scale(${cam.zoom.toFixed(4)}) translate3d(${(-cam.x).toFixed(1)}px, ${(-cam.y).toFixed(1)}px, 0)`;
    for (const p of dots) {
      const x = p.x - (cam.x - W / 2) * p.depth * cam.zoom + 16 * Math.sin(lt * 0.23 + p.ph);
      const y = p.y - (cam.y - H / 2) * p.depth * cam.zoom + 12 * Math.cos(lt * 0.19 + p.ph);
      p.d.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0)`;
    }
  };
  return {
    root, world,
    hide() { root.style.visibility = 'hidden'; },
    show(lt, { arrive, leave, matrix, fade = 1 } = {}) {
      root.style.visibility = fade > 0 ? 'visible' : 'hidden';
      const cam = frame(lt);
      let opacity = fade;
      if (arrive !== undefined) { const e = out3(arrive); opacity = e; cam.zoom *= lerp(0.84, 1, e); cam.blur = Math.max(cam.blur, 9 * (1 - e)); }
      if (leave !== undefined) { const e = clamp(leave); opacity = 1 - e; cam.zoom *= 1 + 0.7 * e * e; cam.blur = Math.max(cam.blur, 12 * e); }
      root.style.opacity = opacity.toFixed(3);
      root.style.transform = matrix || '';
      root.style.filter = cam.blur > 0.4 ? `blur(${cam.blur.toFixed(1)}px)` : ''; // a fast camera smears, as a real shutter does
      place(cam, lt);
    },
  };
}

// A window with a title bar, in the world at x, y (its top left), w x h.
function uiWindow(world, { x, y, w, h, title = '', cls = '' }) {
  const win = document.createElement('div');
  win.className = `ui-win ${cls}`;
  Object.assign(win.style, { left: `${x}px`, top: `${y}px`, width: `${w}px`, height: `${h}px` });
  win.innerHTML = `<div class="ui-bar"><i></i><i></i><i></i><span>${escHtml(title)}</span></div><div class="ui-body"><div class="ui-scroll" style="font-size:${FS}px"></div></div>`;
  world.append(win);
  return { win, scroll: win.querySelector('.ui-scroll'), body: win.querySelector('.ui-body') };
}

// When each typed character and printed line appears: typing at about 26 characters a second, a
// beat after each command, output lines in quick succession, all sped up to fit [start, end].
function typeSchedule(lines, start, end) {
  const CPS = 26, ENTER = 0.32, LINE = 0.1;
  const need = lines.reduce((s, l) => s + (l.typed ? l.text.length / CPS + ENTER : l.wait || LINE), 0);
  const k = Math.min(1, Math.max(0.2, end - start) / Math.max(need, 1e-3));
  let t = start;
  return lines.map((l) => {
    const at = t;
    const dur = l.typed ? (l.text.length / CPS) * k : 0;
    t += l.typed ? dur + ENTER * k : (l.wait || LINE) * k;
    return { ...l, at, dur };
  });
}
const typedPart = (l, lt) => (!l.typed || l.dur <= 0 ? l.text : l.text.slice(0, Math.floor(clamp((lt - l.at) / l.dur) * l.text.length + 1e-6)));
const caretOn = (lt) => (lt * 1.9) % 1 < 0.6;

// Rows of text that appear on a schedule, typed or printed, scrolling up once they fill the
// window; returns the y (in the world) of the row being written at lt, for the camera to follow.
function uiRows(w, sched, render) {
  const rows = sched.map((l) => {
    const row = document.createElement('div');
    row.className = `ui-line ${l.cls || ''}`;
    row.innerHTML = render(l, l.text);
    w.scroll.append(row);
    return row;
  });
  const tops = rows.map((row) => row.offsetTop + row.offsetHeight / 2);
  const bottoms = rows.map((row) => row.offsetTop + row.offsetHeight);
  const view = w.body.offsetHeight - 30;
  const winTop = parseFloat(w.win.style.top) + 46;
  const caret = '<span class="ui-caret"></span>';
  return (lt) => {
    let cur = -1;
    sched.forEach((l, i) => {
      const on = lt >= l.at || (i === 0 && l.typed); // the prompt waits, caret blinking, before the typing starts
      rows[i].style.visibility = on ? 'inherit' : 'hidden'; // not 'visible', so a hidden screen hides all of it
      if (on) cur = i;
      if (l.typed) rows[i].innerHTML = render(l, typedPart(l, lt)) + (on && (lt < l.at + l.dur + 0.3 || i === sched.length - 1) && caretOn(lt) ? caret : '');
    });
    // a step that is still running pulses, then settles once the next line is in
    sched.forEach((l, i) => { if (l.cls === 'step') rows[i].querySelector('.dot').style.opacity = i === cur && i < sched.length - 1 ? (0.35 + 0.65 * Math.abs(Math.sin(lt * 5))).toFixed(2) : '1'; });
    const scroll = cur < 0 ? 0 : Math.max(0, bottoms[cur] - view);
    w.scroll.style.transform = `translateY(${-scroll}px)`;
    const y = (i) => winTop + tops[Math.max(0, i)] - scroll;
    // ease from one row to the next as it appears, so the camera glides instead of stepping
    if (cur < 0) return y(0);
    const next = sched[cur + 1];
    if (!next) return y(cur);
    const k = inOut((lt - sched[cur].at) / Math.max(0.05, next.at - sched[cur].at));
    return lerp(y(cur), winTop + tops[cur + 1] - Math.max(0, bottoms[cur + 1] - view), k * 0.35);
  };
}

const prevOf = (shot) => timeline[timeline.indexOf(shot) - 1];
const intoFromDesk = (shot) => { const p = prevOf(shot); return !!p && p.type === 'desk'; };

// the screens' fonts, loaded before anything is measured, so text wraps the same in every frame
const uiFonts = () => Promise.all([`500 ${FS}px "JetBrains Mono"`, '500 25px Inter', '800 25px Inter', '700 100px Caveat'].map((f) => document.fonts.load(f).catch(() => null)));

// ---- terminal: the product's real commands, typed
SHOTS.terminal = async (el, shot) => {
  await uiFonts();
  const lines = listOf(el.dataset.lines || `$ ${el.dataset.cmd || 'npx your-product'}`)
    .map((s) => (s.startsWith('$ ') ? { typed: true, text: s.slice(2), cls: 'cmd' } : { typed: false, text: s, cls: /^[✔✓]/.test(s) ? 'ok' : s.startsWith('⎿') ? 'res' : '' }));
  const D = shot.dur;
  const sched = typeSchedule(lines, shot.first || intoFromDesk(shot) ? 0.2 : 0.45, D * 0.78);
  const [ww, wh] = WIDE ? [1340, 740] : [960, 1160];
  const [wx, wy] = [(W - ww) / 2, (H - wh) / 2 - (WIDE ? 30 : LIFT * 0.7)];
  let follow;
  const flat = intoFromDesk(shot);
  const scr = uiScreen(3 + timeline.indexOf(shot), (lt) => {
    const fy = follow(lt);
    const k = out3(lt / Math.max(0.5, D * 0.7));
    const start = flat ? { x: W / 2, y: H / 2, zoom: 1, rx: 0, ry: 0 } : { x: W / 2, y: H / 2, zoom: 0.94, rx: 4, ry: -7 };
    const c = camAt([[0, start], [D, { x: wx + ww * 0.42, y: H / 2, zoom: WIDE ? 1.34 : 1.24, rx: -1.5, ry: 3.5 }]], lt, flat ? clamp(lt) : 1);
    c.y = lerp(start.y, fy, 0.75 * k);
    return c;
  });
  const w = uiWindow(scr.world, { x: wx, y: wy, w: ww, h: wh, title: el.dataset.title || 'Terminal', cls: 'ui-term' });
  follow = uiRows(w, sched, (l, text) => escHtml(text));
  const typed = sched.find((l) => l.typed);
  return { screen: scr, show: scr.show, tone: 'dark', events: { type: typed ? typed.at : 0.4, done: sched[sched.length - 1].at } };
};

// ---- agent: an AI agent's session, the prompt typed, its steps streaming, the document it wrote
SHOTS.agent = async (el, shot) => {
  await uiFonts();
  const D = shot.dur;
  const doc = listOf(el.dataset.doc);
  const steps = listOf(el.dataset.steps);
  const lines = [
    ...(el.dataset.ask ? [{ typed: true, text: el.dataset.ask, cls: 'ask' }] : []),
    ...steps.map((s, i) => (s.startsWith('⎿') ? { text: s, cls: 'res', wait: 0.22 } : { text: s, cls: 'step', wait: i === 0 ? 0.55 : 0.5 })),
    ...(el.dataset.done ? [{ text: el.dataset.done, cls: 'done', wait: 0.45 }] : []),
  ];
  if (!lines.length) lines.push({ text: '', wait: 0.1 });
  const sched = typeSchedule(lines, shot.first ? 0.2 : 0.4, D * (doc.length ? 0.55 : 0.8));
  const side = doc.length > 0;
  const [ww, wh] = WIDE ? [side ? 1180 : 1340, 760] : [960, side ? 980 : 1160];
  const wx = WIDE ? (side ? 150 : (W - ww) / 2) : (W - ww) / 2;
  const wy = WIDE ? (H - wh) / 2 - 30 : (side ? 230 : (H - wh) / 2 - LIFT * 0.7);
  // the document stops short of the subtitles once the camera has panned over to it
  const [dw, dh] = WIDE ? [680, 600] : [860, 760];
  const [dx, dy] = WIDE ? [W - 130 - dw, (H - dh) / 2 - 70] : [(W - dw) / 2, wy + wh - 260];
  const docAt = side ? sched[sched.length - 1].at + 0.15 : D;
  const flat = intoFromDesk(shot);
  let follow, docEl, docRows;
  const scr = uiScreen(5 + timeline.indexOf(shot), (lt) => {
    const fy = follow(lt);
    const k = out3(lt / Math.max(0.5, docAt));
    const start = flat ? { x: W / 2, y: H / 2, zoom: 1, rx: 0, ry: 0 } : { x: wx + ww / 2, y: H / 2, zoom: 0.95, rx: 4, ry: -6 };
    const c = camAt([[0, start], [docAt, { x: wx + ww * 0.45, zoom: WIDE ? 1.3 : 1.2, rx: -1, ry: 3 }]], lt, flat ? clamp(lt) : 1);
    c.y = lerp(start.y, fy, 0.75 * k);
    if (side) {
      // the document slides in from the side, writing itself, and the camera pans over to it
      const s = clamp((lt - docAt) / 0.7);
      const e = out3(s);
      docEl.style.opacity = s > 0 ? '1' : '0';
      docEl.style.transform = WIDE
        ? `translate3d(${lerp(260, 0, e)}px, 0, ${lerp(-200, 60, e)}px) rotateY(${lerp(-24, -5, e)}deg)`
        : `translate3d(0, ${lerp(320, 0, e)}px, ${lerp(-200, 60, e)}px) rotateX(${lerp(18, 3, e)}deg)`;
      const n = Math.max(1, Math.ceil(clamp((lt - docAt - 0.2) / Math.max(0.4, (D - docAt) * 0.55)) * docRows.length));
      docRows.forEach((row, i) => { row.style.visibility = i < n ? 'inherit' : 'hidden'; });
      const pan = inOut((lt - docAt) / Math.max(0.6, (D - docAt) * 0.8));
      c.x = lerp(c.x, dx + dw / 2, pan);
      c.y = lerp(c.y, dy + dh * (WIDE ? 0.5 : 0.45), pan);
      c.zoom = lerp(c.zoom, WIDE ? 1.1 : 1.04, pan);
      c.ry = lerp(c.ry, -3, pan);
    }
    return c;
  });
  const w = uiWindow(scr.world, { x: wx, y: wy, w: ww, h: wh, title: el.dataset.title || (el.dataset.app || 'Claude Code').toLowerCase(), cls: 'ui-term ui-agent' });
  w.scroll.innerHTML = `<div class="ui-welcome"><b>✻</b> ${escHtml(el.dataset.app || 'Claude Code')}<span>${escHtml(el.dataset.cwd || '~/marketing')}</span></div>`;
  const tool = (text) => { const m = /^([^()]{1,40})\((.*)\)$/.exec(text); return m ? `<b>${escHtml(m[1])}</b>(${escHtml(m[2])})` : escHtml(text); };
  follow = uiRows(w, sched, (l, text) => (l.cls === 'step' ? `<span class="dot">●</span> ${tool(text)}` : l.cls === 'res' ? escHtml(text.replace(/^⎿\s*/, '⎿  ')) : escHtml(text)));
  if (side) {
    docEl = document.createElement('div');
    docEl.className = 'ui-doc';
    Object.assign(docEl.style, { left: `${dx}px`, top: `${dy}px`, width: `${dw}px`, height: `${dh}px` });
    docEl.innerHTML = doc.map((d) => (d.startsWith('# ') ? `<div class="h">${escHtml(d.slice(2))}</div>` : d.startsWith('- ') ? `<div class="p li">${escHtml(d.slice(2))}</div>`
      : d.startsWith('## ') ? `<div class="p sub">${escHtml(d.slice(3))}</div>` : `<div class="p">${escHtml(d)}</div>`)).join('');
    scr.world.append(docEl);
    docRows = [...docEl.children];
  }
  const typed = sched.find((l) => l.typed);
  return { screen: scr, show: scr.show, tone: 'dark', events: { type: typed ? typed.at : 0.4, done: side ? docAt : sched[sched.length - 1].at } };
};

// ---- wall: the real things it made, floating in the dark, the camera flying through them
SHOTS.wall = async (el, shot) => {
  await uiFonts();
  const D = shot.dur;
  const items = listOf(el.dataset.items, ',').slice(0, 24);
  const labels = listOf(el.dataset.labels, ',');
  const r = rng(11);
  let cards = [];
  const flat = intoFromDesk(shot);
  const POP = Math.min(1.1, D * 0.3) / Math.max(1, items.length);
  const scr = uiScreen(7 + timeline.indexOf(shot), (lt) => {
    const c = camAt([[0, { x: W / 2, y: H / 2, z: 120, rx: 5, ry: -9 }], [D, { x: W / 2, y: H / 2 - 30, z: 760, rx: -3, ry: 9 }]], lt, 0.6);
    for (const cd of cards) {
      const s = flat ? 1 : clamp((lt - cd.at) / 0.4);
      const near = cd.z + c.z; // how close the card has come to the lens; it fades before it gets soft
      const fade = clamp((900 - near) / 300);
      cd.el.style.opacity = (out3(s) * fade).toFixed(3);
      cd.el.style.transform = `translate3d(${cd.x - cd.w / 2}px, ${cd.y - cd.h / 2}px, ${cd.z}px) rotateY(${cd.ry}deg) rotateZ(${cd.rz}deg) scale(${lerp(0.6, 1, back(s)).toFixed(3)})`;
    }
    return c;
  });
  const n = items.length;
  const cardH = WIDE ? 430 : 470;
  cards = await Promise.all(items.map(async (src, i) => {
    const card = document.createElement('div');
    card.className = 'ui-card';
    const img = document.createElement('img');
    img.src = src;
    img.alt = '';
    card.append(img);
    if (labels[i]) { const s = document.createElement('span'); s.textContent = labels[i]; card.append(s); }
    scr.world.append(card);
    try { await img.decode(); } catch { /* render.js reports images that don't load */ }
    const aspect = img.naturalWidth && img.naturalHeight ? img.naturalWidth / img.naturalHeight : 9 / 16;
    const h = cardH * (0.85 + r() * 0.3), w = h * aspect;
    Object.assign(card.style, { width: `${w}px`, height: `${h}px` });
    // a golden-angle spiral, so the cards spread evenly round the middle, nearer ones further out
    const a = i * 2.39996, rad = Math.sqrt((i + 0.6) / n);
    return {
      el: card, w, h, at: 0.1 + i * POP,
      x: W / 2 + Math.cos(a) * rad * W * (WIDE ? 0.58 : 0.7), y: H / 2 - 40 + Math.sin(a) * rad * H * (WIDE ? 0.55 : 0.45),
      z: -1500 + (i / n) * 1400 + r() * 150, ry: (r() - 0.5) * 24, rz: (r() - 0.5) * 8,
    };
  }));
  return { screen: scr, show: scr.show, tone: 'dark', events: { done: 0.1 + (n - 1) * POP + 0.3 } };
};

// ---- player: the user's real video (or picture) playing in a window, the scrubber moving
SHOTS.player = async (el, shot) => {
  await uiFonts();
  const D = shot.dur;
  const src = el.dataset.src || '';
  const video = /\.(mp4|mov|webm|m4v)$/i.test(src);
  const PLAY = shot.first ? 0 : 0.35;
  let aspect = WIDE ? 16 / 9 : 9 / 16;
  const flat = intoFromDesk(shot);
  let media, fill, knob;
  const box = {};
  const scr = uiScreen(9 + timeline.indexOf(shot), (lt) => {
    const p = clamp((lt - PLAY) / Math.max(1, D - PLAY));
    fill.style.width = `${(p * 100).toFixed(2)}%`;
    knob.style.left = `${(p * 100).toFixed(2)}%`;
    const start = flat ? { x: W / 2, y: H / 2, zoom: 1, rx: 0, ry: 0 } : { x: W / 2, y: H / 2, zoom: 0.92, rx: 5, ry: 8 };
    return camAt([[0, start], [D, { x: W / 2, y: box.cy, zoom: 1.12, rx: -1, ry: -4 }]], lt, flat ? clamp(lt) : 1);
  });
  if (src && !video) {
    const img = new Image();
    img.src = src;
    try { await img.decode(); aspect = img.naturalWidth / img.naturalHeight; } catch { /* reported by render.js */ }
    media = img;
  } else if (video) {
    media = document.createElement('video');
    media.src = src;
    media.muted = true;
    if (el.dataset.aspect) aspect = Number(el.dataset.aspect.split(/[:/x]/)[0]) / Number(el.dataset.aspect.split(/[:/x]/)[1]) || aspect;
    // render.js turns the clip into frames and plays them from --in, data-offset seconds in
    media.style.setProperty('--in', `${(shot.in + PLAY).toFixed(2)}s`);
    if (el.dataset.offset) media.dataset.offset = el.dataset.offset;
  }
  // the window fits the picture: up to 72% of the frame's height (and 80% of its width)
  const maxH = H * (WIDE ? 0.62 : 0.56), maxW = W * (WIDE ? 0.7 : 0.86);
  const mh = Math.min(maxH, maxW / aspect), mw = mh * aspect;
  const [ww, wh] = [mw, mh + 46 + 58];
  const [wx, wy] = [(W - ww) / 2, (H - wh) / 2 - (WIDE ? 60 : LIFT * 0.6)];
  box.cy = wy + wh / 2 + (WIDE ? 40 : 0); // the camera sits a little low, so the window clears the subtitles
  const w = uiWindow(scr.world, { x: wx, y: wy, w: ww, h: wh, title: el.dataset.title || src.split('/').pop() || 'video.mp4', cls: 'ui-player' });
  w.body.innerHTML = '<div class="ui-scrub"><b></b><i></i></div>';
  if (media) {
    media.className = 'ui-media';
    media.style.height = `${mh}px`;
    w.body.prepend(media);
  }
  fill = w.body.querySelector('.ui-scrub b');
  knob = w.body.querySelector('.ui-scrub i');
  return { screen: scr, show: scr.show, tone: 'dark', events: { play: PLAY } };
};

// ---- comments: the ending, a handwritten question over an empty comment box being typed in
SHOTS.comments = async (el, shot) => {
  await uiFonts();
  const D = shot.dur;
  const ask = el.dataset.ask || '';
  const [bw, bh] = WIDE ? [1040, 250] : [940, 270];
  const [bx, by] = [(W - bw) / 2, H / 2 - (WIDE ? 20 : LIFT * 0.3)];
  const T = 0.9; // the typing starts once the question is written
  const sched = typeSchedule([{ typed: true, text: ask }], T, D * 0.8)[0];
  let hand, input;
  const scr = uiScreen(13, (lt) => {
    const w = clamp((lt - 0.1) / 0.8);
    hand.style.clipPath = `inset(-20% ${((1 - inOut(w)) * 100).toFixed(1)}% -20% 0)`;
    input.innerHTML = ask && lt >= T ? escHtml(typedPart(sched, lt)) + (caretOn(lt) ? '<span class="ui-caret"></span>' : '') : '<span class="ph">Add a comment…</span>';
    return camAt([[0, { x: W / 2, y: H / 2, zoom: 0.96, rx: 3, ry: -4 }], [D, { x: W / 2, y: H / 2 + 10, zoom: 1.1, rx: -1, ry: 3 }]], lt);
  });
  hand = document.createElement('div');
  hand.className = 'ui-hand';
  hand.textContent = el.dataset.text || 'What should I make next?';
  hand.style.top = `${by - (WIDE ? 190 : 230)}px`;
  hand.style.width = `${W}px`;
  hand.style.fontSize = `${WIDE ? 120 : 112}px`;
  const box = document.createElement('div');
  box.className = 'ui-box';
  Object.assign(box.style, { left: `${bx}px`, top: `${by}px`, width: `${bw}px`, minHeight: `${bh}px` });
  box.innerHTML = '<div class="top"><span>Comments</span><span class="ph">Top</span></div><div class="row"><div class="av"></div><div class="in"></div><div class="post">Post</div></div>';
  scr.world.append(hand, box);
  input = box.querySelector('.in');
  return { screen: scr, show: scr.show, tone: 'dark', events: { type: T } };
};
"""
