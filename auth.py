import json
import os
import re
import time
import uuid
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from config import USER_DB_FILE, ALLOWED_DOMAINS, PORT, SITE_URL, RESEND_API_KEY

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
MIN_PASSWORD_LENGTH = 8

def load_users():
    """Loads users from the JSON database, gracefully handling empty or corrupted files."""
    if not os.path.exists(USER_DB_FILE):
        return {}
    try:
        with open(USER_DB_FILE, 'r') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError as e:
        backup_name = f"{USER_DB_FILE}.corrupt.{int(time.time())}"
        os.rename(USER_DB_FILE, backup_name)
        print(f"⚠️ [AUTH-DB] Warning: {USER_DB_FILE} is corrupted. Backed up to {backup_name}. Starting fresh.")
        return {}

def save_users(users):
    temp_file = USER_DB_FILE + '.tmp'
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4)
    os.replace(temp_file, USER_DB_FILE)
    print(f"💾 [AUTH-DB] Database successfully updated on disk.")

def verify_token(token):
    print(f"\n🔍 [AUTH-VERIFY] Attempting to verify token: {token}")
    users = load_users()
    for email, data in users.items():
        if data.get("token") == token:
            print(f"✅ [AUTH-VERIFY] Token matched for user: {email}. Marking as verified.")
            users[email]["verified"] = True
            users[email]["token"] = None
            save_users(users)
            return True
    
    print(f"❌ [AUTH-VERIFY] Token verification failed. No matching token found.")
    return False

def register_user(email, password, mal_user="", mal_api=""):
    print(f"\n" + "="*50)
    print(f"📝 [AUTH-REGISTER] New registration request initialized.")
    print(f"👤 [AUTH-REGISTER] Target Email: {email}")
    print(f"🔗 [AUTH-REGISTER] Linked MAL User: '{mal_user}'")
    print(f"🔑 [AUTH-REGISTER] Linked API Key length: {len(mal_api)} characters")
    
    email = (email or "").strip().lower()
    password = password or ""
    if not EMAIL_REGEX.match(email):
        return {"error": "Please use a valid email address."}, 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return {"error": f"Password must be at least {MIN_PASSWORD_LENGTH} characters."}, 400

    domain = email.split('@')[-1] if '@' in email else ""
    if domain not in ALLOWED_DOMAINS:
        print(f"❌ [AUTH-REGISTER] Registration blocked. Domain '{domain}' is not reputable.")
        return {"error": "Please use a reputable email provider (Gmail, Outlook, etc.)"}, 400

    users = load_users()
    if email in users:
        print(f"❌ [AUTH-REGISTER] Registration blocked. Email '{email}' already exists.")
        return {"error": "Email already registered."}, 400
        
    print(f"🔒 [AUTH-REGISTER] Hashing password securely...")
    hashed_password = generate_password_hash(password)
    verification_token = str(uuid.uuid4())
    print(f"🎫 [AUTH-REGISTER] Generated Verification Token: {verification_token}")

    users[email] = {
        "password": hashed_password, 
        "mal_user": mal_user.strip(), 
        "mal_api": mal_api.strip(), 
        "verified": False, 
        "token": verification_token
    } 
    save_users(users)
    print(f"✅ [AUTH-REGISTER] User data saved to memory successfully.")
    
    # Resend Email Logic
    resend_api_key = RESEND_API_KEY
    verify_link = f"{SITE_URL}/?token={verification_token}"
    fallback_token = None
    
    if not resend_api_key:
        print(f"⚠️ [AUTH-EMAIL] No RESEND_API_KEY configured. Skipping email delivery.")
        fallback_token = verification_token
    else:
        print(f"📧 [AUTH-EMAIL] Dispatching verification email via Resend API to {email}...")
        try:
            response = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {resend_api_key}"},
                json={
                    "from": "onboarding@resend.dev",
                    "to": email,
                    "subject": "Verify your Anime Recommender Account",
                    "html": f"""
                    <div style="font-family: sans-serif; text-align: center; padding: 20px;">
                        <h2>Welcome to Anime Recommender!</h2>
                        <p>Click the button below to verify your account, or copy the token manually.</p>
                        <a href='{verify_link}' style="background: #6366f1; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a>
                        <br><br>
                        <p style="color: #666; font-size: 14px;">Or paste this token directly into the app:</p>
                        <code style="background: #eee; padding: 5px; border-radius: 4px; font-weight: bold;">{verification_token}</code>
                    </div>
                    """
                }
            )
            if response.status_code in [200, 201]:
                print(f"✅ [AUTH-EMAIL] Email sent successfully! Payload: {response.json()}")
            else:
                fallback_token = verification_token
                print(f"⚠️ [AUTH-EMAIL] Email API responded with non-200 code: {response.status_code} - {response.text}")
        except Exception as e:
            fallback_token = verification_token
            print(f"❌ [AUTH-EMAIL] CRITICAL FAILURE sending email: {e}")
        
    print("="*50 + "\n")
    payload = {"message": "Registered! Please check your email to verify."}
    if fallback_token:
        payload["token"] = fallback_token
        payload["message"] = "Registered! Email delivery failed, please verify with the token below."
    return payload, 200

def login_user(email, password):
    email = (email or "").strip().lower()
    password = password or ""
    print(f"\n🔐 [AUTH-LOGIN] Login attempt for: {email}")
    users = load_users()
    user = users.get(email)

    if not user:
        print(f"❌ [AUTH-LOGIN] Failed: User '{email}' not found in database.")
        return {"error": "Invalid email or password."}, 401

    if not check_password_hash(user.get("password", ""), password):
        print(f"❌ [AUTH-LOGIN] Failed: Incorrect password for '{email}'.")
        return {"error": "Invalid email or password."}, 401
        
    if not user.get("verified", False):
        print(f"⚠️ [AUTH-LOGIN] Denied: User '{email}' has not verified their email.")
        return {"error": "Please verify your email first!"}, 403
        
    print(f"✅ [AUTH-LOGIN] Success! User '{email}' authenticated and fully verified.")
    return {
        "message": "Logged in successfully!",
        "mal_user": user.get("mal_user", ""),
        "mal_api": user.get("mal_api", "")
    }, 200

def update_settings(email, mal_user, mal_api):
    email = (email or "").strip().lower()
    print(f"\n⚙️ [AUTH-SETTINGS] Settings update requested for {email}")
    users = load_users()
    if email in users:
        users[email]['mal_user'] = mal_user
        users[email]['mal_api'] = mal_api
        save_users(users)
        print(f"✅ [AUTH-SETTINGS] Successfully updated MAL credentials for {email}.")
        return True
        
    print(f"❌ [AUTH-SETTINGS] Failed: User {email} not found.")
    return False