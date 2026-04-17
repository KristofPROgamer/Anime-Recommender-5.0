import time
import json
import requests
import os
from config import CLIENT_ID, USERNAME, DATABASE_FILE


def load_database():
    if not os.path.exists(DATABASE_FILE):
        print(f"⚠️  Warning: Database file '{DATABASE_FILE}' not found!")
        return {}
    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ CRITICAL: Database JSON is corrupted: {e}")
        return {}


ANIME_DB = load_database()
print(f"📦 Database loaded: {len(ANIME_DB)} entries ready.")


def fetch_user_mal_list(username, api_key):
    """
    Fetch the user's full MAL list to exclude already-seen titles from recommendations.
    Returns a set of anime IDs. Returns an empty set on any error or if credentials are absent.
    """
    if not username or not api_key:
        return set()

    print(f"🔍 Fetching MAL list for: {username}")
    user_ids = set()
    url = f"https://api.myanimelist.net/v2/users/{username}/animelist"
    headers = {"X-MAL-CLIENT-ID": api_key}
    params = {"limit": 1000, "fields": "list_status"}

    try:
        while url:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                print(f"⚠️  MAL API error {response.status_code}: {response.text}")
                break

            data = response.json()
            for item in data.get("data", []):
                user_ids.add(item["node"]["id"])

            # Pagination: the next URL already embeds all required params
            url = data.get("paging", {}).get("next")
            params = {}

        print(f"✅ Fetched {len(user_ids)} entries from {username}'s list.")
        return user_ids
    except Exception as e:
        print(f"❌ Error fetching MAL list: {e}")
        return set()


def compute_anime_score(watching, completed, on_hold, dropped, plan, score_counts,
                        media_type="Unknown", global_mean=7.64,
                        w_score=0.55, w_approval=0.25, w_engage=0.15, w_drop=0.05):
    """
    Compute a normalised composite score in [0, 1] for a single title.

    Score signals
    -------------
    score_norm    : Bayesian credibility-weighted mean, normalised to [0, 1].
    approval_ratio: Fraction of votes that scored 7 or above.
    engage_ratio  : (watching + completed) / all active users.
    drop_ratio    : dropped / all active users (penalty term).

    Bayesian weight
    ---------------
    weighted_mean = (V / (V + K)) * mean + (K / (V + K)) * global_mean

    where V = number of score votes and K is a format-specific credibility threshold.
    Titles with few votes are pulled toward the global average rather than ranked
    purely on a potentially unrepresentative sample.

    Parameters
    ----------
    score_counts : list of 10 ints, DESCENDING order.
        Index 0 = count of score-10 votes, index 9 = count of score-1 votes.
        This matches the storage convention used by database_updater.py.
        Reversing the order would corrupt both mean_score and approval_ratio.
    """
    k_thresholds = {
        "TV": 5000, "Movie": 3000, "OVA": 1500, "ONA": 1500,
        "Special": 1000, "TV Special": 1000, "Music": 300,
        "PV": 300, "Unknown": 1000
    }

    clean_media_type = str(media_type).strip() if media_type else "Unknown"
    k = k_thresholds.get(clean_media_type, 1000)

    active_users = watching + completed + on_hold + dropped
    if active_users == 0:
        return 0.0, 0.0

    votes = sum(score_counts)
    if votes > 0:
        # score_counts[i] is the vote count for score (10 - i), so index 0 = score 10.
        mean_score = sum((10 - i) * score_counts[i] for i in range(10)) / votes
        weighted_score = (votes / (votes + k)) * mean_score + (k / (votes + k)) * global_mean
        score_norm = weighted_score / 10.0

        # Approval: fraction of votes for scores 7–10 (indices 0–3 in descending order).
        approval_votes = sum(score_counts[i] for i in range(4))
        approval_ratio = approval_votes / votes
    else:
        score_norm, approval_ratio, mean_score = 0.0, 0.0, 0.0

    engage_ratio = (watching + completed) / active_users
    drop_ratio = dropped / active_users

    composite = (
        (w_score    * score_norm)
      + (w_approval * approval_ratio)
      + (w_engage   * engage_ratio)
      - (w_drop     * drop_ratio)
    )

    return max(0.0, min(1.0, composite)), mean_score


def is_candidate_valid(anime_data, included, excluded, linked_groups, logic_mode):
    """Return True if the anime passes all active inclusion/exclusion filters."""
    a_genres = [g.get('id') for g in anime_data.get('genres', [])]
    a_type   = "type_"   + str(anime_data.get('media_type', '')).strip().lower().replace(' ', '_')
    a_status = "status_" + str(anime_data.get('status',     '')).strip().lower().replace(' ', '_')

    # 1. Absolute exclusions — any match disqualifies immediately.
    for ex in excluded:
        if isinstance(ex, int) and ex in a_genres:        return False
        if isinstance(ex, str) and ex in (a_type, a_status): return False

    # 2. Standalone inclusions.
    if logic_mode == 'and':
        for inc in included:
            if isinstance(inc, int) and inc not in a_genres:            return False
            if isinstance(inc, str) and inc not in (a_type, a_status):  return False

    elif logic_mode == 'or' and (included or linked_groups):
        all_reqs = included + [item for group in linked_groups for item in group]
        passed = any(
            (isinstance(r, int) and r in a_genres) or
            (isinstance(r, str) and r in (a_type, a_status))
            for r in all_reqs
        )
        if not passed:
            return False

    # 3. Linked OR-groups — each group must have at least one match.
    if logic_mode == 'and':
        for group in linked_groups:
            if not any(
                (isinstance(r, int) and r in a_genres) or
                (isinstance(r, str) and r in (a_type, a_status))
                for r in group
            ):
                return False

    return True


def process_recommendations(included, excluded, linked_groups, top_x, exclude_mal,
                             min_score, logic_mode, global_mean,
                             w_score, w_approval, w_engage, w_drop,
                             mal_user=None, mal_api=None):
    results = []

    # Fetch the user's MAL list to exclude titles they've already seen.
    user_ids = set()
    if exclude_mal:
        target_user = mal_user if mal_user else USERNAME
        target_api  = mal_api  if mal_api  else CLIENT_ID
        user_ids = fetch_user_mal_list(target_user, target_api)

    for str_aid, anime_data in ANIME_DB.items():
        aid = int(str_aid)

        if aid in user_ids:
            continue

        if not is_candidate_valid(anime_data, included, excluded, linked_groups, logic_mode):
            continue

        score, mean_score = compute_anime_score(
            anime_data.get("watching",  0),
            anime_data.get("completed", 0),
            anime_data.get("on_hold",   0),
            anime_data.get("dropped",   0),
            anime_data.get("plan",      0),
            anime_data.get("score_counts", [0] * 10),
            media_type=anime_data.get("media_type", "Unknown"),
            global_mean=global_mean,
            w_score=w_score, w_approval=w_approval,
            w_engage=w_engage, w_drop=w_drop,
        )

        if mean_score >= min_score:
            entry = anime_data.copy()
            entry["score"]         = score
            entry["raw_mean_score"] = mean_score
            results.append(entry)

    results.sort(key=lambda x: x["score"], reverse=True)
    print(f"✅ {len(results)} valid matches found. Returning top {top_x}.")
    return results[:top_x]
