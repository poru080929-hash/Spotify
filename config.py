import os

# あなたが管理するテストサイトの登録ページ
SITE_URL = os.getenv("SITE_URL", "https://accounts.spotify.com/ja/login?")

# noVNCの公開URL。ローカルDockerなら通常この値で動作します。
VNC_URL = os.getenv(
    "VNC_URL",
    "http://localhost:6080/vnc.html?autoconnect=true&resize=scale",
)

# HTMLの構造に合わせて、候補セレクタを上から順に追加できます。
SELECTORS = {
    "email": [
        "input#email",
        "input[name='email']",
        "input[type='email']",
    ],
    "password": [
        "input#password",
        "input[name='password']",
        "input[type='password']",
    ],
    "display_name": [
        "input#displayName",
        "input[name='displayName']",
        "input[name='display_name']",
        "input[name='name']",
    ],
    "birth_year": [
        "input#year",
        "input[name='year']",
        "input[name='birth_year']",
    ],
    "birth_month": [
        "select#month",
        "select[name='month']",
        "input#month",
        "input[name='month']",
        "input[name='birth_month']",
    ],
    "birth_day": [
        "input#day",
        "input[name='day']",
        "input[name='birth_day']",
    ],
    "submit": [
        "button[type='submit']",
        "input[type='submit']",
        "button[data-testid='submit']",
    ],
}

# テスト用データ。環境変数から後で差し替えられます。
TEST_DATA = {
    "email": os.getenv("TEST_EMAIL", "test@example.test"),
    "password": os.getenv("TEST_PASSWORD", "ChangeMe-Only-For-Testing"),
    "display_name": os.getenv("TEST_DISPLAY_NAME", "Test User"),
    "birth_year": os.getenv("TEST_BIRTH_YEAR", "1990"),
    "birth_month": os.getenv("TEST_BIRTH_MONTH", "5"),
    "birth_day": os.getenv("TEST_BIRTH_DAY", "15"),
}

# 自分のサイトの完了条件を後から追加できます。
COMPLETION_SELECTORS = [
    "[data-testid='signup-complete']",
    "#signup-complete",
]
COMPLETION_URL_PART = os.getenv("COMPLETION_URL_PART", "/signup/complete")
