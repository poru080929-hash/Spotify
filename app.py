import base64
import os
import subprocess
import threading
import time

from flask import Flask, jsonify, redirect, render_template_string, url_for
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

from config import ACTIONS

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
    "screenshot": "",
}


def set_state(**values):
    with lock:
        state.update(values)


def record_progress(message):
    with lock:
        state["message"] = message
        state["history"].append(message)
        state["history"] = state["history"][-20:]


def take_screenshot_b64():
    if driver is not None:
        try:
            png = driver.get_screenshot_as_png()
            return base64.b64encode(png).decode("utf-8")
        except Exception:
            pass
    return ""


def wait_element(selector, timeout=25):
    selectors = [item.strip() for item in selector.split(",")]
    start_time = time.time()

    while time.time() - start_time < timeout:
        for css_selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, css_selector)
                for element in elements:
                    if element.is_displayed():
                        return element
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


def run_action(browser, action, index):
    kind = action.get("type")
    description = describe_action(action, index)
    set_state(
        status="running",
        current_action=description,
        action_index=index,
    )
    record_progress(f"開始 {description}")
    time.sleep(1.0)

    if kind == "goto":
        try:
            browser.get(action["url"])
        except Exception as exc:
            record_progress(f"ページ読み込み警告: {exc}")
        time.sleep(float(action.get("after_wait", 2.5)))
    elif kind == "click":
        element = wait_element(
            action["selector"],
            timeout=float(action.get("timeout", 25)),
        )
        if not element:
            if action.get("optional", False):
                record_progress(
                    f"任意要素が見つからないためスキップ: {action['selector']}"
                )
                return
            raise TimeoutError(
                "要素が見つかりません（ボット検知やモーダルの可能性があります）: "
                f"{action['selector']}"
            )
        browser.execute_script("arguments[0].click();", element)
        time.sleep(float(action.get("after_wait", 2.0)))

    elif kind == "fill":
        element = wait_element(
            action["selector"],
            timeout=float(action.get("timeout", 25)),
        )
        if not element:
            raise TimeoutError(f"入力欄が見つかりません: {action['selector']}")
        element.clear()
        time.sleep(0.3)
        element.send_keys(action_value(action))
        time.sleep(float(action.get("after_wait", 1.5)))

    elif kind == "select":
        element = wait_element(
            action["selector"],
            timeout=float(action.get("timeout", 25)),
        )
        if not element:
            raise TimeoutError(f"選択ボックスが見つかりません: {action['selector']}")
        Select(element).select_by_value(str(action_value(action)))
        time.sleep(float(action.get("after_wait", 1.5)))

    elif kind == "check":
        element = wait_element(
            action["selector"],
            timeout=float(action.get("timeout", 25)),
        )
        if not element:
            raise TimeoutError(f"チェックボックスが見つかりません: {action['selector']}")
        if not element.is_selected():
            browser.execute_script("arguments[0].click();", element)
        time.sleep(float(action.get("after_wait", 1.0)))

    elif kind == "wait":
        time.sleep(float(action.get("seconds", 1)))

    elif kind == "scroll":
        browser.execute_script(
            "window.scrollBy(0, arguments[0]);",
            action.get("y", 500),
        )

    elif kind == "human":
        screenshot = take_screenshot_b64()
        set_state(
            status="waiting_for_human",
            message=action.get("message", "確認してください"),
            screenshot=screenshot,
        )
        resume_event.clear()
        resume_event.wait()

    else:
        raise RuntimeError(f"未対応の操作 type: {kind}")

    record_progress(f"完了 {index}/{len(ACTIONS)}")


