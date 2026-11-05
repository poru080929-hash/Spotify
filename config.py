import os
import random
import string

# VNCは使用せず、完全自動化に特化
VNC_URL = "#"

COMPLETION_URL_PART = "account/overview"
COMPLETION_SELECTORS = [
    "a[data-testid='account-overview']",
    "div[data-testid='user-profile']"
]

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

current_email = generate_random_email()
current_password = generate_secure_password()
current_name = get_special_display_name()
birth_y, birth_m, birth_d = generate_random_birthdate()

ACTIONS = [
    {"type": "goto", "url": "https://www.spotify.com/jp/premium/"},
    {"type": "click", "selector": "a[aria-label*='Premium Standardの購入画面に進みます'], a[href*='purchase/offer'], a[data-testid='signup-btn-link']"},
    {"type": "fill", "selector": "input#username, input[name='username']", "value": current_email},
    {"type": "click", "selector": "button[data-testid='submit'], button[type='submit']"},
    {"type": "wait", "seconds": 2},
    {"type": "fill", "selector": "input#new-password, input[name='new-password'], input[data-testid='password'], input[type='password']", "value": current_password},
    {"type": "click", "selector": "button[data-testid='submit'], button[type='submit']"},
    {"type": "wait", "seconds": 2},
    {"type": "fill", "selector": "input#displayName, input[name='displayName']", "value": current_name},
    {"type": "click", "selector": "button[data-testid='submit'], button[type='submit']"},
    {"type": "wait", "seconds": 2},
    {"type": "fill", "selector": "input#year, input[name='year'], input[data-testid='birthDateYear']", "value": birth_y},
    {"type": "select", "selector": "select#month, select[name='month'], select[data-testid='birthDateMonth']", "value": birth_m},
    {"type": "fill", "selector": "input#day, input[name='day'], input[data-testid='birthDateDay']", "value": birth_d},
    {"type": "click", "selector": "button[data-testid='submit'], button[type='submit']"},
    {"type": "human", "message": "登録内容を確認してください。"}
]
