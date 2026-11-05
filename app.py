import os
import threading
import time

from flask import Flask, jsonify, redirect, render_template_string, url_for
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from config import ACTIONS, COMPLETION_SELECTORS, COMPLETION_URL_PART, VNC_URL

app = Flask(__name__)
lock = threading.Lock()
driver = None
resume_event = threading.Event()
state = {"status": "idle", "error": "", "message": ""}


def wait_element(wait, selector, clickable=False):
    condition = (
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
        if clickable
        else EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )
    return wait.until(condition)


def action_value(action):
    if "value_env" in action:
        name = action["value_env"]
        if name not in os.environ:
            raise RuntimeError(f"環境変数が未設定です: {name}")
        return os.environ[name]
    return action.get("value", "")


def run_action(browser, wait, action):
    kind = action.get("type")

    if kind == "goto":
        browser.get(action["url"])
    elif kind == "click":
        wait_element(wait, action["selector"], clickable=True).click()
    elif kind == "fill":
        element = wait_element(wait, action["selector"])
        element.clear()
        element.send_keys(action_value(action))
    elif kind == "select":
        element = wait_element(wait, action["selector"])
        Select(element).select_by_value(str(action_value(action)))
    elif kind == "check":
        element = wait_element(wait, action["selector"], clickable=True)
        if not element.is_selected():
            element.click()
    elif kind == "wait":
        time.sleep(float(action.get("seconds", 1)))
    elif kind == "scroll":
        browser.execute_script("window.scrollBy(0, arguments[0]);", action.get("y", 500))
    elif kind == "human":
        with lock:
            state.update(
                status="waiting_for_human",
                message=action.get("message", "画面を操作してから再開してください"),
            )
        resume_event.clear()
        resume_event.wait()
    else:
        raise RuntimeError(f"未対応の操作 type: {kind}")


def browser_worker():
    global driver, state
    with lock:
        state = {"status": "starting", "error": "", "message": ""}

    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,720")
    options.binary_location = os.getenv("CHROMIUM_BINARY", "/usr/bin/chromium")

    try:
        service = Service(os.getenv("CHROMEDRIVER", "/usr/bin/chromedriver"))
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 20)
        for action in ACTIONS:
            run_action(driver, wait, action)
        with lock:
            state.update(status="waiting_for_human", message="操作が完了したら、完了状態を確認してください")
    except Exception as exc:
        with lock:
            state = {"status": "error", "error": str(exc), "message": ""}
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
    return any(driver.find_elements(By.CSS_SELECTOR, selector) for selector in COMPLETION_SELECTORS)


PAGE = """
<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>管理下サイトのフォームテスト</title>
<style>body{font-family:sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem}button{padding:.7rem 1rem;margin:.3rem 0}.vnc{width:100%;height:600px;border:1px solid #888}pre{white-space:pre-wrap;color:#b00020}</style></head>
<body><h1>管理下サイトのフォームテスト</h1><p>状態: <strong>{{ status }}</strong></p>
{% if message %}<p>{{ message }}</p>{% endif %}
{% if status in ["idle", "error"] %}<form method="post" action="{{ url_for('start') }}"><button>テストブラウザを起動</button></form>{% endif %}
{% if status == "waiting_for_human" %}<p><a href="{{ vnc_url }}" target="_blank" rel="noreferrer">noVNC画面を開く</a></p><iframe class="vnc" src="{{ vnc_url }}"></iframe><form method="post" action="{{ url_for('resume') }}"><button>人間操作を完了して再開</button></form><form method="post" action="{{ url_for('check') }}"><button>完了状態を確認</button></form>{% endif %}
{% if status == "completed" %}<p>完了条件を確認しました。</p><form method="post" action="{{ url_for('finish') }}"><button>ブラウザを終了</button></form>{% endif %}
{% if error %}<pre>{{ error }}</pre>{% endif %}</body></html>
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


@app.post("/resume")
def resume():
    resume_event.set()
    return redirect(url_for("index"))


@app.post("/check")
def check():
    global state
    if completion_found():
        with lock:
            state.update(status="completed", message="")
        return redirect(url_for("index"))
    return "まだ完了条件を確認できません。画面を確認してください。", 202


@app.post("/finish")
def finish():
    global driver, state
    resume_event.set()
    if driver is not None:
        try:
            driver.quit()
        finally:
            driver = None
    with lock:
        state = {"status": "idle", "error": "", "message": ""}
    return redirect(url_for("index"))


@app.get("/status")
def status():
    with lock:
        return jsonify(state)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
