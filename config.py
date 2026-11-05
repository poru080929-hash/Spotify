import os

# ここから下だけを変更すれば、操作手順を変更できます。
SITE_URL = os.getenv("SITE_URL", "https://example.test/")
VNC_URL = os.getenv(
    "VNC_URL",
    "http://localhost:6080/vnc.html?autoconnect=true&resize=scale",
)

# type は goto / click / fill / select / check / wait / scroll / human
# selector は CSS セレクタです。
# value_env を使うと、入力値を環境変数から読み込みます。
ACTIONS = [
    {"type": "goto", "url": SITE_URL},
    # {"type": "click", "selector": "button#start"},
    # {"type": "fill", "selector": "input[name='email']", "value_env": "TEST_EMAIL"},
    # {"type": "fill", "selector": "input[name='password']", "value_env": "TEST_PASSWORD"},
    # {"type": "select", "selector": "select[name='country']", "value": "JP"},
    # {"type": "check", "selector": "input[name='terms']"},
    # {"type": "wait", "seconds": 2},
    # {"type": "scroll", "y": 500},
    # {"type": "human", "message": "画面を確認してください"},
]

# 管理下テストサイトで使う完了条件
COMPLETION_SELECTORS = [
    "[data-testid='signup-complete']",
    "#signup-complete",
]
COMPLETION_URL_PART = os.getenv("COMPLETION_URL_PART", "/signup/complete")

# 後方互換用。ACTIONSでvalue_envを使うことを推奨します。
TEST_DATA = {
    "email": os.getenv("TEST_EMAIL", "test@example.test"),
    "password": os.getenv("TEST_PASSWORD", "only-for-local-testing"),
    "display_name": os.getenv("TEST_DISPLAY_NAME", "Test User"),
    "birth_year": os.getenv("TEST_BIRTH_YEAR", "1990"),
    "birth_month": os.getenv("TEST_BIRTH_MONTH", "5"),
    "birth_day": os.getenv("TEST_BIRTH_DAY", "15"),
}
