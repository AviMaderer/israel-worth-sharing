"""Build one weekly edition of Israel Worth Sharing.

Stories are gathered every day into the NEXT Sunday's edition; on its Sunday the edition is released
(the main link and the archive switch to it). Until then its page is an unlinked preview.

Usage:  python tools/build.py data/weeks/YYYY-MM-DD.json      (YYYY-MM-DD = the Sunday that starts the week)

Reads   data/config.json, data/dedications.csv, the week file
Writes  YYYY-MM-DD/index.html          the week's page (all stories; each visitor gets their own shuffled picks)
        YYYY-MM-DD/img/<key>.png       our branded image per story (fallback + upload option; only new ones are drawn)
        index.html                     redirects to the latest week
        archive/index.html             list of all weeks
        data/whatsapp/YYYY-MM-DD.txt   ready-to-paste weekly WhatsApp message
        data/stories-log.csv           appends new stories (no duplicates)
        assets/og-card.png, assets/icon.png   (only if missing)
Needs   Python 3 + Playwright with Chromium (for the images).
"""
import asyncio, base64, csv, datetime as dt, html, json, pathlib, sys
from zoneinfo import ZoneInfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
E = html.escape
BLUE, GOLD, INK = "#0038B8", "#E8B04B", "#1C2333"
def today_il():
    import os
    if os.environ.get("IWS_TODAY"):  # for testing only
        return dt.date.fromisoformat(os.environ["IWS_TODAY"])
    return dt.datetime.now(ZoneInfo("Asia/Jerusalem")).date()

HEBREW_NOTE = "(Source article in Hebrew; your browser can translate it.)"

# ---------- inputs ----------
def load(week_file):
    cfg = json.loads((ROOT / "data/config.json").read_text(encoding="utf-8"))
    wk = json.loads(pathlib.Path(week_file).read_text(encoding="utf-8"))
    sunday = dt.date.fromisoformat(wk["week"])
    assert sunday.weekday() == 6, "week must be the date of a Sunday"
    ded = find_dedication(sunday)
    assert wk["stories"], "the week has no stories"
    keys = set()
    for s in wk["stories"]:
        for k in ("key", "added", "tag", "teaser", "headline", "why", "texts", "source", "source_name"):
            assert s.get(k), f"story '{s.get('key')}' is missing '{k}'"
        assert s["key"] not in keys, f"duplicate key {s['key']}"
        keys.add(s["key"])
        out = []
        for t in s["texts"]:
            t = t.rstrip()
            if cfg["hashtag"] not in t:
                lines = t.split("\n")
                if lines[-1].startswith("#"):
                    lines[-1] += " " + cfg["hashtag"]
                else:
                    lines += ["", cfg["hashtag"]]
                t = "\n".join(lines)
            if s.get("source_lang") == "he" and HEBREW_NOTE not in t:
                t += "\n\n" + HEBREW_NOTE
            out.append(t)
        s["texts"] = out
    return cfg, wk, ded

def find_dedication(sunday):
    """Dedication text for the week starting on `sunday`, or "".

    data/dedications.csv columns: start_date,end_date,text (YYYY-MM-DD; an older
    single `date` column also works). Dates are inclusive; end_date may be empty
    for a single day. A row applies to the week if its period overlaps Sunday-Saturday.
    If several rows apply, the shortest period wins; ties go to the later row.
    """
    week_end = sunday + dt.timedelta(days=6)
    best, best_len = "", None
    with open(ROOT / "data/dedications.csv", encoding="utf-8") as f:
        for n, row in enumerate(csv.DictReader(f), start=2):
            text = (row.get("text") or "").strip()
            start = (row.get("start_date") or row.get("date") or "").strip()
            end = (row.get("end_date") or "").strip() or start
            if not text or not start:
                continue
            try:
                a, b = dt.date.fromisoformat(start), dt.date.fromisoformat(end)
            except ValueError:
                sys.exit(f"dedications.csv line {n}: dates must be YYYY-MM-DD (got '{start}', '{end}')")
            if b < a:
                sys.exit(f"dedications.csv line {n}: end_date {end} is before start_date {start}")
            if a <= week_end and b >= sunday and (best_len is None or (b - a).days <= best_len):
                best, best_len = text, (b - a).days
    return best

def nice(d):
    d = dt.date.fromisoformat(d) if isinstance(d, str) else d
    return f"{d.day} {d.strftime('%B %Y')}"

