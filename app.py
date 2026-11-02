import os
import random
import string
import time
import shutil
import tempfile
import setuptools
import requests
from flask import Flask, render_template_string, request, Response

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 内部で動いている websockify (noVNC) のポート
NOVNC_INTERNAL_PORT = 6080

# --- Flaskを通じた noVNC のリバースプロキシ（iframeやWebSocket用） ---
@app.route('/websockify', methods=['GET'])
@app.route('/vnc.html', methods=['GET'])
@app.route('/vnc_lite.html', methods=['GET'])
@app.route('/app/<path:subpath>', methods=['GET', 'POST'])
@app.route('/core/<path:subpath>', methods=['GET', 'POST'])
@app.route('/vendor/<path:subpath>', methods=['GET', 'POST'])
def proxy_novnc(subpath=""):
    target_url = f"http://localhost:{NOVNC_INTERNAL_PORT}{request.full_path}"
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=10
        )
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        return Response(resp.content, resp.status_code, headers)
    except Exception as e:
        return f"VNC Proxy Error: {str(e)}", 502

# --- パスワード生成 (10文字以上、大文字1つ以上、'.'を1つ以上含む) ---
def generate_secure_password():
    lower_digits = string.ascii_lowercase + string.digits
    base = ''.join(random.choice(lower_digits) for _ in range(10))
    pw_list = list(base)
    pw_list[0] = random.choice(string.ascii_uppercase)
    pw_list[1] = '.'
    random.shuffle(pw_list)
    return ''.join(pw_list)

# --- クラウドブラウザによる自動入力処理（インスタンス即死完全対策） ---
def generate_spotify_account_web():
    letters = string.ascii_lowercase + string.digits
    email = f"{''.join(random.choice(letters) for _ in range(10))}@vel0x0.xyz"
    password = generate_secure_password()
    
    options = Options()
    # --- コンテナ環境専用の強力な起動引数（Instance Exited防止） ---
    options.add_argument("--headless=new")  # 一旦ヘッドレスで確実に立ち上げてから画面に反映させるか、安定性を重視
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")  # 共有メモリ不足対策（必須）
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--no-zygote")
    options.add_argument("--single-process")          # コンテナ特有のプロセス即死を防ぐ最終防衛ライン
    options.add_argument("--disable-accelerated-2d-canvas")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--window-size=1280,720")
    
    options.binary_location = "/usr/bin/chromium"
    os.environ["DISPLAY"] = ":99"
    
    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        return {"error": f"Chrome起動失敗 (Docker): {str(e)}"}
    
    try:
        driver.get("https://www.spotify.com/signup/")
        wait = WebDriverWait(driver, 15)
        
        # 1. メールアドレス入力
        email_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'input#username, input[name="username"], input[type="email"]'))
        )
        for char in email:
            email_input.send_keys(char)
            time.sleep(0.05)
            
        next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="submit"], button[type="submit"]')))
        next_btn.click()
        time.sleep(2)

        # 2. パスワード入力
        password_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'input#password, input[name="password"], input[type="password"]'))
        )
        for char in password:
            password_input.send_keys(char)
            time.sleep(0.05)
            
        next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="submit"], button[type="submit"]')))
        next_btn.click()
        time.sleep(2)

        # 3. 名前入力 (指定の空白文字: ⠀⠀ ⠀ ⠀)
        name_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'input#displayName, input[name="displayName"], input[id*="name"]'))
        )
        for char in "⠀⠀ ⠀ ⠀":
            name_input.send_keys(char)
            time.sleep(0.05)

        # 4. 生年月日入力 (18歳以上60歳未満: 1966年〜2008年)
        birth_year = str(random.randint(1966, 2008))
        birth_month = str(random.randint(1, 12))
        birth_day = str(random.randint(1, 28))

        year_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input#year, input[name="year"]')))
        year_input.send_keys(birth_year)
        
        try:
            month_select = driver.find_element(By.CSS_SELECTOR, 'select#month, select[name="month"]')
            Select(month_select).select_by_value(birth_month)
        except Exception:
            driver.find_element(By.CSS_SELECTOR, 'input#month, input[name="month"]').send_keys(birth_month)
            
        driver.find_element(By.CSS_SELECTOR, 'input#day, input[name="day"]').send_keys(birth_day)

        next_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="submit"], button[type="submit"]')))
        next_btn.click()
        
        return {"email": email, "password": password, "status": "Waiting_For_Human"}

    except Exception as e:
        return {"error": f"自動操作途中で停止: {str(e)}"}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cloud Browser Spotify Creator</title>
    <style>
        body { background: #090909; color: #fff; font-family: sans-serif; margin: 0; padding: 20px; text-align: center; }
        .container { max-width: 900px; margin: 0 auto; }
        .button-link { background: #1DB954; color: #fff; padding: 15px 30px; font-size: 16px; font-weight: bold; border: none; border-radius: 12px; cursor: pointer; margin-bottom: 20px; }
        #browser-frame { width: 100%; height: 600px; border: 2px solid #333; border-radius: 12px; background: #000; }
        .result { margin-top: 20px; padding: 15px; background: rgba(29, 185, 84, 0.1); border: 1px solid #1DB954; border-radius: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 クラウドブラウザ・自動アカウント生成</h1>
        <p>ボタンを押すとサーバー側でブラウザが起動し、フォームまで自動入力されます。<br>認証画面が出たら下の画面をスマホで直接タップして操作してください！</p>

        <form method="POST">
            <input type="hidden" name="action" value="start_process">
            <button type="submit" class="button-link">自動入力を開始する</button>
        </form>

        {% if error_msg %}<p style="color: #ffb8bc;">{{ error_msg }}</p>{% endif %}
        {% if success_msg %}<p style="color: #b9f6c9;">{{ success_msg }}</p>{% endif %}

        {% if started %}
            <h3>👇 サーバー上のブラウザ画面（スマホから操作可能）</h3>
            <iframe id="browser-frame" src="/vnc.html?autoconnect=true&resize=scale&reconnect=true"></iframe>
        {% endif %}

        {% if spotify_result %}
            <div class="result">
                <h3>発行されたアカウント情報</h3>
                <input type="text" value="{{ spotify_result.email }}    {{ spotify_result.password }}" readonly style="width: 100%; padding: 10px; background: #222; color: #fff; border: 1px solid #444; border-radius: 8px; text-align: center;">
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    error_msg = None
    success_msg = None
    spotify_result = None
    started = False

    if request.method == "POST":
        action = request.form.get("action")
        if action == "start_process":
            started = True
            spotify_result = generate_spotify_account_web()
            if "error" in spotify_result:
                error_msg = spotify_result["error"]
            else:
                success_msg = "フォームの自動入力が完了しました！画面からreCAPTCHAをクリアしてください。"

    return render_template_string(
        HTML_TEMPLATE,
        success_msg=success_msg,
        error_msg=error_msg,
        spotify_result=spotify_result,
        started=started
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)
