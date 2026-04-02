# Anime-Recommender-5.0

A local anime recommendation web app with user registration, email verification, and genre-based discovery.

## Features

- User registration and verification
- Genre-based anime discovery
- Local JSON-backed storage
- Optional email delivery support
- Easy local setup with a helper script
- Built-in admin account for local access

## Screenshots

<p align="center">
  <img src="FrontPage.png" width="48%" alt="Front page" />
  <img src="SearchResults.png" width="48%" alt="Search results" />
</p>

## Default Admin Account

A built-in admin account is available for local testing:

- **Username:** `admin`
- **Password:** `adminadmin`

## Requirements

- Python 3.10+
- Dependencies from `requirements.txt` or `pyproject.toml`

## Quick Start

## Starter script recommended for easy install (see down bellow a bit)

### 1) Copy environment variables

**Windows (Command Prompt):**
```bash
copy .env.example .env
````

**PowerShell / macOS / Linux:**

```bash
cp .env.example .env
```

### 2) Install dependencies

Using `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

Or install the package directly:

```bash
python -m pip install .
```

### 3) Start the app

```bash
python server.py
```

Or use the helper script:

```bash
python start.py install
python start.py run
```

### 4) Open the app

If the browser does not open automatically, visit:

```text
http://localhost:8080
```

## Starter Script

The `start.py` script handles common local development tasks.

### Available commands

```bash
python start.py install
python start.py run
python start.py update-db
python start.py clean
```

### What they do

* `install`
  Creates a virtual environment, installs dependencies, and extracts `anime_database.json.gz` if it exists.

* `run`
  Starts the web server inside the virtual environment.

* `update-db`
  Refreshes the anime database from the API.

* `clean`
  Removes temporary files, the virtual environment, and the extracted database.

## Environment Variables

Optional configuration:

| Variable         | Description                             |
| ---------------- | --------------------------------------- |
| `PORT`           | HTTP port override                      |
| `MAL_CLIENT_ID`  | Default MAL API client ID               |
| `MAL_USERNAME`   | Default MAL username for list exclusion |
| `RESEND_API_KEY` | Optional email delivery key             |
| `SITE_URL`       | Base URL used in verification links     |

## Data Files

These files are created and updated automatically:

* `users_db.json`
* `anime_database.json`

If `anime_database.json.gz` exists, it is extracted automatically during setup.

## Project Structure

```text
.
├── frontend/
│   ├── app.js
│   ├── index.html
│   └── styles.css
├── .env.example
├── LICENSE
├── anime_database.json.gz
├── auth.py
├── config.py
├── database_updater.py
├── logic.py
├── server.py
├── start.py
├── users_db.json
├── requirements.txt
├── pyproject.toml
├── .gitignore
├── FrontPage.png
└── SearchResults.png
```

## Notes

* If email delivery is unavailable, the verification token is returned in the registration response.
* This project is intended for local development and testing.

## License

This project is licensed under the MIT License.

