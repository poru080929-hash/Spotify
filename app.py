import os
import threading

from flask import Flask, jsonify, redirect, render_template_string, url_for
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from config import (
    COMPLETION_SELECTORS,
    COMPLETION_URL_PART,
    SELECTORS,
    SITE_URL,
    TEST_DATA,
    VNC_URL,
)

app = Flask(__name__)
lock = threading.Lock()
driver = None
state = {"status": "idle", "error": ""}


def find_element(wait, selectors):
    last_error = None
    for selector in selectors:
        try:
            return wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"要素が見つかりません: {selectors}; {last_error}")


def fill_text(wait, selectors, value):
    element = find_element(wait, selectors)
    element.clear()
    element.send_keys(value)
    return element


def fill_birth_date(wait):
    fill_text(wait, SELECTORS["birth_year"], TEST_DATA["birth_year"])
    month = find_element(wait, SELECTORS["birth_month"])
    if month.tag_name.lower() == "select":
        Select(month).select_by_value(TEST_DATA["birth_month"])
    else:
        month.clear()
        month.send_keys(TEST_DATA["birth_month"])
    fill_text(wait, SELECTORS["birth_day"], TEST_DATA["birth_day"])


def browser_worker():
    global driver, state
    with lock:
        state = {"status": "starting", "error": ""}

    options = Options()
    # 人間がVNC画面を操作するため、headlessは指定しません。
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,720")
    options.binary_location = os.getenv("CHROMIUM_BINARY", "/usr/bin/chromium")

    try:
        service = Service(os.getenv("CHROMEDRIVER", "/usr/bin/chromedriver"))
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 20)
        driver.get(SITE_URL)

        fill_text(wait, SELECTORS["email"], TEST_DATA["email"])
        fill_text(wait, SELECTORS["password"], TEST_DATA["password"])
        fill_text(wait, SELECTORS["display_name"], TEST_DATA["display_name"])
        fill_birth_date(wait)
        find_element(wait, SELECTORS["submit"]).click()

        with lock:
            state["status"] = "waiting_for_human"
    except Exception as exc:
        with lock:
            state = {"status": "error", "error": str(exc)}
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass
            driver = None


def completion_found():
    if driver is None:
        return False
    if COMPLETION_URL_PART and COMPLETION_URL_PART in driver.current_url:
        return True
    return any(
        driver.find_elements(By.CSS_SELECTOR, selector)
        for selector in COMPLETION_SELECTORS
    )


PAGE = """
<!doctype html>
<html lang="ja">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>管理下サイトのフォームテスト</title>
<style>body{font-family:sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem}button{padding:.7rem 1rem;margin:.3rem 0}pre{white-space:pre-wrap;color:#b00020}.vnc{width:100%;height:600px;border:1px solid #888}</style>
</head>
<body>
<h1>管理下サイトのフォームテスト</h1>
<p>状態: <strong>{{ status }}</strong></p>
{% if status in ["idle", "error"] %}<form method="post" action="{{ url_for('start') }}"><button>テストブラウザを起動</button></form>{% endif %}
{% if status == "waiting_for_human" %}
<p>必要な確認操作を、別タブで開いたブラウザ画面から行ってください。</p>
<p><a href="{{ vnc_url }}" target="_blank" rel="noreferrer">noVNC画面を開く</a></p>
<iframe class="vnc" src="{{ vnc_url }}"></iframe>
<form method="post" action="{{ url_for('check') }}"><button>完了状態を確認</button></form>
{% endif %}
{% if status == "completed" %}<p>完了条件を確認しました。</p><form method="post" action="{{ url_for('finish') }}"><button>ブラウザを終了</button></form>{% endif %}
{% if error %}<pre>{{ error }}</pre>{% endif %}
</body></html>
"""


@app.get("/")
def index():
    with lock:
        snapshot = dict(state)
    return render_template_string(PAGE, vnc_url=VNC_URL, **snapshot)


@app.post("/start")
def start():
    with lock:
        if state["status"] in {"starting", "waiting_for_human"}:
            return "すでに実行中です", 409
    threading.Thread(target=browser_worker, daemon=True).start()
    return redirect(url_for("index"))


@app.post("/check")
def check():
    global state
    if completion_found():
        with lock:
            state["status"] = "completed"
        return redirect(url_for("index"))
    return "まだ完了条件を確認できません。ブラウザ画面を確認してください。", 202


@app.post("/finish")
def finish():
    global driver, state
    if driver is not None:
        try:
            driver.quit()
        finally:
            driver = None
    with lock:
        state = {"status": "idle", "error": ""}
    return redirect(url_for("index"))


@app.get("/status")
def status():
    with lock:
        return jsonify(state)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