# ---------- brand pieces ----------
def mark(size, bg=GOLD, fg=INK):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 48 48" aria-hidden="true">'
            f'<rect width="48" height="48" rx="12" fill="{bg}"/>'
            f'<path d="M16 24 L32 15 M16 24 L32 33" stroke="{fg}" stroke-width="3.5" stroke-linecap="round"/>'
            f'<circle cx="15" cy="24" r="5.5" fill="{fg}"/><circle cx="33" cy="14.5" r="5.5" fill="{fg}"/>'
            f'<circle cx="33" cy="33.5" r="5.5" fill="{fg}"/></svg>')

def font_css(prefix, embed=False):
    def src(file):
        if embed:
            return "data:font/woff2;base64," + base64.b64encode((ROOT / "assets/fonts" / file).read_bytes()).decode()
        return f"{prefix}assets/fonts/{file}"
    f = lambda fam, w, file: (f"@font-face{{font-family:'{fam}';font-weight:{w};font-display:swap;"
                              f"src:url({src(file)}) format('woff2')}}")
    return "\n".join([f("Rubik", 500, "rubik-latin-500-normal.woff2"), f("Rubik", 700, "rubik-latin-700-normal.woff2"),
                      f("Assistant", 400, "assistant-latin-400-normal.woff2"), f("Assistant", 700, "assistant-latin-700-normal.woff2")])

# ---------- images (Playwright) ----------
BG = (f"background:{BLUE};background-image:radial-gradient(rgba(255,255,255,.10) 2.5px, transparent 2.5px);"
      "background-size:44px 44px")

def card_html(cfg, s):
    return f'''<html><head><style>{font_css("", embed=True)}
body{{margin:0;width:1080px;height:1080px;overflow:hidden;font-family:Rubik}}
.c{{width:1080px;height:1080px;box-sizing:border-box;padding:84px;display:flex;flex-direction:column;{BG}}}
.b{{display:flex;align-items:center;gap:18px;font:500 30px/1 Rubik;letter-spacing:.12em;color:{GOLD}}}
.t{{margin-top:auto;font:500 30px/1 Rubik;letter-spacing:.1em;text-transform:uppercase;color:#C9D6F5}}
h1{{margin:22px 0 0;font:700 86px/1.06 Rubik;color:#fff;letter-spacing:-.015em;text-wrap:balance}}
.r{{margin-top:44px;height:8px;width:140px;background:{GOLD};border-radius:4px}}
</style></head><body><div class="c"><div class="b">{mark(56)}{E(cfg["site_name"]).upper()}</div>
<div class="t">{E(s["tag"])}</div><h1>{E(s["headline"])}</h1><div class="r"></div></div></body></html>'''

def og_html(cfg):
    return f'''<html><head><style>{font_css("", embed=True)}
body{{margin:0;width:1200px;height:630px;overflow:hidden}}
.c{{width:1200px;height:630px;box-sizing:border-box;padding:90px;display:flex;flex-direction:column;justify-content:center;gap:28px;{BG}}}
h1{{margin:0;font:700 96px/1 Rubik;color:#fff;letter-spacing:-.02em}} p{{margin:0;font:500 40px/1.2 Rubik;color:{GOLD}}}
</style></head><body><div class="c">{mark(110)}<h1>{E(cfg["site_name"])}</h1><p>{E(cfg["tagline"])}</p></div></body></html>'''

async def render(jobs):
    if not jobs:
        return
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for html_src, path, w, h in jobs:
            pg = await b.new_page(viewport={"width": w, "height": h})
            await pg.set_content(html_src); await pg.wait_for_timeout(300)
            path.parent.mkdir(parents=True, exist_ok=True)
            await pg.screenshot(path=str(path)); await pg.close()
        await b.close()

