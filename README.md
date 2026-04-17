# Anime Recommender Version 1.0

A self-hosted anime discovery engine built on MyAnimeList community data. Configure genre, theme, and demographic filters through an interactive UI; a Bayesian-weighted scoring algorithm ranks results by community engagement, approval rate, and drop-rate penalty — not just raw score.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Scoring Algorithm](#scoring-algorithm)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Data Pipeline](#data-pipeline)
- [Known Limitations](#known-limitations)
- [License](#license)

---

## Overview

MAL's own ranking system treats a score of 8.5 from 500 votes identically to a score of 8.5 from 500,000 votes. This project corrects that by applying a **Bayesian credibility adjustment** (borrowed from the Wikimedia and Letterboxd rating methodologies) combined with multi-signal engagement metrics to produce a more reliable composite ranking.

The application is entirely self-hosted and runs as a lightweight Python HTTP server — no framework, no database daemon, no cloud dependency.

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│                    Browser                       │
│  index.html · app.js · styles.css               │
│  - Genre filter UI with linked OR-group canvas   │
│  - Session via localStorage                      │
│  - Export to JSON                                │
└──────────────────────┬──────────────────────────┘
                       │ HTTP (JSON)
┌──────────────────────▼──────────────────────────┐
│              server.py (stdlib HTTPServer)        │
│  GET  /               → serve index.html         │
│  POST /api/login      → auth.py                  │
│  POST /api/register   → auth.py                  │
│  POST /api/recommend  → logic.py                 │
│  GET  /api/status     → uptime + db count        │
└────────────┬─────────────────────┬───────────────┘
             │                     │
┌────────────▼──────────┐ ┌───────▼───────────────┐
│       auth.py          │ │       logic.py          │
│  - werkzeug scrypt pw  │ │  - In-memory anime DB   │
│  - UUID email tokens   │ │  - Bayesian scoring     │
│  - Resend API email    │ │  - Genre/type filtering  │
│  - users_db.json       │ │  - MAL list exclusion    │
└───────────────────────┘ └───────────────────────┘
                                    │
                          ┌─────────▼──────────────┐
                          │  anime_database.json     │
                          │  Built by               │
                          │  database_updater.py     │
                          │  via Jikan API v4        │
                          └────────────────────────┘
```

---

## Features

**Discovery**
- Toggle-based genre, theme, format, demographic, and status filters
- Three-state button cycle: neutral → included → excluded
- CTRL+Drag to visually link two tags into an OR-group (rendered as a live SVG line)
- AND / OR global logic mode switch
- Configurable result count and minimum MAL score floor
- Optional MAL list integration — fetches the user's watched list via API and excludes already-seen titles
- Guests can discover without an account (MAL exclusion is auto-disabled)

**Results**
- Ranked cards showing algorithm match %, MAL score, synopsis, genre chips, and status
- Proportional stat bar: Watching / Completed / On Hold / Dropped / Planning
- Direct MAL link and trailer link per card
- Client-side search and sort (by algorithm match, MAL score, or community size)
- Export full results to JSON

**Authentication**
- Email/password registration with scrypt hashing (via Werkzeug)
- UUID-based email verification (Resend API or in-app fallback token)
- Persistent MAL credentials stored server-side per verified account
- Settings updates are rejected for unverified accounts

**Infrastructure**
- Zero-dependency HTTP server (Python `http.server`)
- Atomic JSON writes with `.tmp` swap to prevent data corruption
- `start.py` helper: venv creation, dependency install, database extraction, and cleanup
- Database compressed and bundled as `.gz` for distribution

---

## Scoring Algorithm

Each anime receives a **composite score** in [0, 1], computed as:

```
composite = w_score    × score_norm
          + w_approval × approval_ratio
          + w_engage   × engage_ratio
          - w_drop     × drop_ratio
```

**score_norm** is derived from a Bayesian credibility-weighted mean:

```
weighted_mean = (V / (V + K)) × mean_score
              + (K / (V + K)) × global_mean

score_norm = weighted_mean / 10.0
```

Where `V` = number of score votes, `K` = format-specific credibility threshold (TV: 5000, Movie: 3000, OVA/ONA: 1500, etc.), and `global_mean` = population average (default 7.64). Titles with few votes are pulled toward the global average rather than ranked on a potentially unrepresentative sample.

| Signal | Formula | Default Weight |
|---|---|---|
| Score | Bayesian-weighted mean / 10 | 0.55 |
| Approval | Fraction of votes ≥ 7 | 0.25 |
| Engagement | (watching + completed) / active users | 0.15 |
| Drop penalty | dropped / active users | −0.05 |

All weights are configurable via `.env` or the API payload.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, `http.server` (stdlib) |
| Auth | Werkzeug (scrypt hashing), UUID tokens |
| Email | Resend API (optional) |
| Data | Jikan API v4 (MAL unofficial), JSON flat-file |
| MAL Integration | MyAnimeList API v2 |
| Frontend | Vanilla JS (ES2020), HTML5, CSS3 |
| Fonts | Plus Jakarta Sans (Google Fonts) |

No framework. No ORM. No Docker required.

---

## Project Structure

```
anime-recommender/
├── frontend/
│   ├── index.html          # SPA shell; GENRE_MAP injected server-side
│   ├── app.js              # All UI logic, filter state, API calls
│   └── styles.css          # CSS custom properties, glassmorphism theme
│
├── auth.py                 # Registration, login, token verification
├── config.py               # Environment config, genre/theme ID map
├── database_updater.py     # Jikan API scraper → anime_database.json
├── logic.py                # Scoring engine, MAL list fetch, filter logic
├── server.py               # HTTP server, route dispatch
├── start.py                # Developer helper CLI
│
├── anime_database.json.gz  # Pre-built database (extract on install)
├── anime_database.json     # Extracted at runtime (gitignored)
├── users_db.json           # User accounts (gitignored in production)
│
├── .env.example            # Environment variable template
├── requirements.txt        # pip dependencies
└── README.md
```

---

## Quick Start

**Prerequisites:** Python 3.10+, `pip` in your PATH.

### Option A — Automated (recommended)

```bash
git clone https://github.com/yourname/anime-recommender.git
cd anime-recommender
cp .env.example .env
python start.py install
python start.py run
```

The browser opens automatically at `http://localhost:8080`.

### Option B — Manual

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

python -c "import gzip, shutil; shutil.copyfileobj(gzip.open('anime_database.json.gz','rb'), open('anime_database.json','wb'))"

python server.py
```

### Helper Commands

| Command | Description |
|---|---|
| `python start.py install` | Create venv, install deps, extract DB |
| `python start.py run` | Start the server |
| `python start.py update-db` | Re-scrape Jikan API (hours, rate-limited) |
| `python start.py clean` | Remove venv, cache, and extracted DB |

---

## Configuration

Copy `.env.example` to `.env`:

```env
PORT=8080
SITE_URL=http://localhost:8080

# MyAnimeList API — for MAL list exclusion (optional)
MAL_CLIENT_ID=your_client_id
MAL_USERNAME=your_username

# Resend email API — for verification emails (optional)
# If unset, verification tokens are shown directly in the UI
RESEND_API_KEY=your_resend_key
```

All variables are optional. The app is fully functional without a MAL API key or Resend key — verification tokens surface in the UI when email delivery is unavailable.

To get a MAL Client ID: visit [myanimelist.net/apiconfig](https://myanimelist.net/apiconfig) and register an application.

---

## API Reference

All endpoints accept and return `application/json`.

### `POST /api/register`
```json
{
  "email": "user@gmail.com",
  "password": "mypassword",
  "mal_user": "optional_mal_username",
  "mal_api":  "optional_client_id"
}
```
Returns `200 { "message": "..." }`. If email delivery is unavailable, the response also includes `"token": "<uuid>"` for manual verification.

### `POST /api/verify_manual`
```json
{ "token": "uuid-verification-token" }
```
Returns `200` on success, `400` if the token is invalid or already consumed.

### `POST /api/login`
```json
{ "email": "user@gmail.com", "password": "mypassword" }
```
Returns `200 { "message": "...", "mal_user": "...", "mal_api": "..." }`.

### `POST /api/settings`
Requires a registered, verified account. Updates MAL credentials server-side.
```json
{ "email": "user@gmail.com", "mal_user": "username", "mal_api": "client_id" }
```

### `POST /api/recommend`
```json
{
  "included":      [1, 4],
  "excluded":      [12],
  "linked_groups": [[22, 8]],
  "logic_mode":    "and",
  "top_x":         10,
  "min_score":     7.0,
  "exclude_mal":   true,
  "mal_user":      "optional",
  "mal_api":       "optional"
}
```
Returns a ranked array of anime objects. Does not require authentication.

### `GET /api/status`
Returns server uptime, version, database entry count, and configured site URL.

---

## Data Pipeline

`anime_database.json.gz` was built by `database_updater.py`, which:

1. Paginates through all anime on Jikan API v4 (`/v4/anime?page=N`)
2. Fetches per-title statistics (`/v4/anime/{id}/statistics`) for score distributions
3. Stores watching / completed / on-hold / dropped / plan-to-watch counts, genre lists, synopsis, cover image, and trailer URL
4. Saves atomically after each page (`.tmp` swap) so a partial run can be safely resumed

To rebuild from scratch (several hours due to Jikan's rate limits):
```bash
python start.py update-db
```

---

## Known Limitations

- **Database staleness** — The bundled database is a static snapshot. Newly airing titles require running `update-db`.
- **Single-threaded server** — `http.server` is not suitable for concurrent users. Wrap with Gunicorn or migrate to an ASGI framework for production.
- **Flat-file auth** — `users_db.json` does not scale beyond a small number of users. SQLite or PostgreSQL would be the appropriate next step.
- **No server-side session tokens** — The `/api/settings` endpoint trusts the client-supplied email. This is acceptable for a local deployment; a production version should issue signed session tokens on login.
- **MAL list latency** — Large MAL lists (1000+ entries) add a few seconds of fetch time per recommendation request.

---

## License

MIT License — see `LICENSE` for details.
