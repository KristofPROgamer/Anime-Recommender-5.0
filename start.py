"""
Anime Recommender v1.0 — Developer Helper Script
Usage: python start.py [install | run | update-db | clean]
"""

import gzip
import shutil
import subprocess
import sys
from pathlib import Path

PYTHON = Path(sys.executable)
VENV = Path("venv") if Path("venv").exists() else Path(".venv") if Path(".venv").exists() else Path("venv")
VENV_BIN = VENV / ("Scripts" if sys.platform.startswith("win") else "bin")
VENV_PYTHON = VENV_BIN / ("python.exe" if sys.platform.startswith("win") else "python")

DB_COMPRESSED = Path("anime_database.json.gz")
DB_JSON = Path("anime_database.json")


def run(command):
    subprocess.check_call(command, shell=False)


def get_python_executable() -> Path:
    return VENV_PYTHON if VENV_PYTHON.exists() else PYTHON


def ensure_pip_installed(python_exec: Path):
    try:
        run([str(python_exec), "-m", "pip", "--version"])
    except subprocess.CalledProcessError:
        print("Bootstrapping pip...")
        run([str(python_exec), "-m", "ensurepip", "--upgrade"])


def install():
    # 1. Virtual environment
    if not VENV_PYTHON.exists():
        print("[1/3] Creating virtual environment...")
        run([PYTHON, "-m", "venv", str(VENV)])
    else:
        print("[1/3] Virtual environment already exists.")

    # 2. Dependencies
    python_exec = get_python_executable()
    ensure_pip_installed(python_exec)
    pip = [str(python_exec), "-m", "pip"]

    print("[2/3] Installing dependencies...")
    run(pip + ["install", "--upgrade", "pip", "--quiet"])

    if Path("requirements.txt").exists():
        run(pip + ["install", "-r", "requirements.txt", "--quiet"])
    elif Path("pyproject.toml").exists():
        run(pip + ["install", ".", "--quiet"])
    else:
        print("  ⚠️  No dependency manifest found. Skipping.")

    # 3. Database
    print("[3/3] Preparing anime database...")
    if DB_JSON.exists():
        print("  ✅ Database already extracted.")
    elif DB_COMPRESSED.exists():
        print("  📦 Extracting anime_database.json.gz ...")
        try:
            with gzip.open(DB_COMPRESSED, "rb") as f_in, open(DB_JSON, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
            print("  ✅ Database extracted successfully.")
        except Exception as e:
            print(f"  ❌ Extraction failed: {e}")
            sys.exit(1)
    else:
        print("  ⚠️  No compressed database found. Run 'update-db' to build one from scratch.")

    print("\n✅ Setup complete. Run: python start.py run")


def run_server():
    print("🚀 Starting Anime Recommender v1.0...")
    run([str(get_python_executable()), "server.py"])


def update_db():
    print("🔄 Starting full database update from Jikan API...")
    print("   This may take several hours for a full scrape.")
    run([str(get_python_executable()), "database_updater.py"])


def clean():
    print("🧹 Cleaning up project artifacts...")
    for path in [Path("__pycache__"), VENV]:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
            print(f"  Removed {path}/")
    if DB_JSON.exists():
        DB_JSON.unlink()
        print(f"  Removed {DB_JSON}")
    print("✅ Clean complete.")


def help_text():
    print("Anime Recommender v1.0 — Local Helper Script")
    print()
    print("Commands:")
    print("  install     Create venv, install dependencies, extract database")
    print("  run         Start the web server")
    print("  update-db   Refresh the anime database from Jikan API")
    print("  clean       Remove venv, cache, and extracted database")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        help_text()
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "install":
        install()
    elif cmd == "run":
        run_server()
    elif cmd == "update-db":
        update_db()
    elif cmd == "clean":
        clean()
    else:
        print(f"Unknown command: '{cmd}'")
        print()
        help_text()
        sys.exit(1)