# ---------- page ----------
PAGE_CSS = """
:root{--blue:#0038B8;--gold:#E8B04B;--sand:#F3ECE0;--paper:#FFFDF9;--ink:#1C2333;--muted:#5B6275;--line:#E3D9C8;--btn-fg:#FFFFFF;--soft:#EAF0FB;--new:#1E7A4C;
 --f-display:'Rubik','Segoe UI',system-ui,sans-serif;--f-body:'Assistant','Segoe UI',system-ui,sans-serif;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--blue:#7EA2FF;--gold:#F0BE62;--sand:#10162A;--paper:#182038;--ink:#ECEFF7;--muted:#A6AEC4;--line:#2A3452;--btn-fg:#0B1124;--soft:#1F2A4A;--new:#6FD3A0;color-scheme:dark}}
:root[data-theme="dark"]{--blue:#7EA2FF;--gold:#F0BE62;--sand:#10162A;--paper:#182038;--ink:#ECEFF7;--muted:#A6AEC4;--line:#2A3452;--btn-fg:#0B1124;--soft:#1F2A4A;--new:#6FD3A0;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--sand);color:var(--ink);font:400 18px/1.5 var(--f-body);padding-inline:16px;padding-block:max(20px,env(safe-area-inset-top)) 48px}
.wrap{max-width:560px;margin:0 auto;display:grid;gap:22px}
header{display:grid;gap:6px;padding-top:8px}
.brand{display:flex;align-items:center;gap:10px;font:500 14px/1 var(--f-display);letter-spacing:.14em;color:var(--blue);text-transform:uppercase;text-decoration:none}
header h1{margin:6px 0 0;font:700 clamp(30px,8vw,40px)/1.05 var(--f-display);letter-spacing:-.015em;text-wrap:balance}
.date{margin:0;color:var(--muted);font-size:16px}
.howto{margin:4px 0 0;color:var(--muted);font-size:16px}
.ded{margin:6px 0 0;padding:12px 16px;border-radius:10px;background:var(--paper);border:1px solid var(--line);font-size:17px;text-align:center;line-height:1.45}
.ded b{font-family:var(--f-display);font-weight:500}
.ded .name{display:block;font-family:var(--f-display);font-weight:700}
.howto-h{margin:14px 0 0;font:500 13px/1 var(--f-display);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.steps{margin:6px 0 0;padding-left:22px;color:var(--ink);font-size:17px}
.steps li{margin:3px 0}
.heads{margin:10px 0 0;border:1px solid var(--line);border-radius:10px;background:var(--paper);padding:0 16px}
.heads summary{cursor:pointer;padding:12px 0;font:500 15px/1.2 var(--f-display);color:var(--blue)}
.heads ul{margin:0 0 14px;padding-left:20px;display:grid;gap:6px;font-size:16px}
.heads a{color:var(--ink)}
.sec{margin:8px 0 0;font:500 13px/1 var(--f-display);letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.list{display:grid;gap:14px}
.story{background:var(--paper);border:1px solid var(--line);border-radius:14px;overflow:hidden}
.story>summary{list-style:none;cursor:pointer;padding:16px 18px;display:grid;gap:6px}
.story>summary::-webkit-details-marker{display:none}
.story[open]>summary{padding-bottom:4px}
.top{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font:500 12px/1 var(--f-display);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.badge{padding:4px 7px;border-radius:999px;letter-spacing:.04em}
.badge.new{color:var(--new);border:1px solid currentColor}
.preview-note{margin:0;padding:10px 14px;border-radius:10px;background:var(--gold);color:#1C2333;font:500 15px/1.35 var(--f-display)}
.badge.done{color:var(--muted);border:1px solid var(--line)}
.story h2{margin:0;font:700 21px/1.2 var(--f-display);letter-spacing:-.01em;text-wrap:balance}
.why{margin:0;color:var(--muted);font-size:16px}
.more-cue{font:500 14px/1 var(--f-display);color:var(--blue)}
.story[open] .more-cue{display:none}
.body{padding:8px 18px 20px;display:grid;gap:12px;min-width:0}
.preview{display:block;text-decoration:none;color:inherit;background:var(--soft);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.og{display:block;width:100%;max-width:100%;aspect-ratio:1.91;object-fit:cover;background:var(--line)}
.pmeta{display:grid;gap:4px;padding:10px 14px 12px}
.site{font:500 12px/1 var(--f-display);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.ogt{font:500 15px/1.3 var(--f-display);color:var(--ink)}
.lbl{margin-top:4px;font:500 14px/1 var(--f-display);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.swap{border:0;background:var(--soft);color:var(--blue);font:500 14px/1 var(--f-display);padding:9px 12px;border-radius:999px;cursor:pointer}
.tip{margin:0;font-size:15px;color:var(--muted)}
.post{width:100%;resize:vertical;font:400 17px/1.5 var(--f-body);color:var(--ink);background:var(--sand);border:1px solid var(--line);border-radius:10px;padding:12px 14px;min-height:240px}
.post:focus-visible,.btn:focus-visible,.net:focus-visible,.swap:focus-visible,summary:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.actions{display:flex;flex-wrap:wrap;gap:8px}
.btn{flex:1 1 auto;border:1px solid var(--blue);background:transparent;color:var(--blue);border-radius:10px;padding:12px 14px;font:500 15px/1 var(--f-display);cursor:pointer;min-height:46px}
.btn.primary{background:var(--blue);color:var(--btn-fg);flex-basis:100%}
.nets{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:6px}
.net{text-align:center;text-decoration:none;color:var(--ink);background:var(--soft);border-radius:8px;padding:10px 4px;font:500 13px/1.1 var(--f-display)}
.hint{margin:0;min-height:1.2em;font-size:15px;color:var(--blue)}
.ours{border:1px solid var(--line);border-radius:10px;padding:0 14px}
.ours summary{cursor:pointer;padding:12px 0;font:500 15px/1.2 var(--f-display);color:var(--blue)}
.ours[open]{padding-bottom:14px;display:grid;gap:10px}
.ours p{margin:0;font-size:15px;color:var(--muted)}
.art{display:block;width:100%;height:auto;aspect-ratio:1;max-width:100%;border-radius:8px}
.src{margin:0;font-size:15px;color:var(--muted);border-top:1px solid var(--line);padding-top:12px}
.src a{color:var(--ink)}
.lang{font:500 12px/1 var(--f-display);padding:3px 6px;border-radius:6px;background:var(--soft);color:var(--blue);margin-left:4px}
footer{display:grid;gap:10px;color:var(--muted);font-size:15px}
footer a{color:var(--ink)}
"""

