# israel-worth-sharing

Weekly verified good news from Israel, with ready-to-share posts for social media.

Live site: https://avimaderer.github.io/israel-worth-sharing/

## How it works

One edition per week (named by its Sunday). Every morning Sunday–Friday a Claude scheduled task follows `CONTENT_RULES.md`: on Sunday it starts the week with 8–10 stories and prepares the WhatsApp message; Monday–Friday it adds 2–3 more. GitHub Pages publishes the result.

## Files you may edit

| File | What it controls |
|---|---|
| `CONTENT_RULES.md` | How stories are chosen and written |
| `data/sources.md` | Where the task looks for stories |
| `data/config.json` | Site name, tagline, hashtag, opening lines, dedication contact |
| `data/dedications.csv` | One row per dedication: `start_date,end_date,text`, e.g. `2026-10-04,2026-10-10,In loving memory of David ben Moshe`. Leave end_date empty for one day. Shows on every week the period overlaps; the shortest matching period wins. |
| `data/weeks/<SUNDAY>.json` | A week's stories (fix a typo, then re-run the build) |

## Generated files (don't edit by hand)

`<SUNDAY>/` week pages and images, `index.html` (redirects to the latest week), `archive/`, `data/whatsapp/`, `data/stories-log.csv`.
