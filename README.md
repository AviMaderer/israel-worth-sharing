# israel-worth-sharing

Daily verified good news from Israel, with ready-to-share posts for social media.

Live site: https://avimaderer.github.io/israel-worth-sharing/

## How it works

Each morning a Claude scheduled task follows `CONTENT_RULES.md`: it finds and verifies stories, writes `data/days/<date>.json`, runs `tools/build.py`, and pushes. GitHub Pages publishes the result.

## Files you may edit

| File | What it controls |
|---|---|
| `CONTENT_RULES.md` | How stories are chosen and written |
| `data/config.json` | Site name, tagline, hashtag, opening lines, dedication contact |
| `data/dedications.csv` | One row per dedicated day: `date,text`, e.g. `2026-10-14,in loving memory of David ben Moshe` |
| `data/days/<date>.json` | A day's stories (fix a typo, then re-run the build) |

## Generated files (don't edit by hand)

`<date>/` day pages and images, `index.html` (redirects to the latest day), `archive/`, `data/whatsapp/`, `data/stories-log.csv`.
