"""Build one day of Israel Worth Sharing.

Usage:  python tools/build.py data/days/YYYY-MM-DD.json

Reads   data/config.json, data/dedications.csv, the day file
Writes  YYYY-MM-DD/index.html          the day's page
        YYYY-MM-DD/img/<key>.png       our branded image per story (fallback + upload option)
        index.html                     redirects to the latest day
        archive/index.html             list of all days
        data/whatsapp/YYYY-MM-DD.txt   ready-to-paste WhatsApp message
        data/stories-log.csv           appends the day's stories (no duplicates)
        assets/og-card.png             site link-preview image (only if missing)
Needs   Python 3 + Playwright with Chromium (for the images).
"""
import csv, datetime as dt, html, json, pathlib, sys, asyncio

ROOT = pathlib.Path(__file__).resolve().parent.parent
E = html.escape
BLUE, GOLD, INK = "#0038B8", "#E8B04B", "#1C2333"

# ---------- inputs ----------
def load(day_file):
    cfg = json.loads((ROOT / "data/config.json").read_text(encoding="utf-8"))
    day = json.loads(pathlib.Path(day_file).read_text(encoding="utf-8"))
    ded = find_dedication(day["date"])
    assert 1 <= len(day["stories"]) <= 3, "A day needs 1 to 3 stories"
    for s in day["stories"]:
        for k in ("key", "tag", "teaser", "headline", "why", "text", "source", "source_name"):
            assert s.get(k), f"story missing '{k}'"
        tag = cfg["hashtag"]
        if tag not in s["text"]:
            lines = s["text"].rstrip().split("\n")
            if lines[-1].startswith("#"):
                lines[-1] += " " + tag
            else:
                lines += ["", tag]
            s["text"] = "\n".join(lines)
    return cfg, day, ded

def find_dedication(date_iso):
    """Dedication text for one page date, or "".

    data/dedications.csv columns: start_date,end_date,text (YYYY-MM-DD).
    Both dates are inclusive whole days: a page dated on the start date, the
    end date, or any day between gets the dedication. end_date may be left
    empty for a single day. If several rows match, the shortest period wins
    (so a one-day dedication overrides a month-long one); ties go to the
    later row in the file.
    """
    day = dt.date.fromisoformat(date_iso)
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
            if a <= day <= b and (best_len is None or (b - a).days <= best_len):
                best, best_len = text, (b - a).days
    return best

def nice_date(iso):
    d = dt.date.fromisoformat(iso)
    return f"{d.strftime('%A')}, {d.day} {d.strftime('%B %Y')}"

# ---------- brand pieces ----------
def mark(size, bg=GOLD, fg=INK):
    # Three linked dots: the "share" idea, in brand colors.
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 48 48" aria-hidden="true">'
            f'<rect width="48" height="48" rx="12" fill="{bg}"/>'
            f'<path d="M16 24 L32 15 M16 24 L32 33" stroke="{fg}" stroke-width="3.5" stroke-linecap="round"/>'
            f'<circle cx="15" cy="24" r="5.5" fill="{fg}"/><circle cx="33" cy="14.5" r="5.5" fill="{fg}"/>'
            f'<circle cx="33" cy="33.5" r="5.5" fill="{fg}"/></svg>')

def font_css(prefix, embed=False):
    import base64
    def src(file):
        if embed:
            return "data:font/woff2;base64," + base64.b64encode((ROOT / "assets/fonts" / file).read_bytes()).decode()
        return f"{prefix}assets/fonts/{file}"
    f = lambda fam, w, file: (f"@font-face{{font-family:'{fam}';font-weight:{w};font-display:swap;"
                              f"src:url({src(file)}) format('woff2')}}")
    return "\n".join([f("Rubik", 500, "rubik-latin-500-normal.woff2"), f("Rubik", 700, "rubik-latin-700-normal.woff2"),
                      f("Assistant", 400, "assistant-latin-400-normal.woff2"), f("Assistant", 700, "assistant-latin-700-normal.woff2")])