PAGE_JS = r"""
const enc = encodeURIComponent;
const store = { get(){ try { return new Set(JSON.parse(localStorage.getItem('iws-shared') || '[]')); } catch { return new Set(); } },
                add(k){ try { const s = this.get(); s.add(k); localStorage.setItem('iws-shared', JSON.stringify([...s])); } catch {} } };
const shared = store.get();
const rand = a => a.map(v => [Math.random(), v]).sort((x, y) => x[0] - y[0]).map(x => x[1]);
const opOrder = rand(OPENERS.map((_, i) => i));
// Each visitor gets their own order: unshared stories first, shared ones last.
const cards = [...document.querySelectorAll('.story')];
const score = c => Math.random() - (shared.has(c.dataset.key) ? 10 : 0);
const order = cards.map(c => [score(c), c]).sort((a, b) => b[0] - a[0]).map(x => x[1]);
const picks = document.getElementById('picks'), more = document.getElementById('more');
order.forEach((c, i) => { (i < 3 ? picks : more).appendChild(c); if (i < 3) c.open = true; });
if (!more.children.length) document.getElementById('more-h').hidden = true;
document.querySelectorAll('.jump').forEach(a => a.addEventListener('click', e => {
  const c = document.getElementById(a.getAttribute('href').slice(1)); if (!c) return;
  e.preventDefault(); c.open = true; c.scrollIntoView({ behavior: 'smooth', block: 'start' });
}));

order.forEach((card, idx) => {
  const key = card.dataset.key, m = META[key];
  const img = card.querySelector('.art'), ta = card.querySelector('.post'), hint = card.querySelector('.hint');
  const og = card.querySelector('.og');
  const say = t => { hint.textContent = t; clearTimeout(card._t); card._t = setTimeout(() => hint.textContent = '', 4500); };
  const fallback = () => { og.onerror = null; og.src = og.dataset.fallback; og.style.aspectRatio = '1'; };
  if (!og.getAttribute('src')) fallback(); else { og.onerror = fallback; if (og.complete && og.naturalWidth === 0) fallback(); }
  if (shared.has(key)) card.querySelector('.top').insertAdjacentHTML('beforeend', '<span class="badge done">Shared</span>');
  const markShared = () => { if (!shared.has(key)) { shared.add(key); store.add(key); card.querySelector('.top').insertAdjacentHTML('beforeend', '<span class="badge done">Shared</span>'); } };
  let oi = idx, vi = Math.floor(Math.random() * m.texts.length);
  const opener = () => OPENERS[opOrder[oi % OPENERS.length]];
  const compose = () => opener() + '\n\n' + m.texts[vi % m.texts.length];
  let last = compose(); ta.value = last;
  const links = () => {
    const t = ta.value.trim();
    card.querySelector('.wa').href = 'https://wa.me/?text=' + enc(t + '\n\n' + m.source);
    card.querySelector('.x').href = 'https://twitter.com/intent/tweet?text=' + enc(m.headline) + '&url=' + enc(m.source);
    card.querySelector('.fb').href = 'https://www.facebook.com/sharer/sharer.php?u=' + enc(m.source);
    card.querySelector('.li').href = 'https://www.linkedin.com/sharing/share-offsite/?url=' + enc(m.source);
  };
  card.querySelector('.swap').addEventListener('click', () => {
    const oldOpener = opener(); oi += 1; vi += 1;
    if (ta.value === last) { last = compose(); ta.value = last; say('New wording. Edit it any way you like.'); }
    else if (ta.value.startsWith(oldOpener)) { ta.value = opener() + ta.value.slice(oldOpener.length); say('You edited the text, so only the opening line changed.'); }
    else { ta.value = opener() + '\n\n' + ta.value; say('Added a new opening line above your text.'); }
    links();
  });
  links(); ta.addEventListener('input', links);
  const file = async () => new File([await (await fetch(img.src)).blob()], `israel-worth-sharing-${key}.png`, { type: 'image/png' });
  const copy = async () => {
    try { await navigator.clipboard.writeText(ta.value); return true; }
    catch { ta.select(); try { return document.execCommand('copy'); } catch { return false; } }
  };
  card.querySelector('.copy').addEventListener('click', async () => { markShared(); say(await copy() ? 'Copied. Paste it into your post.' : 'Text selected. Press Copy on your keyboard.'); });
  card.querySelector('.wa').addEventListener('click', markShared);
  card.querySelector('.x').addEventListener('click', markShared);
  card.querySelector('.fb').addEventListener('click', () => { markShared(); copy().then(ok => ok && say('Text copied. Paste it into your Facebook post.')); });
  card.querySelector('.li').addEventListener('click', () => { markShared(); copy().then(ok => ok && say('Text copied. Paste it into your LinkedIn post.')); });
  card.querySelector('.share').addEventListener('click', async () => {
    markShared();
    try { if (navigator.share) { await navigator.share({ text: ta.value.trim(), url: m.source }); return; } }
    catch (e) { if (e && e.name === 'AbortError') return; }
    await copy(); say('Text copied. Use a button below to post, then paste.');
  });
  card.querySelector('.dl').addEventListener('click', async () => {
    markShared();
    const f = await file(), a = document.createElement('a');
    a.href = URL.createObjectURL(f); a.download = f.name; document.body.appendChild(a); a.click(); a.remove();
    say('Image saved. On a phone you can also press and hold the image.');
  });
  card.querySelector('.share-img').addEventListener('click', async () => {
    markShared();
    const text = ta.value.trim() + '\n\n' + m.source;
    try {
      const f = await file();
      if (navigator.canShare && navigator.canShare({ files: [f] })) { await navigator.share({ files: [f], text }); return; }
      if (navigator.share) { await navigator.share({ text }); return; }
    } catch (e) { if (e && e.name === 'AbortError') return; }
    await copy(); say('Sharing works on phones. Text copied: download the image and paste the text.');
  });
});
"""