def command_version(command):
    try:
        return subprocess.check_output(
            command,
            text=True,
            stderr=subprocess.STDOUT,
            timeout=10,
        ).strip()
    except Exception as exc:
        return f"取得失敗: {exc}"


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
            "screenshot": "",
        }

    chromium_binary = os.getenv("CHROMIUM_BINARY", "/usr/bin/chromium")
    chromedriver_binary = os.getenv("CHROMEDRIVER", "/usr/bin/chromedriver")

    options = Options()
    options.page_load_strategy = "eager"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-features=Translate,BackForwardCache")
    options.add_argument("--window-size=1280,720")
    options.add_argument("--user-data-dir=/tmp/selenium-profile")
    options.binary_location = chromium_binary

    try:
        record_progress(
            f"Chromium: {command_version([chromium_binary, '--version'])}"
        )
        record_progress(
            f"ChromeDriver: {command_version([chromedriver_binary, '--version'])}"
        )

        service = Service(
            chromedriver_binary,
            log_output="/tmp/chromedriver.log",
        )
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(45)
        driver.set_script_timeout(30)
        wait = WebDriverWait(driver, 20)

        for index, action in enumerate(ACTIONS, start=1):
            run_action(driver, action, index)

        screenshot = take_screenshot_b64()
        set_state(
            status="waiting_for_human",
            current_action="自動操作完了",
            message="処理が完了しました",
            screenshot=screenshot,
        )

    except Exception as exc:
        screenshot = take_screenshot_b64()
        log_path = "/tmp/chromedriver.log"
        error_text = str(exc)
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as log_file:
                    log_tail = log_file.read()[-4000:]
                error_text += f"\n\nChromeDriverログ末尾:\n{log_tail}"
            except Exception:
                pass

        with lock:
            state.update(
                status="waiting_for_human",
                error=error_text,
                message="Chrome起動または自動操作でエラーが発生しました。ログを確認してください。",
                screenshot=screenshot,
            )
        record_progress(f"一時停止: {exc}")


PAGE = """
<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>自動操作</title>
<style>
body{font-family:sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem}
button{padding:.7rem 1rem;margin:.3rem 0;font-size:1rem}
pre{white-space:pre-wrap;color:#b00020;overflow-wrap:anywhere}
.progress{padding:1rem;background:#f2f5f7;border-radius:8px;margin:1rem 0}
.history{font-size:.9rem;background:#111;color:#eee;padding:1rem;border-radius:8px;max-height:220px;overflow:auto}
.screenshot-box{margin:1rem 0;border:2px solid #ccc;border-radius:8px;padding:.5rem;background:#fafafa}
.screenshot-box img{width:100%;height:auto;border-radius:4px;display:block}
</style>
</head>
<body>
<h1>自動操作</h1>
<p>状態: <strong id="status">{{ status }}</strong></p>
<div class="progress">
  <strong id="current-action">{{ current_action or message }}</strong><br>
  <span id="progress-count">{{ action_index }}/{{ action_total }}</span>
  <p id="status-message">{{ message }}</p>
</div>

<div class="screenshot-box" id="screenshot-container" style="display:{% if screenshot %}block{% else %}none{% endif %};">
  <strong>停止時の画面スクショ:</strong>
  <img id="screenshot-img" src="{% if screenshot %}data:image/png;base64,{{ screenshot }}{% endif %}" alt="スクショ">
</div>

<pre class="history" id="history">{% for item in history %}{{ item }}
{% endfor %}</pre>

{% if status in ["idle", "error"] %}
<form method="post" action="{{ url_for('start') }}"><button>自動化を開始</button></form>
{% endif %}
{% if status == "waiting_for_human" %}
<form method="post" action="{{ url_for('finish') }}"><button>セッションを終了してリセット</button></form>
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
    document.getElementById("history").textContent = (data.history || []).join("\n");

    const container = document.getElementById("screenshot-container");
    const image = document.getElementById("screenshot-img");
    if (data.screenshot) {
      image.src = "data:image/png;base64," + data.screenshot;
      container.style.display = "block";
    } else {
      container.style.display = "none";
    }
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
            "screenshot": "",
        }
    return redirect(url_for("index"))


@app.get("/status")
def status():
    with lock:
        return jsonify(state)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
