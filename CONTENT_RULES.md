# Israel Worth Sharing: daily run instructions

The daily scheduled task follows this file. Edit it to change how stories are chosen or written.

## 1. Before researching

- Today's date is the date in Israel (Asia/Jerusalem).
- Read `data/config.json` and `data/stories-log.csv`. Never repeat a story whose source, or the same underlying event, is already in the log.
- If `data/days/<today>.json` already exists, stop and report: today was already built.

## 2. Choosing stories

Pick **3 stories**, ideally from 3 different categories:
health and medicine, science, technology and innovation, aid and rescue, environment, agriculture and water, education, culture, coexistence.

Every story must:

- Be **positive, real and already happened.** No funding announcements, "could one day" claims, or plans.
- Be **recent.** Prefer the last 4 weeks. Up to 3 months old is acceptable when the story is strong.
- Have Israel or Israelis at its center.
- Be **verified at the source:** open (fetch) the article itself and check every number, name, date and quote against it. Never rely on a search snippet.
- Use a **free-to-read source** where possible (Times of Israel, ISRAEL21c, NoCamels, Jerusalem Post, university and hospital press offices, IsraAID, United Hatzalah, Save a Child's Heart). Avoid paywalled sources (Haaretz, Globes premium).
- Stay out of **military, political and conflict topics** (pilot rule).

If only 1 or 2 stories meet the bar, publish 1 or 2. Never pad with a weak story.

## 3. Writing each story (fields in the day file)

| Field | Rule |
|---|---|
| `key` | short lowercase word, unique for the day (e.g. `heart`) |
| `tag` | category, 1–2 words (e.g. `Global health`) |
| `teaser` | for the WhatsApp message, max ~70 characters |
| `headline` | max ~80 characters, plain and specific |
| `why` | one line: the key number or proof point |
| `text` | the post: 50–90 words, warm and factual, short paragraphs. Do NOT add an opening line (the page adds a rotating one). Quotes only if copied exactly from the source. End with one hashtag line starting with `#Israel` plus 2–3 topic tags. The build adds `#IsraelWorthSharing`. |
| `source` | article URL |
| `source_name` | publisher and date, e.g. `The Times of Israel, Sep 23, 2026` |
| `site` | publisher domain, e.g. `timesofisrael.com` |
| `og_title` | the article's own title (from its og:title) |
| `og_image` | the article's preview image URL (its og:image). Leave empty if there is none. Never download or re-host it. |

## 4. Build and publish

1. Save the day file as `data/days/<YYYY-MM-DD>.json` (same shape as the existing day files).
2. Run `python tools/build.py data/days/<YYYY-MM-DD>.json` (needs Playwright; install with `pip install playwright` if missing; Chromium is preinstalled).
3. Commit everything with the message `Day <YYYY-MM-DD>` and push to `main`.
4. Wait about a minute, then confirm the page answers at `<site_url><YYYY-MM-DD>/`.

## 5. Email Avi

Subject: `ISRAEL WORTH SHARING <YYYY-MM-DD>: ready to post`

Body, in this order:

1. The page link.
2. The WhatsApp message, copied exactly from `data/whatsapp/<YYYY-MM-DD>.txt`, ready to paste.
3. For each story: headline, source link, and one line on how it was verified.
4. Anything Avi should double-check (an older story, a thin source, a missing preview image).

If anything failed (no stories cleared the bar, build or push error), email Avi what happened instead, and do not publish a partial page.