def story_html(s):
    k = E(s["key"])
    he = s.get("source_lang") == "he"
    return f'''
<details class="story" id="{k}" data-key="{k}">
  <summary>
    <span class="top">{E(s['tag'])}</span>
    <h2>{E(s['headline'])}</h2>
    <p class="why">{E(s['why'])}</p>
    <span class="more-cue">Open to share &#8250;</span>
  </summary>
  <div class="body">
    <a class="preview" href="{E(s['source'])}" target="_blank" rel="noopener">
      <img class="og" src="{E(s.get('og_image', ''))}" alt="" loading="lazy" referrerpolicy="no-referrer" data-fallback="img/{k}.png">
      <span class="pmeta"><span class="site">{E(s.get('site', ''))}{'<span class="lang">Hebrew</span>' if he else ''}</span><span class="ogt">{E(s.get('og_title') or s['headline'])}</span></span>
    </a>
    <div class="lbl"><label for="t-{k}">Your post</label>
      <button type="button" class="swap">&#8635; New wording</button></div>
    <p class="tip">Tip: add one sentence about why this matters to you.</p>
    <textarea id="t-{k}" class="post" rows="11" spellcheck="true"></textarea>
    <div class="actions">
      <button type="button" class="btn primary share">Share text + link</button>
      <button type="button" class="btn copy">Copy text</button>
    </div>
    <div class="nets" aria-label="Post to">
      <a class="net wa" target="_blank" rel="noopener">WhatsApp</a>
      <a class="net x" target="_blank" rel="noopener">X</a>
      <a class="net fb" target="_blank" rel="noopener">Facebook</a>
      <a class="net li" target="_blank" rel="noopener">LinkedIn</a>
    </div>
    <p class="hint" aria-live="polite"></p>
    <details class="ours">
      <summary>Need an image to upload? Use ours</summary>
      <p>For Instagram, WhatsApp Status, or a photo post. Free to share.</p>
      <img class="art" src="img/{k}.png" alt="{E(s['headline'])}" width="1080" height="1080" loading="lazy">
      <div class="actions">
        <button type="button" class="btn dl">Download image</button>
        <button type="button" class="btn share-img">Share image + text</button>
      </div>
    </details>
    <p class="src">Source: <a href="{E(s['source'])}" target="_blank" rel="noopener">{E(s['source_name'])}</a>{'<span class="lang">Hebrew</span>' if he else ''}</p>
  </div>
</details>'''

