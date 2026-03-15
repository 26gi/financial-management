# 家計簿 KAKEIBO（FastAPI + Supabase版）

## ファイル構成

```
kakeibo-fastapi/
├── client/                ← フロントエンド（Netlifyにデプロイ）
│   ├── index.html
│   ├── manifest.json
│   └── sw.js
└── server/                ← バックエンド（Renderにデプロイ）
    ├── main.py            ← FastAPI アプリ本体
    ├── requirements.txt   ← Pythonパッケージ一覧
    ├── Procfile           ← Render起動コマンド
    └── .env.example       ← 環境変数テンプレート
```

---

## セットアップ手順（全部無料）

### ステップ 1：Supabase でPostgreSQLを準備する

1. https://supabase.com でアカウント作成
2. 「New Project」でプロジェクト作成（名前は何でもOK）
3. 左メニュー「Project Settings」→「Database」
4. 「Connection string」→「URI」をコピー
   ```
   postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres
   ```
   ※ `[PASSWORD]` は作成時に設定したパスワード

### ステップ 2：APIサーバーを Render にデプロイする

1. `server/` フォルダをGitHubにpush
   ```bash
   git init
   git add .
   git commit -m "init"
   git remote add origin https://github.com/あなたのID/kakeibo-server.git
   git push -u origin main
   ```

2. https://render.com でアカウント作成

3. 「New +」→「Web Service」→ GitHubリポジトリを選択

4. 以下のように設定：
   | 項目 | 値 |
   |---|---|
   | Name | kakeibo-api（任意） |
   | Environment | Python 3 |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

5. 「Environment Variables」に追加：
   ```
   DATABASE_URL = postgresql://postgres:...（Supabaseの接続文字列）
   ```

6. 「Create Web Service」→ デプロイ完了後のURL（例: `https://kakeibo-api.onrender.com`）をメモ

### ステップ 3：フロントエンドのAPIアドレスを更新する

`client/index.html` を開き、以下を編集：

```javascript
// 変更前
: 'https://your-server.onrender.com/api';

// 変更後（Renderで発行されたURL）
: 'https://kakeibo-api.onrender.com/api';
```

### ステップ 4：フロントエンドを Netlify にデプロイする

1. https://netlify.com でアカウント作成
2. `client/` フォルダをブラウザにドラッグ&ドロップ
3. 発行されたURLでアクセス可能に

### ステップ 5：iPhoneにインストール

1. Safariで開く → 共有ボタン（□↑）→「ホーム画面に追加」

---

## ローカルでの動作確認（任意）

```bash
cd server
python -m venv venv
source venv/bin/activate    # Windowsは: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # .envを作成してDATABASE_URLを設定
uvicorn main:app --reload
```

APIドキュメント（Swagger UI）は http://localhost:8000/docs で確認できます。

---

## 家族での共有方法

アプリ起動時のログイン画面で **同じユーザーIDを入力** するだけです。

```
例：ユーザーID → "yamada_family"
```

---

## 同期の仕組み

| 状況 | 動作 |
|---|---|
| オンライン | 操作と同時にSupabase（PostgreSQL）へ保存 |
| オフライン | localStorageに保存・「未同期」マーク表示 |
| オフライン→復帰 | 自動で未同期データをサーバーへ送信 |
| 定期同期 | 30秒ごとに他端末の変更を取得 |

---

## 無料枠の目安

| サービス | 無料枠 |
|---|---|
| Supabase | 500MB DB・月50,000リクエスト |
| Render | 月750時間（1サービスなら常時稼働） |
| Netlify | 月100GB転送 |
