from flask import Flask, render_template, request, jsonify
import random
import string
import requests
import time
from threading import Thread

app = Flask(__name__)

SPOTIFY_API_URL = "https://spclient.wg.spotify.com/signup/public/v1/account"

def generate_email():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + "@vel0x0.xyz"

def create_spotify_account(email, password):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "account_details": {
            "birthdate": "1990-01-01",
            "country": "JP",
            "display_name": email.split("@")[0],
            "email": email,
            "password": password,
            "password_confirm": password,
            "gender": "male"
        },
        "callback_state": "spotify",
        "agreed_to_terms": True,
        "marketing_opt_in": False
    }
    try:
        response = requests.post(SPOTIFY_API_URL, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return True, email, password
        else:
            return False, email, password
    except:
        return False, email, password

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    count = int(request.form.get("count", 1))
    results = []

    def worker():
        for _ in range(count):
            email = generate_email()
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
            success, acc_email, acc_pass = create_spotify_account(email, password)
            results.append({
                "email": acc_email,
                "password": acc_pass,
                "status": "Success" if success else "Failed"
            })
            time.sleep(2)

    thread = Thread(target=worker)
    thread.start()
    thread.join()

    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)