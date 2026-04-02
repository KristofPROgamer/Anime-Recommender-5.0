# MAL Rater Stats

A local anime recommendation web app with user registration, verification, and genre-based discovery.

## Requirements
- Python 3.10+
- dependencies installed from `requirements.txt` or `pyproject.toml`

## Run locally
1. Copy example environment variables:
   ```bash
   copy .env.example .env
   ```
   or on PowerShell:
   ```powershell
   cp .env.example .env
   ```
2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
   or, if you prefer package install:
   ```bash
   python -m pip install .
   ```
3. Start the app:
   ```bash
   python server.py
   ```
   or use the helper script:
   ```bash
   python start.py install
   python start.py run
   ```
4. Open the browser if it does not open automatically:
   ```bash
   http://localhost:8080
   ```

## Environment variables
Optional configuration:
- `PORT` — HTTP port override
- `MAL_CLIENT_ID` — default MAL API client ID
- `MAL_USERNAME` — default MAL username for list exclusion
- `RESEND_API_KEY` — optional email delivery key
- `SITE_URL` — launch URL used in verification links

## Notes
- `users_db.json` and `anime_database.json` are created and updated automatically.
- If email delivery is unavailable, the verification token is returned in the registration response.

