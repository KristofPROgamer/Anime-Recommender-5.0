import gzip
import shutil
import subprocess
import sys
from pathlib import Path

PYTHON = Path(sys.executable)
VENV = Path("venv") if Path("venv").exists() else Path(".venv") if Path(".venv").exists() else Path("venv")
VENV_BIN = VENV / ("Scripts" if sys.platform.startswith("win") else "bin")
VENV_PYTHON = VENV_BIN / ("python.exe" if sys.platform.startswith("win") else "python")
VENV_PIP = VENV_BIN / ("pip.exe" if sys.platform.startswith("win") else "pip")

DB_COMPRESSED = Path("anime_database.json.gz")
DB_JSON = Path("anime_database.json")


def run(command):
    subprocess.check_call(command, shell=False)


def create_venv():
    if not VENV_PYTHON.exists():
        print("[1/3] Creating virtual environment...")
        run([PYTHON, "-m", "venv", str(VENV)])
    else:
        print("[1/3] Virtual environment already exists.")


def install():
    create_venv()
    print("[2/3] Installing dependencies...")
    python_exec = get_python_executable()
    ensure_pip_installed(python_exec)
    pip_cmd = [str(python_exec), "-m", "pip"]

    run(pip_cmd + ["install", "--upgrade", "pip"])

    if Path("requirements.txt").exists():
        run(pip_cmd + ["install", "-r", "requirements.txt"])
    elif Path("pyproject.toml").exists():
        run(pip_cmd + ["install", "."])
    else:
        print("⚠️ No dependency manifest found. Skipping package installation.")

    print("[3/3] Handling database...")
    if DB_COMPRESSED.exists():
        with gzip.open(DB_COMPRESSED, "rb") as f_in:
            with open(DB_JSON, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        print("✅ Database extracted and ready.")
    else:
        print("⚠️ Compressed database not found.")


def get_python_executable():
    if VENV_PYTHON.exists():
        return VENV_PYTHON
    return PYTHON


def ensure_pip_installed(python_exec):
    try:
        run([str(python_exec), "-m", "pip", "--version"])
    except subprocess.CalledProcessError:
        print("[2/3] Bootstrapping pip into the virtual environment...")
        run([str(python_exec), "-m", "ensurepip", "--upgrade"])


def run_server():
    print("🚀 Starting server...")
    run([str(get_python_executable()), "server.py"])


def update_db():
    print("🔄 Starting full database scrape...")
    run([str(get_python_executable()), "database_updater.py"])


def clean():
    print("🧹 Cleaning up...")

    pycache = Path("__pycache__")
    if pycache.exists():
        shutil.rmtree(pycache, ignore_errors=True)

    if VENV.exists():
        shutil.rmtree(VENV, ignore_errors=True)

    if DB_JSON.exists():
        DB_JSON.unlink()

    print("✅ Clean complete.")


def help():
    print("Anime Recommender 5.0 - Local developer helper")
    print("Available commands:")
    print("  install    - Setup a virtual environment, install dependencies, and extract the database")
    print("  run        - Start the web server inside the virtual environment")
    print("  update-db  - Refresh the anime database from Jikan API")
    print("  clean      - Remove temporary files, venv, and extracted database")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        help()
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
        help()