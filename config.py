import os
import random
import string

# 1. 最初に開くURL
SITE_URL = os.getenv("SITE_URL", "https://www.spotify.com/jp/premium/")
VNC_URL = os.getenv(
    "VNC_URL",
    "http://localhost:6080/vnc.html?autoconnect=true&resize=scale",
)

# --- 動的データの生成関数 ---
def generate_random_email():
    letters = string.ascii_lowercase + string.digits
    random_str = "".join(random.choice(letters) for _ in range(10))
    return f"{random_str}@vel0x0.xyz"

def generate_secure_password():
    # 「数字を一つ、英字を一字、合計で10文字」のパスワードをランダム生成
    # 例：英字8文字 + 大文字1文字 + 数字1文字 などをベースに10文字に調整
    alphabet = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    
    # 最低条件（数字1つ、英字（大文字・小文字含む）を10文字）
    pw_chars = [
        random.choice(digits),
        random.choice(uppercase),
    ]
    # 残り8文字を小文字や数字からランダムに埋めて計10文字にする
    while len(pw_chars) < 10:
        pw_chars.append(random.choice(alphabet + digits))
        
    random.shuffle(pw_chars)
    return "".join(pw_chars)

def generate_birth_date():
    # 18歳から60歳未満 (2026年基準で1966年〜2008年)
    year = str(random.randint(1966, 2008))
    month = str(random.randint(1, 12))
    day = str(random.randint(1, 28))
    return year, month, day

birth_year, birth_month, birth_day = generate_birth_date()

# テストデータ（毎回ランダムに生成）
TEST_DATA = {
    "email": os.getenv("TEST_EMAIL", generate_random_email()),
    "password": os.getenv("TEST_PASSWORD", generate_secure_password()),
    "display_name": os.getenv("TEST_DISPLAY_NAME", "⠀⠀ ⠀ ⠀"),
    "birth_year": os.getenv("TEST_BIRTH_YEAR", birth_year),
    "birth_month": os.getenv("TEST_BIRTH_MONTH", birth_month),
    "birth_day": os.getenv("TEST_BIRTH_DAY", birth_day),
}

# --- お前の指示通りの正確な操作ステップ定義 ---
ACTIONS = [
    # 1. 最初は https://www.spotify.com/jp/premium/ を開く
    {"type": "goto", "url": SITE_URL},
    {"type": "wait", "seconds": 2},
    
    # 2. 「1ヶ月間¥0で体験」をタップ
    {"type": "click", "selector": "a[data-testid='plan-card-cta'], a[href*='signup'], button[data-testid*='cta']"},
    {"type": "wait", "seconds": 2},
    
    # 3. 「登録」をタップ（※ページ遷移により自動的に登録画面になる場合もあるため、ボタンがあればクリック）
    {"type": "click", "selector": "button[data-testid='submit'], a[data-testid='signup-link']"},
    {"type": "wait", "seconds": 2},
    
    # 4. メールアドレス入力画面 -> ランダムな @vel0x0.xyz を入力
    {"type": "fill", "selector": "input#username, input[name='username'], input[type='email']", "value_env": "TEST_EMAIL"},
    # 5. 「次へ」をタップ
    {"type": "click", "selector": "button[data-testid='submit'], button[type='submit']"},
    {"type": "wait", "seconds": 2},
    
    # 6. パスワード画面 -> 指定条件の10文字パスワードを入力して次へ
    {"type": "fill", "selector": "input#password, input[name='password'], input[type='password']", "value_env": "TEST_PASSWORD"},
    {"type": "click", "selector": "button[data-testid='submit'], button[type='submit']"},
    {"type": "wait", "seconds": 2},
    
    # 7. 名前入力 -> ⠀⠀ ⠀ ⠀ で入力して次へ
    {"type": "fill", "selector": "input#displayName, input[name='displayName'], input[id*='name']", "value_env": "TEST_DISPLAY_NAME"},
    {"type": "click", "selector": "button[data-testid='submit'], button[type='submit']"},
    {"type": "wait", "seconds": 2},
    
    # 8. 生年月日を18歳〜60歳未満で入力 ＆ 性別「無回答」を選択
    {"type": "fill", "selector": "input#year, input[name='year']", "value_env": "TEST_BIRTH_YEAR"},
    {"type": "fill", "selector": "input#day, input[name='day']", "value_env": "TEST_BIRTH_DAY"},
    # 月の選択（セレクトボックスまたは入力に対応）
    {"type": "select_or_fill", "selector": "select#month, select[name='month'], input#month", "value_env": "TEST_BIRTH_MONTH"},
    # 性別「無回答」の選択（Spotifyのラジオボタンやドロップダウンに対応）
    {"type": "click_if_exists", "selector": "input[id*='prefer-not-to-say'], label[for*='prefer-not-to-say'], input[value='prefer_not_to_say'], [data-testid*='gender-prefer-not-to-say']"},
    {"type": "click", "selector": "button[data-testid='submit'], button[type='submit']"},
    {"type": "wait", "seconds": 2},
    
    # 9. 利用規約三つともにチェックを入れる
    {"type": "check_all", "selectors": [
        "input[type='checkbox']",
        "label[for*='terms']",
        "[data-testid*='checkbox']"
    ]},
    
    # 10. 「登録する」をタップ
    {"type": "click", "selector": "button[data-testid='submit'], button[type='submit']"},
    
    # 11. 購入手続き画面（または認証画面）になったら人間へ引き渡し
    {"type": "human", "message": "購入手続き画面または認証画面になりました。操作を続けてください。"},
]

# 完了条件（購入手続き画面や完了URL）
COMPLETION_SELECTORS = [
    "[data-testid='payment-form']",
    "#payment-form",
    ".checkout-container",
]
COMPLETION_URL_PART = os.getenv("COMPLETION_URL_PART", "/checkout")

SELECTORS = {} # app.py側との互換用
