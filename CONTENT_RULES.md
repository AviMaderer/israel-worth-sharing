# Israel Worth Sharing: run instructions

The scheduled task follows this file. Edit it to change how stories are chosen or written.

## How the week works

- One **edition per week**, named by the date of its Sunday (Israel time): `data/weeks/<SUNDAY>.json`, published at `<site_url><SUNDAY>/`.
- Stories are **gathered every day, including Saturday**, into the **upcoming edition**. Until its Sunday, that edition's page is an unlinked preview (only Avi has the link).
- **Which edition to add to:** on Sunday, today's edition (it is released this morning). On any other day, the **next** Sunday's edition. Create the week file if it doesn't exist yet.
- **Monday–Saturday runs:** add **2–3 new stories** to the upcoming edition and rebuild. Email Avi a short note.
- **Sunday run (release):** add final stories to today's edition so it has **at least 12** where possible (otherwise 3–5 more), rebuild, push. The build releases it automatically: the main link and the archive switch to it. Email Avi the WhatsApp message to send.
- **Nothing is missed after the release:** news published on Sunday after the release run, or late on Saturday, is picked up by the next run and goes into the following edition. Each run searches the last several days, not only the last 24 hours; the story log prevents repeats.
- Fewer stories is fine if not enough meet the bar. Never pad with a weak story.
- If a run finds nothing new, still rebuild (so dedication or config changes take effect) and say so in the email.

## 1. Before researching

- Today's date is the date in Israel (Asia/Jerusalem).
- Read `data/config.json`, `data/sources.md`, `data/stories-log.csv` and the target edition's week file if it exists.
- Never repeat a story whose source, or the same underlying event, is already in the log or in any week file.

## 2. Choosing stories

- Search across **all** source groups in `data/sources.md` (English news, Hebrew news, universities, hospitals, aid organizations, innovation). Use WebSearch, site-restricted searches, and the sources' own news pages.
- **No more than 2 stories from the same outlet per run**, and aim for a mix of categories across the edition: health and medicine, science, technology, aid and rescue, environment, agriculture and water, education, culture, coexistence.
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
| `key` | short lowercase slug, unique within the edition (e.g. `zambia-hearts`) |
| `added` | today's date, YYYY-MM-DD |
| `tag` | category, 1–2 words (e.g. `Global health`) |
| `teaser` | for the WhatsApp message and headline list, max ~70 characters |
| `headline` | max ~80 characters, plain and specific |
| `why` | one line: the key number or proof point |
| `texts` | **three versions** of the post, each 50–90 words, warm and factual, short paragraphs: (1) personal and warm, (2) number-led and factual, (3) opens with a question or a hook. Do NOT add an opening line (the page adds a rotating one). Quotes only if copied exactly from the source. Each ends with one hashtag line starting `#Israel` plus 2–3 topic tags; the build adds `#IsraelWorthSharing`. |
| `source` | article URL |
| `source_name` | publisher and date, e.g. `The Times of Israel, Sep 23, 2026` |
| `site` | publisher domain, e.g. `timesofisrael.com` |
| `source_lang` | only for Hebrew sources: `"he"` |
| `og_title` | the article's own title (its og:title) |
| `og_image` | the article's preview image URL (its og:image). Leave empty if there is none. Never download or re-host it. |

Add new stories to the end of the `stories` list. Never remove or rewrite stories already in the file, except to fix an error. Once an edition is released, do not add to it again.

## 4. Build and publish

1. Save the week file.
2. Run `python tools/build.py data/weeks/<SUNDAY>.json`.
3. Commit with the message `Edition <SUNDAY>: +N stories` (Sunday: `Release <SUNDAY>`) and push to `main`.

## 5. Email Avi (avi.maderer@gmail.com)

Always put the page link at the top.

**Sunday** subject: `ISRAEL WORTH SHARING EDITION <SUNDAY>: ready to send`
1. The page link (now live).
2. The WhatsApp message, copied exactly from `data/whatsapp/<SUNDAY>.txt`, as plain text ready to paste.
3. The number of stories, and for each story added today: headline, source link, and one line on how it was verified.
4. Anything Avi should double-check (an older story, a thin source, a Hebrew-only source, a missing preview image).

**Monday–Saturday** subject: `ISRAEL WORTH SHARING <DATE>: N stories added to <SUNDAY> edition`
The preview link for the upcoming edition, its running story count, the new headlines with source links, and anything to double-check. No WhatsApp message.

If anything fails (build or push error), email Avi what happened instead, and do not publish a partial page.
