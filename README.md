# 管理下サイト用の汎用フォームテスト

このアプリは、自分が管理するテストサイトをSeleniumで操作するサンプルです。`app.py`は一度設定したら、操作を変えるときは基本的に`config.py`だけを編集します。

## 変更するファイルは `config.py` だけ

`ACTIONS`を上から順に実行します。

```python
ACTIONS = [
    {"type": "goto", "url": SITE_URL},
    {"type": "click", "selector": "button#start"},
    {"type": "fill", "selector": "input[name='email']", "value_env": "TEST_EMAIL"},
    {"type": "fill", "selector": "input[name='password']", "value_env": "TEST_PASSWORD"},
    {"type": "select", "selector": "select[name='country']", "value": "JP"},
    {"type": "check", "selector": "input[name='terms']"},
    {"type": "wait", "seconds": 2},
    {"type": "scroll", "y": 500},
    {"type": "human", "message": "画面を確認して操作してください"},
]
```

使用できる操作：

- `goto`: ページを開く。`url`が必要
- `click`: 要素をクリック。`selector`が必要
- `fill`: 文字を入力。`selector`と`value`または`value_env`が必要
- `select`: selectを選択。`selector`と`value`が必要
- `check`: チェックボックスをオンにする。`selector`が必要
- `wait`: 待機。`seconds`が必要
- `scroll`: 縦スクロール。`y`が必要
- `human`: noVNCで人間が操作し、「人間操作を完了して再開」を押す

## セレクタの例

```python
"button#start"
"input#email"
"input[name='email']"
"button[data-testid='continue']"
"select[name='country']"
```

対象サイトのHTMLに合わせて、`selector`を変更してください。`app.py`を変更する必要はありません。

## 入力値

パスワードなどは設定ファイルへ直接書かず、環境変数を使えます。

```bash
export TEST_EMAIL=test@example.test
export TEST_PASSWORD='only-for-local-testing'
```

`value_env`を使います。

```python
{"type": "fill", "selector": "input[name='password']", "value_env": "TEST_PASSWORD"}
```

## 完了判定

`COMPLETION_SELECTORS`または`COMPLETION_URL_PART`を`config.py`で変更します。

```python
COMPLETION_SELECTORS = ["#signup-complete"]
COMPLETION_URL_PART = "/signup/complete"
```

## Docker

```bash
docker build -t self-site-test .
docker run --rm -p 5000:5000 -p 6080:6080 \
  -e SITE_URL=https://your-test-site.example/signup \
  -e TEST_EMAIL=test@example.test \
  -e TEST_PASSWORD='only-for-local-testing' \
  self-site-test
```

`http://localhost:5000`を開き、noVNCは`http://localhost:6080/vnc.html?autoconnect=true&resize=scale`です。

## 注意

管理下のテストサイトとテストデータだけで使用してください。本番の個人情報や本物のパスワードは使わないでください。認証やCAPTCHAを自動突破する処理は含めていません。