def dedication_html(cfg, ded):
    if ded:
        return f'<p class="ded">This week’s stories are dedicated<span class="name">{E(ded)}</span></p>'
    if cfg.get("dedication_contact"):
        return (f'<p class="ded"><b>Dedicate a week</b> in honor or in memory of someone you love. '
                f'Contact: {E(cfg["dedication_contact"])}</p>')
    return '<p class="ded"><b>Coming soon:</b> dedicate a week’s stories in honor or in memory of someone you love.</p>'

def head(cfg, title, desc, url, prefix):
    img = cfg["site_url"] + "assets/og-card.png"
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta property="og:type" content="website"><meta property="og:site_name" content="{E(cfg['site_name'])}">
<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{E(url)}"><meta property="og:image" content="{E(img)}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="robots" content="noindex">
<link rel="icon" href="{prefix}assets/icon.png">
<style>{font_css(prefix)}{PAGE_CSS}</style></head>'''

def week_page(cfg, wk, ded):
    stories = sorted(wk["stories"], key=lambda s: s["added"], reverse=True)
    preview = dt.date.fromisoformat(wk["week"]) > today_il()
    n = len(stories)
    title = f"{cfg['site_name']}: week of {nice(wk['week'])}"
    desc = f"{n} good-news stories from Israel, ready to share."
    meta = json.dumps({s["key"]: {"headline": s["headline"], "source": s["source"], "texts": s["texts"]} for s in stories}, ensure_ascii=False)
    return f'''{head(cfg, title, desc, cfg["site_url"] + wk["week"] + "/", "../")}
<body><div class="wrap">
{('<p class="preview-note">Preview: this edition is still being collected and will be released on Sunday, ' + nice(wk["week"]) + '. Only people with this link can see it.</p>') if preview else ''}
<header>
  <a class="brand" href="../archive/">{mark(24)}{E(cfg["site_name"])}</a>
  <h1>This week’s good news</h1>
  <p class="date">Week of {nice(wk["week"])} · {n} {"story" if n == 1 else "stories"}</p>
  {dedication_html(cfg, ded)}
  <p class="howto-h">How to share</p>
  <ol class="steps">
    <li>Open a story below. Your top picks are shuffled just for you.</li>
    <li>Edit the post if you like, or tap <b>New wording</b>.</li>
    <li>Tap <b>Share text + link</b>, or <b>Copy text</b> and paste it.</li>
    <li>Post it on WhatsApp, Facebook, X or LinkedIn.</li>
  </ol>
  <details class="heads"><summary>All {n} headlines this week</summary><ul>{"".join(f'<li><a href="#{E(s["key"])}" class="jump">{E(s["teaser"])}</a></li>' for s in stories)}</ul></details>
</header>
<p class="sec">Your picks</p>
<div class="list" id="picks"></div>
<p class="sec" id="more-h">More stories this week</p>
<div class="list" id="more">{"".join(story_html(s) for s in stories)}</div>
<footer>
  <p>Know someone who would post these? Forward this link. <a href="../archive/">Past weeks</a></p>
