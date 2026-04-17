import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("MAL_CLIENT_ID", "")
USERNAME = os.getenv("MAL_USERNAME", "")
PORT = int(os.getenv("PORT", "8080"))
SITE_URL = os.getenv("SITE_URL", f"http://localhost:{PORT}")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
DATABASE_FILE = "anime_database.json"
USER_DB_FILE = "users_db.json"
ALLOWED_DOMAINS = ["gmail.com", "outlook.com", "yahoo.com", "proton.me", "icloud.com"]

# --- SCORING CONFIGURATION ---
GLOBAL_MEAN = 7.64
SCORE_WEIGHTS = {
    "score": 0.55,
    "approval": 0.25,
    "engage": 0.15,
    "drop": 0.05
}

GENRE_MAP = {
    "Format (Type)": {
        "TV Series": "type_tv", "Movie": "type_movie", "OVA": "type_ova",
        "ONA": "type_ona", "Special": "type_special"
    },
    "Status": {
        "Airing": "status_currently_airing",
        "Completed": "status_finished_airing",
        "Upcoming": "status_not_yet_aired"
    },
    "Genres": {
        "Action": 1, "Adventure": 2, "Avant Garde": 5, "Award Winning": 46,
        "Boys Love": 28, "Comedy": 4, "Drama": 8, "Fantasy": 10,
        "Girls Love": 26, "Gourmet": 47, "Horror": 14, "Mystery": 7,
        "Romance": 22, "Sci-Fi": 24, "Slice of Life": 36, "Sports": 30,
        "Supernatural": 37, "Suspense": 41
    },
    "Explicit": {
        "Ecchi": 9, "Erotica": 49, "Hentai": 12
    },
    "Themes": {
        "Adult Cast": 50, "Anthropomorphic": 51, "CGDCT": 52, "Childcare": 53,
        "Combat Sports": 54, "Crossdressing": 81, "Delinquents": 55,
        "Detective": 39, "Educational": 56, "Gag Humor": 57, "Gore": 58,
        "Harem": 35, "High Stakes Game": 59, "Historical": 13,
        "Idols (Female)": 60, "Idols (Male)": 61, "Isekai": 62,
        "Iyashikei": 63, "Love Polygon": 64, "Love Status Quo": 65,
        "Magical Sex Shift": 200, "Mahou Shoujo": 66,  # BUG FIX: were both 66
        "Martial Arts": 17, "Mecha": 18, "Medical": 67, "Military": 38,
        "Music": 19, "Mythology": 6, "Organized Crime": 68, "Otaku Culture": 69,
        "Parody": 20, "Performing Arts": 70, "Pets": 71, "Psychological": 40,
        "Racing": 3, "Reincarnation": 72, "Reverse Harem": 73, "Samurai": 21,
        "School": 23, "Showbiz": 74, "Space": 29, "Strategy Game": 11,
        "Super Power": 31, "Survival": 75, "Team Sports": 76,
        "Time Travel": 77, "Urban Fantasy": 78, "Vampire": 32,
        "Video Game": 79, "Villainess": 82, "Visual Arts": 80, "Workplace": 48
    },
    "Demographics": {
        "Josei": 43, "Kids": 15, "Seinen": 42, "Shoujo": 25, "Shounen": 27
    }
}
