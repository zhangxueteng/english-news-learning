# Newslingo — English News Learning Website

A responsive static website for learning English through daily news. It includes:
- Daily news cards with A1–C1 level filters and search
- Article detail drawer with video/source link, sentence-by-sentence Chinese translation
- Clickable key vocabulary, phrases, grammar explanations, save-word interaction
- Local-browser learning progress
- GitHub Actions workflow to generate graded learning cards from official BBC News/CNN video RSS feeds daily

## Important demo status
The initial page includes clearly labelled sample learning cards so the interface works immediately. The video buttons point to topic searches and source sections; they are not falsely represented as embedded licensed videos. Real-time articles are populated after setup below. News providers' copyright and embedding terms apply.

## Deploy publicly with GitHub Pages
1. Create a **public** GitHub repository, for example `english-news-learning`.
2. Upload all files/folders in this project to the repository root (keep `.github/workflows/daily-news.yml`).
3. Open **Settings → Pages**. Choose **Deploy from a branch**, branch `main`, folder `/ (root)`, then Save.
4. The public URL will be `https://YOUR-GITHUB-USERNAME.github.io/english-news-learning/`. It becomes active after GitHub finishes its first deployment.
5. Open **Settings → Secrets and variables → Actions → New repository secret**. Add `OPENAI_API_KEY` with an API key that has API billing enabled. Never put the key in `index.html`.
6. Open **Actions → Update daily English news → Run workflow** to test the first refresh. It is then scheduled daily at 06:15 UTC+8.
7. In **Settings → Actions → General**, ensure the workflow has permission to read and write repository contents if a commit is blocked.

## Daily content pipeline
Official BBC News/CNN YouTube channel RSS feeds → video IDs and titles → original publisher-hosted video embed + English audio → learning aids and title translation → `data/news.json` → GitHub Pages publish.
Every newly generated news card is based on a video published by an official news-channel YouTube feed and embeds the publisher-hosted video, so playback uses original English audio instead of browser-generated speech. News cards are not published from text-only RSS headlines. If the official video feeds fail, the updater preserves the previous dataset rather than replacing it with text-only cards. Embedded videos remain subject to YouTube availability, regional restrictions, and publisher removal.

## Local preview
Open `index.html` directly in a browser. If the browser blocks loading `data/news.json` for `file://`, it automatically falls back to the built-in sample cards. For a more accurate preview, run:
```bash
python -m http.server 8000
```
Then visit `http://localhost:8000`.

## Current limitations and next steps
- User accounts and cloud-synced progress are not included; progress is stored in localStorage.
- Daily news refresh uses public official-channel video RSS feeds and does not require `OPENAI_API_KEY`. Free headline translation is best-effort; if unavailable, the English title and original video still work.
- RSS feeds and API availability may change. Review source links and AI-generated translations periodically.
- Add a licensed video provider/API to populate true daily video content; don't download or redistribute copyrighted videos/subtitles without permission.
- For full dictionary lookup, add a dictionary provider in a server-side function so API credentials are never exposed in the browser.