</footer>
</div>
<script>const META = {meta}; const OPENERS = {json.dumps(cfg["openers"], ensure_ascii=False)};{PAGE_JS}</script>
</body></html>'''

def weeks_built():
    """Released editions only: built, and their Sunday has arrived (Israel time)."""
    today = today_il().isoformat()
    return sorted((p.stem for p in (ROOT / "data/weeks").glob("*.json")
                   if p.stem <= today and (ROOT / p.stem / "index.html").exists()), reverse=True)

def redirect_page(cfg, latest):
    return f'''{head(cfg, cfg["site_name"], cfg["tagline"], cfg["site_url"], "")}
<meta http-equiv="refresh" content="0; url=./{latest}/">
<body><p style="padding:24px"><a href="./{latest}/">Open this week’s stories</a></p>
<script>location.replace('./{latest}/');</script></body></html>'''

def archive_page(cfg):
    items = []
    for w in weeks_built():
        st = json.loads((ROOT / "data/weeks" / f"{w}.json").read_text(encoding="utf-8"))["stories"]
        lis = "".join(f"<li>{E(s['teaser'])}</li>" for s in st[:6])
        extra = f"<li>and {len(st) - 6} more</li>" if len(st) > 6 else ""
        items.append(f'<li class="story" style="padding:16px 18px"><a href="../{w}/" style="color:inherit"><h2>Week of {nice(w)}</h2></a>'
                     f'<ul>{lis}{extra}</ul></li>')
    return f'''{head(cfg, cfg["site_name"] + ": past weeks", cfg["tagline"], cfg["site_url"] + "archive/", "../")}
<body><div class="wrap"><header><a class="brand" href="../">{mark(24)}{E(cfg["site_name"])}</a><h1>Past weeks</h1></header>
<ul style="list-style:none;margin:0;padding:0;display:grid;gap:14px">{"".join(items)}</ul></div></body></html>'''

def whatsapp(cfg, wk, ded):
    d = dt.date.fromisoformat(wk["week"])
    st = wk["stories"]
    lines = [f"*{cfg['site_name']}* · Week of {d.day} {d.strftime('%b')}"]
    if ded:
        lines += [f"\U0001F56F️ This week’s stories are dedicated", f"*{ded}*"]
    lines += ["", f"This week’s good news from Israel: {len(st)} {'story' if len(st) == 1 else 'stories'} ready to share, including:", ""]
    lines += [f"• {s['teaser']}" for s in st[:4]]
    lines += ["", f"Pick a story, tweak the words, share \U0001F449 {cfg['site_url']}{wk['week']}/", "",
              "Know someone who’d share these? Forward this message."]
    return "\n".join(lines) + "\n"

def log_stories(wk):
    p = ROOT / "data/stories-log.csv"
    have = {r["source"] for r in csv.DictReader(open(p, encoding="utf-8"))}
    with open(p, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for s in wk["stories"]:
            if s["source"] not in have:
                w.writerow([s["added"], s["headline"], s["source"]])

def main(week_file):
    cfg, wk, ded = load(week_file)
    week = wk["week"]
    out = ROOT / week
    jobs = [(card_html(cfg, s), out / "img" / f"{s['key']}.png", 1080, 1080)
            for s in wk["stories"] if not (out / "img" / f"{s['key']}.png").exists()]
    if not (ROOT / "assets/og-card.png").exists():
        jobs.append((og_html(cfg), ROOT / "assets/og-card.png", 1200, 630))
    if not (ROOT / "assets/icon.png").exists():
        jobs.append((f'<body style="margin:0">{mark(64)}</body>', ROOT / "assets/icon.png", 64, 64))
    asyncio.run(render(jobs))
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(week_page(cfg, wk, ded), encoding="utf-8")
    released = weeks_built()
    if released:
        (ROOT / "index.html").write_text(redirect_page(cfg, released[0]), encoding="utf-8")
    (ROOT / "archive").mkdir(exist_ok=True)
    (ROOT / "archive/index.html").write_text(archive_page(cfg), encoding="utf-8")
    (ROOT / "data/whatsapp").mkdir(exist_ok=True)
    msg = whatsapp(cfg, wk, ded)
    (ROOT / "data/whatsapp" / f"{week}.txt").write_text(msg, encoding="utf-8")
    log_stories(wk)
    status = "RELEASED (live)" if week <= today_il().isoformat() else "PREVIEW (not linked until its Sunday)"
    print(f"Built edition {week}: {len(wk['stories'])} stories, {status}. Page: {cfg['site_url']}{week}/\n")
    print(msg)

if __name__ == "__main__":
    main(sys.argv[1])
