import os
import random
import string
import time
import shutil
import tempfile
import setuptools  # Python 3.14のdistutilsエラー対策
from flask import Flask, render_template_string, request

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- パスワード生成 (10文字以上、大文字1つ以上、'.'を1つ以上含む) ---
def generate_secure_password():
    lower_digits = string.ascii_lowercase + string.digits
    base = ''.join(random.choice(lower_digits) for _ in range(10))
    pw_list = list(base)
    pw_list[0] = random.choice(string.ascii_uppercase)
    pw_list[1] = '.'
    random.shuffle(pw_list)
    return ''.join(pw_list)

# --- 標準SeleniumによるSpotifyアカウント自動生成 (厳格完了確認版) ---
def generate_spotify_account_web():
    letters = string.ascii_lowercase + string.digits
    email = f"{''.join(random.choice(letters) for _ in range(10))}@vel0x0.xyz"
    password = generate_secure_password()
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--window-size=1920,1080")
    options.page_load_strategy = "none"

    profile_dir = tempfile.mkdtemp(prefix="spotify-chrome-")
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.binary_location = "/usr/bin/chromium"
    
    driver = None
    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(15)
        driver.set_script_timeout(15)
    except WebDriverException as e:
        shutil.rmtree(profile_dir, ignore_errors=True)
        return {"error": f"Chrome起動失敗 (Docker): {str(e)}"}
    
    try:
        driver.get("https://www.spotify.com/signup/")
        wait = WebDriverWait(driver, 15)
        
        # 1. メールアドレス入力
        email_input = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    'input#username:not([disabled]), '
                    'input[name="username"]:not([disabled]), '
                    'input[type="email"]:not([disabled])'
                )
            )
        )
        for char in email:
            email_input.send_keys(char)
            time.sleep(random.uniform(0.02, 0.05))
            
        # 次へボタン
        next_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="submit"], button[type="submit"]'))
        )
        next_btn.click()
        time.sleep(2)

        # 2. パスワード入力
        password_input = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    'input#password:not([disabled]), '
                    'input[name="password"]:not([disabled]), '
                    'input[type="password"]:not([disabled])'
                )
            )
        )
        for char in password:
            password_input.send_keys(char)
            time.sleep(random.uniform(0.02, 0.05))
            
        next_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="submit"], button[type="submit"]'))
        )
        next_btn.click()
        time.sleep(2)

        # 3. 名前入力 (指定の空白文字)
        name_input = wait.until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    'input#displayName:not([disabled]), '
                    'input[name="displayName"]:not([disabled]), '
                    'input[id*="name"]:not([disabled])'
                )
            )
        )
        target_name = "⠀⠀ ⠀ ⠀"
        for char in target_name:
            name_input.send_keys(char)
            time.sleep(random.uniform(0.02, 0.05))

        # 4. 生年月日入力 (18歳以上60歳未満: 1966年〜2008年をランダム選択)
        birth_year = str(random.randint(1966, 2008))
        birth_month = str(random.randint(1, 12))
        birth_day = str(random.randint(1, 28))

        year_input = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'input#year, input[name="year"]'))
        )
        year_input.send_keys(birth_year)
        
        try:
            month_select = driver.find_element(By.CSS_SELECTOR, 'select#month, select[name="month"]')
            Select(month_select).select_by_value(birth_month)
        except Exception:
            month_input = driver.find_element(By.CSS_SELECTOR, 'input#month, input[name="month"]')
            month_input.send_keys(birth_month)
            
        day_input = driver.find_element(By.CSS_SELECTOR, 'input#day, input[name="day"]')
        day_input.send_keys(birth_day)

        # 生年月日入力後の「次へ」ボタン
        next_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="submit"], button[type="submit"]'))
        )
        next_btn.click()
        time.sleep(2)

        # 5. 利用規約などの最終同意・登録完了ボタンの押下
        # Spotifyの登録フローによって「登録する」や複数のチェックボックス・規約同意ボタンが現れるため順次処理
        try:
            # 性別選択があれば適当に選択（例：指定なし、または最初のラジオボタン）
            gender_options = driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')
            if gender_options:
                gender_options[0].click()
                time.sleep(1)
        except Exception:
            pass

        # 最終の「Spotifyに登録する」などのボタンを探してクリック
        for _ in range(2):
            try:
                submit_btn = wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="submit"], button[type="submit"]'))
                )
                submit_btn.click()
                time.sleep(3)
            except Exception:
                break

        # 6. 【重要】アカウント作成が本当に完了したかをURLや画面遷移で検証
        # 登録が成功するとURLが /signup から /account や /overview などに変わる、またはウェルカム要素が出現する
        time.sleep(3)
        current_url = driver.current_url
        if "signup" in current_url:
            # まだサインアップ画面に留まっている場合は、reCAPTCHAやブロックに阻まれている可能性が高い
            return {"error": f"登録が完了しませんでした（登録画面で停止中）。URL: {current_url}"}

        return {"email": email, "password": password, "status": "Success"}

    except TimeoutException as e:
        try:
            driver.save_screenshot("/tmp/spotify-timeout.png")
        except Exception:
            pass
        return {"error": f"タイムアウト発生（要素が見つかりません）: {str(e)}"}
    except Exception as e:
        return {"error": f"自動操作エラー: {str(e)}"}
    finally:
        try:
            driver.quit()
        except Exception:
            pass
        shutil.rmtree(profile_dir, ignore_errors=True)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spotify Account Generator</title>
    <style>
        :root {
            --bg: #090909;
            --surface: #171717;
            --surface-light: #222222;
            --border: rgba(255, 255, 255, 0.10);
            --text: #ffffff;
            --muted: #a6a6a6;
            --green: #46d369;
            --spotify: #1DB954;
            --shadow: 0 24px 70px rgba(0, 0, 0, 0.45);
        }
        * { box-sizing: border-box; }
        body {
            min-height: 100vh;
            margin: 0;
            padding: 40px 20px;
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: linear-gradient(180deg, #181818 0%, var(--bg) 55%);
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            width: min(100%, 600px);
            padding: 40px;
            background: rgba(23, 23, 23, 0.94);
            border: 1px solid var(--border);
            border-radius: 24px;
            box-shadow: var(--shadow);
        }
        h1 { margin: 0 0 10px; font-size: 26px; color: var(--spotify); }
        .lead { margin: 0 0 25px; color: var(--muted); font-size: 14px; }
        .notice {
            margin-bottom: 20px;
            padding: 14px;
            border-radius: 12px;
            font-size: 14px;
        }
        .notice.error { color: #ffb8bc; background: rgba(229, 9, 20, 0.12); border: 1px solid rgba(229, 9, 20, 0.3); }
        .notice.success { color: #b9f6c9; background: rgba(70, 211, 105, 0.12); border: 1px solid rgba(70, 211, 105, 0.3); }
        .button-link {
            display: inline-flex;
            width: 100%;
            min-height: 56px;
            align-items: center;
            justify-content: center;
            color: #fff;
            font-size: 16px;
            font-weight: 800;
            background: linear-gradient(135deg, #1ed760, var(--spotify));
            border: 0;
            border-radius: 12px;
            cursor: pointer;
            box-shadow: 0 10px 25px rgba(29, 185, 84, 0.25);
            transition: 0.2s;
        }
        .button-link:hover { opacity: 0.9; transform: translateY(-2px); }
        input[type="text"] {
            width: 100%;
            min-height: 56px;
            margin: 0;
            padding: 14px 16px;
            color: var(--text);
            font-family: monospace;
            font-size: 15px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border);
            border-radius: 12px;
            outline: none;
        }
        .result {
            margin-top: 25px;
            padding: 20px;
            background: rgba(29, 185, 84, 0.08);
            border: 1px solid rgba(29, 185, 84, 0.3);
            border-radius: 16px;
        }
        .result-title { margin: 0 0 12px; color: var(--spotify); font-size: 16px; font-weight: 800; }
        .credential-box { display: flex; gap: 10px; }
    </style>
</head>
<body>
    <main class="container">
        <h1>🎵 Spotify アカウント自動生成</h1>
        <p class="lead">ボタンを押すとサーバー側でブラウザが起動し、登録完了まで自動処理します。</p>

        {% if error_msg %}<div class="notice error">{{ error_msg }}</div>{% endif %}
        {% if success_msg %}<div class="notice success">{{ success_msg }}</div>{% endif %}

        <form method="POST" onsubmit="startGeneration()">
            <input type="hidden" name="action" value="create_spotify">
            <button type="submit" class="button-link" id="generateBtn">Spotifyアカウントを自動生成する</button>
        </form>

        {% if spotify_result %}
            <div class="result">
                <p class="result-title">アカウント登録成功！</p>
                <label style="font-size: 12px; color: var(--muted); display: block; margin-bottom: 6px;">メールアドレス　　　　　パスワード</label>
                <div class="credential-box">
                    <input type="text" id="spotifyCreds" value="{{ spotify_result.email }}    {{ spotify_result.password }}" readonly>
                    <button type="button" class="button-link" id="copySpotifyBtn" onclick="copySpotifyCreds()" style="width: 140px; min-height: 56px; margin: 0;">📋 コピー</button>
                </div>
            </div>
        {% endif %}
    </main>

    <script>
        function startGeneration() {
            var btn = document.getElementById("generateBtn");
            btn.disabled = true;
            btn.innerText = "生成・登録中...（最大45秒）";
        }

        function copySpotifyCreds() {
            var copyText = document.getElementById("spotifyCreds");
            copyText.select();
            copyText.setSelectionRange(0, 99999);
            navigator.clipboard.writeText(copyText.value).then(function() {
                var btn = document.getElementById("copySpotifyBtn");
                btn.innerText = "✨ コピー完了";
                setTimeout(function() {
                    btn.innerText = "📋 コピー";
                }, 2000);
            });
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    error_msg = None
    success_msg = None
    spotify_result = None

    if request.method == "POST":
        action = request.form.get("action")
        if action == "create_spotify":
            try:
                spotify_result = generate_spotify_account_web()
                if "error" in spotify_result:
                    error_msg = f"生成エラー: {spotify_result['error']}"
                else:
                    success_msg = "Spotifyアカウントの作成と登録が完了しました！"
            except Exception as e:
                error_msg = f"エラー: {e}"

    return render_template_string(
        HTML_TEMPLATE,
        success_msg=success_msg,
        error_msg=error_msg,
        spotify_result=spotify_result
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
