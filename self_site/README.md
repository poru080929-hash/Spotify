# 管理下サイト用フォームテスト

このフォルダは、自分が管理するテストサイトのフォームを対象にしたSeleniumテスト用のサンプルです。既存のルートアプリとは分離しています。

## 設定

`config.py` のセレクタをサイトのHTMLに合わせて変更できます。URLやテスト値は環境変数でも変更できます。

```bash
export SITE_URL=https://your-test-site.example/signup
export TEST_EMAIL=test@example.test
export TEST_PASSWORD='only-for-local-testing'
export TEST_DISPLAY_NAME='Test User'
export TEST_BIRTH_YEAR=1990
export TEST_BIRTH_MONTH=5
export TEST_BIRTH_DAY=15
```

## Docker

```bash
docker build -t self-site-test .
docker run --rm -p 5000:5000 -p 6080:6080 \
  -e SITE_URL=https://your-test-site.example/signup \
  self-site-test
```

ブラウザで `http://localhost:5000` を開き、noVNC画面は `http://localhost:6080/vnc.html?autoconnect=true&resize=scale` で開きます。外部ホスティングで利用する場合は、VNCのWebSocketポートを別途公開できる構成が必要です。Flaskの通常のHTTPプロキシでWebSocketを中継しないでください。

## 注意

- 管理下のテストサイトとテストデータだけで使用してください。
- 本番の個人情報や本物のパスワードを設定しないでください。
- 認証やCAPTCHAを自動突破する処理は含めていません。必要な確認は人間が画面上で行います。
- 公開環境では認証、アクセス制限、TLS、セッション分離を追加してください。
- Gunicornのworker数は1にしています。ブラウザをプロセス内で保持するためです。
