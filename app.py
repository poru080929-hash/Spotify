import os
import threading
import time

from flask import Flask, jsonify, redirect, render_template_string, url_for
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

from config import ACTIONS, COMPLETION_SELECTORS, COMPLETION_URL_PART, VNC_URL

app = Flask(__name__)
lock = threading.Lock()
driver = None
resume_event = threading.Event()
state = {
    "status": "idle",
    "error": "",
    "message": "",
    "current_action": "",
    "action_index": 0,
    "action_total": len(ACTIONS),
    "history": [],
}

def set_state(**values):
    with lock:
        state.update(values)

def wait_element(selector, timeout=25):
    selectors = [s.strip() for s in selector.split(",")]
    start_time = time.time()
    while time.time() - start_time < timeout:
        for sel in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, sel)
                for el in elements:
                    if el.is_displayed():
                        return el
            except Exception:
                pass
        time.sleep(0.5)
    return None

def action_value(action):
    if "value_env" in action:
        name = action["value_env"]
        if name not in os.environ:
            raise RuntimeError(f"環境変数が未設定です: {name}")
        return os.environ[name]
    return action.get("value", "")

def describe_action(action, index):
    labels = {
        "goto": "ページを開いています",
        "click": "クリックしています",
        "fill": "入力しています",
        "select": "選択しています",
        "check": "チェックしています",
        "wait": "待機しています",
        "scroll": "スクロールしています",
        "human": "確認を待っています",
    }
    kind = action.get("type", "unknown")
    text = labels.get(kind, f"{kind}を実行しています")
    selector = action.get("selector")
    if selector:
        text += f"（対象: {selector}）"
    return f"{index}/{len(ACTIONS)}: {text}"

def record_progress(message):
    with lock:
        state["message"] = message
        state["history"].append(message)
        state["history"] = state["history"][-20:]

def run_action(browser, wait, action, index):
    kind = action.get("type")
    description = describe_action(action, index)
    set_state(status="running", current_action=description, action_index=index)
    record_progress(f"開始 {description}")

    time.sleep(1.0)

    if kind == "goto":
        browser.get(action["url"])
        time.sleep(2.5)
    elif kind == "click":
        element = wait_element(action["selector"])
        if not element:
            raise TimeoutError(f"要素が見つかりません（ボット検知の可能性があります）: {action['selector']}")
        browser.execute_script("arguments[0].click();", element)
        time.sleep(2.0)
    elif kind == "fill":
        element = wait_element(action["selector"])
        if not element:
            raise TimeoutError(f"入力欄が見つかりません（ボット検知の可能性があります）: {action['selector']}")
        element.clear()
        time.sleep(0.3)
        element.send_keys(action_value(action))
        time.sleep(1.5)
    elif kind == "select":
        element = wait_element(action["selector"])
        if not element:
            raise TimeoutError(f"選択ボックスが見つかりません: {action['selector']}")
        Select(element).select_by_value(str(action_value(action)))
        time.sleep(1.5)
    elif kind == "check":
        element = wait_element(action["selector"])
        if not element:
            raise TimeoutError(f"チェックボックスが見つかりません: {action['selector']}")
        if not element.is_selected():
            browser.execute_script("arguments[0].click();", element)
        time.sleep(1.0)
    elif kind == "wait":
        time.sleep(float(action.get("seconds", 1)))
    elif kind == "scroll":
        browser.execute_script("window.scrollBy(0, arguments[0]);", action.get("y", 500))
    elif kind == "human":
        set_state(status="waiting_for_human", message=action.get("message", "確認してください"))
        resume_event.clear()
        resume_event.wait()
    else:
        raise RuntimeError(f"未対応の操作 type: {kind}")

    record_progress(f"完了 {index}/{len(ACTIONS)}")

