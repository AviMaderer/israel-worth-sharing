# Israel Worth Sharing: run instructions

The scheduled task follows this file. Edit it to change how stories are chosen or written.

## How the week works

- One **edition per week**, named by the date of its Sunday (Israel time): `data/weeks/<SUNDAY>.json`, published at `<site_url><SUNDAY>/`.
- **Sunday run:** create the new week file and add **8–10 stories**. Then email Avi the weekly WhatsApp message to send.
- **Monday–Friday runs:** add **2–3 new stories** to the current week's file and rebuild. Email Avi a short note (no WhatsApp message needed).
- Fewer stories is fine if not enough meet the bar. Never pad with a weak story.
- If a run finds nothing new, still rebuild the week (so dedication or config changes take effect) and say so in the email.

## 1. Before researching

- Today's date is the date in Israel (Asia/Jerusalem). This week's Sunday is today if today is Sunday, otherwise the most recent Sunday.
- Read `data/config.json`, `data/sources.md`, `data/stories-log.csv` and the current week file if it exists.
- Never repeat a story whose source, or the same underlying event, is already in the log or in the week file.

## 2. Choosing stories

- Search across **all** source groups in `data/sources.md` (English news, Hebrew news, universities, hospitals, aid organizations, innovation). Use WebSearch, site-restricted searches, and the sources' own news pages.
- **No more than 2 stories from the same outlet per run**, and aim for a mix of categories: health and medicine, science, technology, aid and rescue, environment, agriculture and water, education, culture, coexistence.
- Every story must:
  - be **positive, real and already happened** (no funding announcements, "could one day" claims, or plans);
  - be **recent**: prefer the last 4 weeks; up to 3 months is acceptable for a strong story;
  - have Israel or Israelis at its center;
  - be **verified at the source**: open (fetch) the article itself and check every number, name, date and quote against it. Never rely on a search snippet;
  - stay out of **military, political and conflict topics** (pilot rule).
- **Prefer free-to-read sources.** Avoid paywalled ones (Haaretz, Globes premium).
- **Hebrew sources:** if an English version of the same story exists anywhere, link that instead. If only a Hebrew source exists, use it and set `"source_lang": "he"`. The post text stays in English; the build adds a note that the article is in Hebrew.

## 3. Writing each story (fields in the week file)

| Field | Rule |
|---|---|
| `key` | short lowercase slug, unique within the week (e.g. `zambia-hearts`) |
| `added` | today's date, YYYY-MM-DD |
| `tag` | category, 1–2 words (e.g. `Global health`) |
| `teaser` | for the WhatsApp message, max ~70 characters |
| `headline` | max ~80 characters, plain and specific |
| `why` | one line: the key number or proof point |
| `texts` | **three versions** of the post, each 50–90 words, warm and factual, short paragraphs: (1) personal and warm, (2) number-led and factual, (3) opens with a question or a hook. Do NOT add an opening line (the page adds a rotating one). Quotes only if copied exactly from the source. Each ends with one hashtag line starting `#Israel` plus 2–3 topic tags; the build adds `#IsraelWorthSharing`. |
| `source` | article URL |
| `source_name` | publisher and date, e.g. `The Times of Israel, Sep 23, 2026` |
| `site` | publisher domain, e.g. `timesofisrael.com` |
| `source_lang` | only for Hebrew sources: `"he"` |
| `og_title` | the article's own title (its og:title) |
| `og_image` | the article's preview image URL (its og:image). Leave empty if there is none. Never download or re-host it. |

Add new stories to the end of the `stories` list. Never remove or rewrite stories already published this week, except to fix an error.

## 4. Build and publish

1. Save the week file.
2. Run `python tools/build.py data/weeks/<SUNDAY>.json`.
3. Commit with the message `Week <SUNDAY>: +N stories` (or `Rebuild <SUNDAY>`) and push to `main`.

## 5. Email Avi (avi.maderer@gmail.com)

**Sunday** subject: `ISRAEL WORTH SHARING WEEK OF <SUNDAY>: ready to send`
1. The page link.
2. The WhatsApp message, copied exactly from `data/whatsapp/<SUNDAY>.txt`, as plain text ready to paste.
3. For each new story: headline, source link, and one line on how it was verified.
4. Anything Avi should double-check (an older story, a thin source, a Hebrew-only source, a missing preview image).

**Monday–Friday** subject: `ISRAEL WORTH SHARING <DATE>: N stories added`
The page link, the new headlines with source links, and anything to double-check. No WhatsApp message.

If anything fails (build or push error), email Avi what happened instead, and do not publish a partial page.
