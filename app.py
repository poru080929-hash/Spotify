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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Spotify登録フォームへの入力（アカウント作成は行わない） ---
def generate_spotify_account_web():
    letters = string.ascii_lowercase + string.digits
    email = f"{''.join(random.choice(letters) for _ in range(10))}@vel0x0.xyz"
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--window-size=1920,1080")
    # reCAPTCHA等の外部リソースが完了しなくてもDOMを操作できるようにする。
    options.page_load_strategy = "none"

    # リクエストごとにChromeプロファイルを分離する。
    # 固定ポートや共有プロファイルは、Renderの同時実行時にセッション切断を起こす。
    profile_dir = tempfile.mkdtemp(prefix="spotify-chrome-")
    options.add_argument(f"--user-data-dir={profile_dir}")
    
    # Docker環境（Debian系）のパスを明示
    options.binary_location = "/usr/bin/chromium"
    
    driver = None
    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(10)
        driver.set_script_timeout(15)
    except WebDriverException as e:
        shutil.rmtree(profile_dir, ignore_errors=True)
        return {"error": f"Chrome起動失敗 (Docker): {str(e)}"}
    
    try:
        # Renderの送信元IPに応じてSpotifyが適切な国別ページへリダイレクトする。
        # /jp/signup/ に固定すると、地域確認モーダルで入力欄が disabled になる。
        driver.get("https://www.spotify.com/signup/")
        # ページ全体ではなく、必要な入力欄がDOMに現れるまで待つ。
        wait = WebDriverWait(driver, 18)
        
        # Spotifyの現行ページではメール欄のIDが email から username に変更されている。
        # 初期表示時はページの初期化が完了するまで disabled のため、有効化も待つ。
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
            time.sleep(random.uniform(0.05, 0.15))
            
        return {
            "email": email,
            "status": "email_entered",
            "message": (
                "メールアドレスを登録フォームに入力しました。"
                "Spotifyアカウントの作成・ログイン確認は完了していません。"
            ),
        }
    except TimeoutException:
        try:
            driver.save_screenshot("/tmp/spotify-timeout.png")
        except Exception:
            pass
        return {
            "error": (
                "Spotifyのメール入力欄が見つかりませんでした。"
                f" URL={driver.current_url} title={driver.title}"
            )
        }
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
        <p class="lead">ボタンを押すとSpotifyの登録フォームにメールアドレスを入力します。アカウント作成自体は完了しません。</p>

        {% if error_msg %}<div class="notice error">{{ error_msg }}</div>{% endif %}
        {% if success_msg %}<div class="notice success">{{ success_msg }}</div>{% endif %}

        <form method="POST" onsubmit="startGeneration()">
            <input type="hidden" name="action" value="create_spotify">
            <button type="submit" class="button-link" id="generateBtn">Spotify登録フォームに入力する</button>
        </form>

        {% if spotify_result %}
            <div class="result">
                <p class="result-title">登録フォームへの入力完了</p>
                <label style="font-size: 12px; color: var(--muted); display: block; margin-bottom: 6px;">入力したメールアドレス</label>
                <div class="credential-box">
                    <input type="text" id="spotifyCreds" value="{{ spotify_result.email }}" readonly>
                    <button type="button" class="button-link" id="copySpotifyBtn" onclick="copySpotifyCreds()" style="width: 140px; min-height: 56px; margin: 0;">📋 コピー</button>
                </div>
            </div>
        {% endif %}
    </main>

    <script>
        function startGeneration() {
            var btn = document.getElementById("generateBtn");
            btn.disabled = true;
            btn.innerText = "生成中...（最大30秒）";
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
                    success_msg = spotify_result["message"]
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
