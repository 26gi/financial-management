# ---- ビルドステージ ----
FROM python:3.12-slim AS builder

WORKDIR /app

# 依存パッケージのみ先にインストール（レイヤーキャッシュを活用）
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- 実行ステージ ----
FROM python:3.12-slim

WORKDIR /app

# ビルドステージからインストール済みパッケージをコピー
COPY --from=builder /install /usr/local

# アプリコードをコピー
COPY main.py .

# 非rootユーザーで実行（セキュリティ対策）
RUN useradd -m appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
