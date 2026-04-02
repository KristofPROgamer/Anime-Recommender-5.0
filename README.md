````md
# MAL Rater Stats

A local anime recommendation web app with user registration, email verification, and genre-based discovery.

This project is currently in active development and the public repo is meant to show the architecture, workflow, and core functionality.

## Features

- User registration and verification
- Local user storage
- Anime database extraction from compressed data
- Genre-based discovery and scoring logic
- Helper script for setup, cleanup, and running the app
- Environment-based configuration for local development

## Requirements

- Python 3.10+
- Dependencies from `requirements.txt` or `pyproject.toml`

## Repository Structure

- `frontend/` — frontend code
- `server.py` — main web server
- `start.py` — local helper script for setup and running
- `logic.py` — scoring and recommendation logic
- `auth.py` — registration and verification flow
- `database_updater.py` — database refresh script
- `config.py` — configuration values
- `anime_database.json.gz` — compressed anime database
- `.env.example` — example environment variables

## Run Locally

### 1. Copy environment variables

Windows Command Prompt:
```bat
copy .env.example .env
````

PowerShell:

```powershell
cp .env.example .env
```

### 2. Install dependencies

Using requirements:

```bash
python -m pip install -r requirements.txt
```

Or install the project package:

```bash
python -m pip install .
```

### 3. Start the app

Run the server directly:

```bash
python server.py
```

Or use the helper script:

```bash
python start.py install
python start.py run
```

If the browser does not open automatically, visit:

```text
http://localhost:8080
```

## Environment Variables

Optional configuration:

* `PORT` — HTTP port override
* `MAL_CLIENT_ID` — MyAnimeList API client ID
* `MAL_USERNAME` — MyAnimeList username used for list exclusion
* `RESEND_API_KEY` — optional email delivery key
* `SITE_URL` — base URL used in verification links

## Notes

* `anime_database.json` is extracted locally from `anime_database.json.gz`.
* `users_db.json` is created and updated automatically at runtime.
* If email delivery is unavailable, the verification token is returned in the registration response.
* This repository is a work in progress and will continue to be updated.

## License

This project is licensed under the MIT License.

```

One small improvement: later, add a `Screenshots` section and a `Roadmap` section. That will make it look much more complete.
```