# ---------- images (Playwright) ----------
def card_html(cfg, s):
    return f'''<html><head><style>{font_css("", embed=True)}
body{{margin:0;width:1080px;height:1080px;overflow:hidden;font-family:Rubik}}
.c{{position:relative;width:1080px;height:1080px;box-sizing:border-box;padding:84px;display:flex;flex-direction:column;
 background:{BLUE};background-image:radial-gradient(rgba(255,255,255,.10) 2.5px, transparent 2.5px);background-size:44px 44px}}
.b{{display:flex;align-items:center;gap:18px;font:500 30px/1 Rubik;letter-spacing:.12em;color:{GOLD}}}
.t{{margin-top:auto;font:500 30px/1 Rubik;letter-spacing:.1em;text-transform:uppercase;color:#C9D6F5}}
h1{{margin:22px 0 0;font:700 86px/1.06 Rubik;color:#fff;letter-spacing:-.015em;text-wrap:balance}}
.r{{margin-top:44px;height:8px;width:140px;background:{GOLD};border-radius:4px}}
</style></head><body><div class="c"><div class="b">{mark(56)}{E(cfg["site_name"]).upper()}</div>
<div class="t">{E(s["tag"])}</div><h1>{E(s["headline"])}</h1><div class="r"></div></div></body></html>'''

def og_html(cfg):
    return f'''<html><head><style>{font_css("", embed=True)}
body{{margin:0;width:1200px;height:630px;overflow:hidden}}
.c{{width:1200px;height:630px;box-sizing:border-box;padding:90px;display:flex;flex-direction:column;justify-content:center;gap:28px;
 background:{BLUE};background-image:radial-gradient(rgba(255,255,255,.10) 2.5px, transparent 2.5px);background-size:44px 44px}}
h1{{margin:0;font:700 96px/1 Rubik;color:#fff;letter-spacing:-.02em}} p{{margin:0;font:500 40px/1.2 Rubik;color:{GOLD}}}
</style></head><body><div class="c">{mark(110)}<h1>{E(cfg["site_name"])}</h1><p>{E(cfg["tagline"])}</p></div></body></html>'''

async def render(jobs):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for html_src, path, w, h in jobs:
            pg = await b.new_page(viewport={"width": w, "height": h})
            await pg.set_content(html_src); await pg.wait_for_timeout(300)
            path.parent.mkdir(parents=True, exist_ok=True)
            await pg.screenshot(path=str(path)); await pg.close()
        await b.close()

# ---------- day page ----------
PAGE_CSS = """
:root{--blue:#0038B8;--gold:#E8B04B;--sand:#F3ECE0;--paper:#FFFDF9;--ink:#1C2333;--muted:#5B6275;--line:#E3D9C8;--btn-fg:#FFFFFF;--soft:#EAF0FB;
 --f-display:'Rubik','Segoe UI',system-ui,sans-serif;--f-body:'Assistant','Segoe UI',system-ui,sans-serif;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--blue:#7EA2FF;--gold:#F0BE62;--sand:#10162A;--paper:#182038;--ink:#ECEFF7;--muted:#A6AEC4;--line:#2A3452;--btn-fg:#0B1124;--soft:#1F2A4A;color-scheme:dark}}
:root[data-theme="dark"]{--blue:#7EA2FF;--gold:#F0BE62;--sand:#10162A;--paper:#182038;--ink:#ECEFF7;--muted:#A6AEC4;--line:#2A3452;--btn-fg:#0B1124;--soft:#1F2A4A;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--sand);color:var(--ink);font:400 18px/1.5 var(--f-body);padding-inline:16px;padding-block:max(20px,env(safe-area-inset-top)) 48px}
.wrap{max-width:560px;margin:0 auto;display:grid;gap:28px}
header{display:grid;gap:6px;padding-top:8px}
.brand{display:flex;align-items:center;gap:10px;font:500 14px/1 var(--f-display);letter-spacing:.14em;color:var(--blue);text-transform:uppercase;text-decoration:none}
header h1{margin:6px 0 0;font:700 clamp(30px,8vw,40px)/1.05 var(--f-display);letter-spacing:-.015em;text-wrap:balance}
.date{margin:0;color:var(--muted);font-size:16px}
.today{margin:18px 0 0;padding:14px 16px;border-radius:10px;background:var(--paper);border:1px solid var(--line)}
.today h2{margin:0 0 6px;font-size:18px}
.today ul{margin:0;padding-left:20px}
.today li{margin:4px 0;font-size:16px;line-height:1.4}
.today a{color:inherit}
.howto{margin:6px 0 0;padding-left:22px;color:var(--muted);font-size:16px}
.howto li{margin:3px 0}
.howto-h{margin:16px 0 0;font-size:15px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}
.ded{margin:6px 0 0;padding:12px 16px;border-radius:10px;background:var(--paper);border:1px solid var(--line);font-size:17px;text-align:center;line-height:1.45}
.ded b{display:block;font-family:var(--f-display);font-weight:700}
.story{background:var(--paper);border:1px solid var(--line);border-radius:14px;overflow:hidden}
.preview{display:block;text-decoration:none;color:inherit;background:var(--soft);border-bottom:1px solid var(--line)}
.og{display:block;width:100%;max-width:100%;aspect-ratio:1.91;object-fit:cover;background:var(--line)}
.pmeta{display:grid;gap:4px;padding:12px 16px 14px}
.site{font:500 12px/1 var(--f-display);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.ogt{font:500 16px/1.3 var(--f-display);color:var(--ink)}
.body{padding:20px 20px 22px;display:grid;gap:12px;min-width:0}
.tag{margin:0;font:500 13px/1 var(--f-display);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.num{color:var(--blue);margin-right:6px;font-variant-numeric:tabular-nums}
h2{margin:0;font:700 24px/1.18 var(--f-display);letter-spacing:-.01em;text-wrap:balance}
.why{margin:0;color:var(--muted);font-size:17px}
.lbl{margin-top:6px;font:500 14px/1 var(--f-display);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.lbl span{color:var(--muted);margin-left:6px}
.swap{border:0;background:var(--soft);color:var(--blue);font:500 14px/1 var(--f-display);padding:9px 12px;border-radius:999px;cursor:pointer}
.post{width:100%;resize:vertical;font:400 17px/1.5 var(--f-body);color:var(--ink);background:var(--sand);border:1px solid var(--line);border-radius:10px;padding:12px 14px;min-height:220px}
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
footer{display:grid;gap:10px;color:var(--muted);font-size:15px}
footer a{color:var(--ink)}
"""

