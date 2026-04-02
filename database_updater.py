import os, time, json, requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import DATABASE_FILE # Uses your updated config!

session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries, pool_connections=10))

def fetch_with_retry(url, label="API", max_attempts=5):
    backoff = 1
    for attempt in range(1, max_attempts + 1):
        try:
            res = session.get(url, timeout=10)
            if res.status_code == 200:
                return res.json()
            if res.status_code == 429:
                retry_after = res.headers.get("Retry-After")
                wait = int(retry_after) if retry_after and retry_after.isdigit() else backoff
                print(f"⚠️ [{label}] Rate limited. Retrying in {wait}s...")
                time.sleep(wait)
            elif res.status_code == 404:
                return None
            else:
                print(f"⚠️ [{label}] Unexpected status {res.status_code} for {url}")
                time.sleep(backoff)
        except requests.RequestException as error:
            print(f"❌ [{label}] Network error: {error}. Retrying in {backoff}s...")
            time.sleep(backoff)
        backoff = min(backoff * 2, 30)
    print(f"❌ [{label}] Failed after {max_attempts} attempts: {url}")
    return None

def update_database():
    print("="*50 + "\n🔄 UPDATING ANIME DATABASE\n" + "="*50)
    
    db = {}
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            db = json.load(f)
            
    current_page = 1
    has_next_page = True
    
    while has_next_page:
        page_data = fetch_with_retry(f"https://api.jikan.moe/v4/anime?page={current_page}", f"Page-{current_page}")
        if not page_data or "data" not in page_data: break
            
        has_next_page = page_data.get("pagination", {}).get("has_next_page", False)
        
        for item in page_data["data"]:
            aid = str(item["mal_id"])
            print(f"  🌐 [UPDATING] ID {aid} ({item.get('title')})...")
            
            s_res = fetch_with_retry(f"https://api.jikan.moe/v4/anime/{aid}/statistics", "Stats")
            time.sleep(1) # Be nice to Jikan API
            if not s_res or "data" not in s_res: continue
                
            stats = s_res["data"]
            score_counts = [0] * 10
            for s in stats.get("scores", []):
                val = s.get("score")
                if 1 <= val <= 10: score_counts[10 - val] = s.get("votes")
            
            db[aid] = {
                "id": aid, "title": item.get("title"), 
                "picture": item.get("images", {}).get("jpg", {}).get("large_image_url"),
                "score_counts": score_counts, "trailer": item.get("trailer", {}).get("url"), 
                "synopsis": item.get("synopsis"),
                "watching": stats.get("watching", 0), "completed": stats.get("completed", 0), 
                "on_hold": stats.get("on_hold", 0), "dropped": stats.get("dropped", 0), 
                "plan": stats.get("plan_to_watch", 0),
                "genres": [{"id": g["mal_id"], "name": g["name"]} for g in item.get("genres", [])],
                "media_type": item.get("type"), "status": item.get("status")
            }
            
        temp_path = f"{DATABASE_FILE}.tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
        os.replace(temp_path, DATABASE_FILE)
        print(f"💾 Page {current_page} saved. Total records: {len(db)}")
        current_page += 1

if __name__ == "__main__":
    update_database()