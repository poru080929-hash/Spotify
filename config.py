import os
import random
import string

# noVNCのURL
VNC_URL = os.getenv("VNC_URL", "http://localhost:6080/vnc.html")

# 完了判定用のURLパーツやCSSセレクタ
COMPLETION_URL_PART = "account/overview"
COMPLETION_SELECTORS = [
    "a[data-testid='account-overview']",
    "div[data-testid='user-profile']"
]

# 動的データ生成用のヘルパー関数
def generate_random_email():
    letters = string.ascii_lowercase + string.digits
    rand_str = ''.join(random.choice(letters) for _ in range(8))
    return f"{rand_str}@vel0x0.xyz"

def generate_secure_password():
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    digits = string.digits
    password_chars = [
        random.choice(upper),
        random.choice(digits)
    ]
    all_chars = lower + upper + digits
    password_chars.extend(random.choice(all_chars) for _ in range(8))
    random.shuffle(password_chars)
    return "".join(password_chars)

def get_special_display_name():
    return "⠀⠀ ⠀ ⠀"

def generate_random_birthdate():
    year = random.randint(1966, 2008)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return str(year), str(month), str(day)

# 動的データを事前に生成
current_email = generate_random_email()
current_password = generate_secure_password()
current_name = get_special_display_name()
birth_y, birth_m, birth_d = generate_random_birthdate()

# 自動化アクションの定義配列
ACTIONS = [
    # 1. SpotifyのLPへ移動
    {"type": "goto", "url": "https://www.spotify.com/jp/premium/"},
    
    # 2. 1ヶ月無料体験ボタンをクリック
    {"type": "click", "selector": "a[data-testid='signup-btn-link'], a[href*='purchase/offer']"},
    
    # 3. メールアドレス入力
    {"type": "fill", "selector": "input#username, input[name='username']", "value": current_email},
    
    # 4. 「次へ」ボタンを明示的にクリックして画面遷移させる
    {"type": "click", "selector": "button[data-testid='submit']"},
    
    # 5. パスワード入力画面のロード待ち
    {"type": "wait", "seconds": 3},
    
    # 6. パスワード入力（複数の候補セレクタで確実に捉える & Enter送信）
    {"type": "fill", "selector": "input[data-testid='password'], input[data-testid='new-password'], input[type='password']", "value": current_password, "press_enter": True},
    
    # 7. 画面遷移のロード待ち
    {"type": "wait", "seconds": 3},
    
    # 8. 名前入力（Enter送信）
    {"type": "fill", "selector": "input#displayName, input[name='displayName']", "value": current_name, "press_enter": True},
    
    # 9. 画面遷移のロード待ち
    {"type": "wait", "seconds": 3},
    
    # 10-12. 生年月日入力 (年・月・日)
    {"type": "fill", "selector": "input#year, input[name='year'], input[data-testid='birthDateYear']", "value": birth_y},
    {"type": "select", "selector": "select#month, select[name='month'], select[data-testid='birthDateMonth']", "value": birth_m},
    {"type": "fill", "selector": "input#day, input[name='day'], input[data-testid='birthDateDay']", "value": birth_d, "press_enter": True},
    
    # 13. 最終的な登録確認や人間による操作の補助
    {"type": "human", "message": "性別選択、利用規約チェック、最後の「登録する」ボタンを確認してください。"}
]