def browser_worker():
    global driver, state
    with lock:
        state = {
            "status": "starting",
            "error": "",
            "message": "ブラウザを起動しています",
            "current_action": "",
            "action_index": 0,
            "action_total": len(ACTIONS),
            "history": [],
        }

    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,720")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.binary_location = os.getenv("CHROMIUM_BINARY", "/usr/bin/chromium")

    try:
        service = Service(os.getenv("CHROMEDRIVER", "/usr/bin/chromedriver"))
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 20)
        for index, action in enumerate(ACTIONS, start=1):
            run_action(driver, wait, action, index)

        set_state(status="waiting_for_human", current_action="自動操作完了", message="処理が完了しました")
    except Exception as exc:
        # エラーや検知で止まった場合、即死させずに一時停止モードへ逃がす
        with lock:
            state.update(
                status="waiting_for_human",
                error=str(exc),
                message="ボット検知またはタイムアウトにより一時停止しました。画面を確認してください。",
            )
        record_progress(f"一時停止: {exc}")
        # driverは終了させず保持する

def completion_found():
    if driver is None:
        return False
    if COMPLETION_URL_PART and COMPLETION_URL_PART in driver.current_url:
        return True
    return any(driver.find_elements(By.CSS_SELECTOR, selector) for selector in COMPLETION_SELECTORS)

PAGE = """
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>自動アカウント生成</title>
<style>
body{font-family:sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem}
button{padding:.7rem 1rem;margin:.3rem 0;font-size:1rem}
pre{white-space:pre-wrap;color:#b00020}
.progress{padding:1rem;background:#f2f5f7;border-radius:8px;margin:1rem 0}
.history{font-size:.9rem;background:#111;color:#eee;padding:1rem;border-radius:8px;max-height:220px;overflow:auto}
</style>
</head>
<body>
<h1>自動アカウント生成</h1>
<p>状態: <strong id="status">{{ status }}</strong></p>
<div class="progress">
  <strong id="current-action">{{ current_action or message }}</strong><br>
  <span id="progress-count">{{ action_index }}/{{ action_total }}</span>
  <p id="status-message">{{ message }}</p>
</div>
<pre class="history" id="history">{% for item in history %}{{ item }}
{% endfor %}</pre>
{% if status in ["idle", "error"] %}
<form method="post" action="{{ url_for('start') }}"><button>自動化を開始</button></form>
{% endif %}
{% if status == "waiting_for_human" %}
<form method="post" action="{{ url_for('resume') }}"><button>操作を再開する</button></form>
<form method="post" action="{{ url_for('finish') }}"><button>セッションを終了してリセット</button></form>
{% endif %}
{% if status == "completed" %}
<form method="post" action="{{ url_for('finish') }}"><button>セッションを終了</button></form>
{% endif %}
{% if error %}<pre>{{ error }}</pre>{% endif %}
<script>
async function refreshStatus() {
  try {
    const response = await fetch("{{ url_for('status') }}", {cache: "no-store"});
    const data = await response.json();
    document.getElementById("status").textContent = data.status || "";
    document.getElementById("current-action").textContent = data.current_action || data.message || "";
    document.getElementById("progress-count").textContent = `${data.action_index || 0}/${data.action_total || 0}`;
    document.getElementById("status-message").textContent = data.message || "";
    document.getElementById("history").textContent = (data.history || []).join("\\n");
  } catch (error) {
    console.warn("更新失敗", error);
  }
}
setInterval(refreshStatus, 1000);
</script>
</body>
</html>
"""

@app.get("/")
def index():
    with lock:
        snapshot = dict(state)
    return render_template_string(PAGE, **snapshot)

@app.post("/start")
def start():
    with lock:
        if state["status"] in {"starting", "running", "waiting_for_human"}:
            return "すでに実行中です", 409
    threading.Thread(target=browser_worker, daemon=True).start()
    return redirect(url_for("index"))

@app.post("/resume")
def resume():
    resume_event.set()
    return redirect(url_for("index"))

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
        state = {
            "status": "idle",
            "error": "",
            "message": "",
            "current_action": "",
            "action_index": 0,
            "action_total": len(ACTIONS),
            "history": [],
        }
    return redirect(url_for("index"))

@app.get("/status")
def status():
    with lock:
        return jsonify(state)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