PAGE_JS = r"""
const enc = encodeURIComponent;
const order = OPENERS.map((_, i) => i).sort(() => Math.random() - 0.5);
document.querySelectorAll('.story').forEach((card, idx) => {
  const key = card.dataset.key, m = META[key];
  const img = card.querySelector('.art'), ta = card.querySelector('.post'), hint = card.querySelector('.hint');
  const og = card.querySelector('.og');
  const say = t => { hint.textContent = t; clearTimeout(card._t); card._t = setTimeout(() => hint.textContent = '', 4000); };
  const fallback = () => { og.onerror = null; og.src = og.dataset.fallback; og.style.aspectRatio = '1'; };
  if (!og.getAttribute('src')) fallback(); else { og.onerror = fallback; if (og.complete && og.naturalWidth === 0) fallback(); }
  const links = () => {
    const t = ta.value.trim();
    card.querySelector('.wa').href = 'https://wa.me/?text=' + enc(t + '\n\n' + m.source);
    card.querySelector('.x').href = 'https://twitter.com/intent/tweet?text=' + enc(m.headline) + '&url=' + enc(m.source);
    card.querySelector('.fb').href = 'https://www.facebook.com/sharer/sharer.php?u=' + enc(m.source);
    card.querySelector('.li').href = 'https://www.linkedin.com/sharing/share-offsite/?url=' + enc(m.source);
  };
  let pos = idx * 3, opener = OPENERS[order[pos % OPENERS.length]];
  ta.value = opener + '\n\n' + ta.value;
  card.querySelector('.swap').addEventListener('click', () => {
    pos += 1; const next = OPENERS[order[pos % OPENERS.length]];
    if (ta.value.startsWith(opener)) ta.value = next + ta.value.slice(opener.length);
    else ta.value = next + '\n\n' + ta.value;
    opener = next; links(); say('New opening line. Edit it any way you like.');
  });
  links(); ta.addEventListener('input', links);
  const file = async () => new File([await (await fetch(img.src)).blob()], `israel-worth-sharing-${key}.png`, { type: 'image/png' });
  const copy = async () => {
    try { await navigator.clipboard.writeText(ta.value); return true; }
    catch { ta.select(); try { return document.execCommand('copy'); } catch { return false; } }
  };
  card.querySelector('.copy').addEventListener('click', async () => say(await copy() ? 'Copied. Paste it into your post.' : 'Text selected. Press Copy on your keyboard.'));
  card.querySelector('.fb').addEventListener('click', () => copy().then(ok => ok && say('Text copied. Paste it into your Facebook post.')));
  card.querySelector('.li').addEventListener('click', () => copy().then(ok => ok && say('Text copied. Paste it into your LinkedIn post.')));
  card.querySelector('.share').addEventListener('click', async () => {
    try { if (navigator.share) { await navigator.share({ text: ta.value.trim(), url: m.source }); return; } }
    catch (e) { if (e && e.name === 'AbortError') return; }
    await copy(); say('Text copied. Use a button below to post, then paste.');
  });
  card.querySelector('.dl').addEventListener('click', async () => {
    const f = await file(), a = document.createElement('a');
    a.href = URL.createObjectURL(f); a.download = f.name; document.body.appendChild(a); a.click(); a.remove();
    say('Image saved. On a phone you can also press and hold the image.');
  });
  card.querySelector('.share-img').addEventListener('click', async () => {
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

def story_html(i, n, s):
    og = E(s.get("og_image", ""))
    return f'''
<article class="story" id="{E(s['key'])}" data-key="{E(s['key'])}">
  <a class="preview" href="{E(s['source'])}" target="_blank" rel="noopener">
    <img class="og" src="{og}" alt="" referrerpolicy="no-referrer" data-fallback="img/{E(s['key'])}.png">
    <span class="pmeta"><span class="site">{E(s.get('site', ''))}</span><span class="ogt">{E(s.get('og_title') or s['headline'])}</span></span>
  </a>
  <div class="body">
    <p class="tag"><span class="num">{i}/{n}</span> {E(s['tag'])}</p>
    <h2>{E(s['headline'])}</h2>
    <p class="why">{E(s['why'])}</p>
    <div class="lbl"><label for="t-{E(s['key'])}">Your post<span>edit freely</span></label>
      <button type="button" class="swap">&#8635; Try another opening</button></div>
    <textarea id="t-{E(s['key'])}" class="post" rows="10" spellcheck="true">{E(s['text'])}</textarea>
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
      <img class="art" src="img/{E(s['key'])}.png" alt="{E(s['headline'])}" width="1080" height="1080" loading="lazy">
      <div class="actions">
        <button type="button" class="btn dl">Download image</button>
        <button type="button" class="btn share-img">Share image + text</button>
      </div>
    </details>
    <p class="src">Source: <a href="{E(s['source'])}" target="_blank" rel="noopener">{E(s['source_name'])}</a></p>
  </div>
</article>'''

def dedication_html(cfg, ded):
    if ded:
        return f'<p class="ded">Today’s stories are dedicated<b>{E(ded)}</b></p>'
    if cfg.get("dedication_contact"):
        return (f'<p class="ded"><b>Dedicate a day</b> in honor or in memory of someone you love. '
                f'Contact: {E(cfg["dedication_contact"])}</p>')
    return '<p class="ded"><b>Coming soon:</b> dedicate a day’s stories in honor or in memory of someone you love.</p>'

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
<link rel="icon" href="{prefix}assets/icon.png">
<style>{font_css(prefix)}{PAGE_CSS}</style></head>'''

def day_page(cfg, day, ded):
    n = len(day["stories"]); date = day["date"]
    word = {1: "One good thing", 2: "Two good things", 3: "Three good things"}[n]
    title = f"{cfg['site_name']}: {word}, {nice_date(date)}"
    desc = " · ".join(s["teaser"] for s in day["stories"])
    meta = json.dumps({s["key"]: {"headline": s["headline"], "source": s["source"]} for s in day["stories"]}, ensure_ascii=False)
    return f'''{head(cfg, title, desc, cfg["site_url"] + date + "/", "../")}
<body><div class="wrap">
<header>
  <a class="brand" href="../archive/">{mark(24)}{E(cfg["site_name"])}</a>
  <h1>{word}</h1>
  <p class="date">{nice_date(date)}</p>
  {dedication_html(cfg, ded)}
  <section class="today"><h2>Today’s good news from Israel:</h2><ul>{"".join(f'<li><a href="#{E(s["key"])}">{E(s["teaser"])}</a></li>' for s in day["stories"])}</ul></section>
  <p class="howto-h">How to share</p>
  <ol class="howto">
    <li>Pick a story below and edit the post if you like.</li>
    <li>Tap <b>Share text + link</b>, or <b>Copy text</b>.</li>
    <li>Post it on WhatsApp, Facebook, X or LinkedIn.</li>
  </ol>
</header>
{"".join(story_html(i + 1, n, s) for i, s in enumerate(day["stories"]))}
<footer>
  <p>Know someone who would post these? Forward today’s link. <a href="../archive/">Past days</a></p>
</footer>
</div>
<script>const META = {meta}; const OPENERS = {json.dumps(cfg["openers"], ensure_ascii=False)};{PAGE_JS}</script>
</body></html>'''

def redirect_page(cfg, latest):
    return f'''{head(cfg, cfg["site_name"], cfg["tagline"], cfg["site_url"], "")}
<meta http-equiv="refresh" content="0; url=./{latest}/">
<body><p style="padding:24px"><a href="./{latest}/">Open today’s stories</a></p>
<script>location.replace('./{latest}/');</script></body></html>'''

def archive_page(cfg):
    days = sorted((p.stem for p in (ROOT / "data/days").glob("*.json")), reverse=True)
    items = []
    for d in days:
        if not (ROOT / d / "index.html").exists():
            continue
        st = json.loads((ROOT / "data/days" / f"{d}.json").read_text(encoding="utf-8"))["stories"]
        lis = "".join(f"<li>{E(s['teaser'])}</li>" for s in st)
        items.append(f'<li class="story" style="padding:16px 18px"><a href="../{d}/" style="color:inherit"><h2>{nice_date(d)}</h2></a><ul>{lis}</ul></li>')
    return f'''{head(cfg, cfg["site_name"] + ": past days", cfg["tagline"], cfg["site_url"] + "archive/", "../")}
<body><div class="wrap"><header><a class="brand" href="../">{mark(24)}{E(cfg["site_name"])}</a><h1>Past days</h1></header>
<ul style="list-style:none;margin:0;padding:0;display:grid;gap:14px">{"".join(items)}</ul></div></body></html>'''

def whatsapp(cfg, day, ded):
    d = dt.date.fromisoformat(day["date"])
    lines = [f"*{cfg['site_name']}* · {d.strftime('%a')} {d.day} {d.strftime('%b')}"]
    if ded:
        lines.append(f"\U0001F56F️ Today’s stories are dedicated {ded}")
    lines += ["", "Today’s good news from Israel:", ""]
    lines += [f"• {s['teaser']}" for s in day["stories"]]
    lines += ["", f"Ready-to-post text and links \U0001F449 {cfg['site_url']}{day['date']}/", "",
              "Know someone who’d share these? Forward this message."]
    return "\n".join(lines) + "\n"

def log_stories(day):
    p = ROOT / "data/stories-log.csv"
    have = {r["source"] for r in csv.DictReader(open(p, encoding="utf-8"))}
    with open(p, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        for s in day["stories"]:
            if s["source"] not in have:
                w.writerow([day["date"], s["headline"], s["source"]])

def main(day_file):
    cfg, day, ded = load(day_file)
    date = day["date"]
    out = ROOT / date
    jobs = [(card_html(cfg, s), out / "img" / f"{s['key']}.png", 1080, 1080) for s in day["stories"]]
    if not (ROOT / "assets/og-card.png").exists():
        jobs.append((og_html(cfg), ROOT / "assets/og-card.png", 1200, 630))
    if not (ROOT / "assets/icon.png").exists():
        jobs.append((f'<body style="margin:0">{mark(64)}</body>', ROOT / "assets/icon.png", 64, 64))
    asyncio.run(render(jobs))
    (out / "index.html").write_text(day_page(cfg, day, ded), encoding="utf-8")
    latest = max(p.name for p in ROOT.iterdir() if p.is_dir() and len(p.name) == 10 and p.name[4] == "-" and (p / "index.html").exists())
    (ROOT / "index.html").write_text(redirect_page(cfg, latest), encoding="utf-8")
    (ROOT / "archive").mkdir(exist_ok=True)
    (ROOT / "archive/index.html").write_text(archive_page(cfg), encoding="utf-8")
    (ROOT / "data/whatsapp").mkdir(exist_ok=True)
    msg = whatsapp(cfg, day, ded)
    (ROOT / "data/whatsapp" / f"{date}.txt").write_text(msg, encoding="utf-8")
    log_stories(day)
    print(f"Built {date}: {len(day['stories'])} stories. Page: {cfg['site_url']}{date}/\n")
    print(msg)

if __name__ == "__main__":
    main(sys.argv[1])
