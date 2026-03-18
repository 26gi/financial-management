from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Optional
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

# ---- DB接続プール ----
db_pool: asyncpg.Pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    db_pool = await asyncpg.create_pool(
        dsn=os.environ["DATABASE_URL"],
        ssl="require",
        min_size=1,
        max_size=5,
    )
    await init_db()
    yield
    await db_pool.close()

app = FastAPI(title="家計簿 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番では特定のドメインに絞ってください
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- DB初期化 ----
async def init_db():
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          TEXT PRIMARY KEY,
                user_id     TEXT NOT NULL,
                type        TEXT NOT NULL CHECK (type IN ('income','expense')),
                amount      INTEGER NOT NULL,
                memo        TEXT DEFAULT '',
                date        TEXT NOT NULL,
                cat         TEXT NOT NULL,
                created_at  TIMESTAMPTZ DEFAULT NOW(),
                updated_at  TIMESTAMPTZ DEFAULT NOW(),
                deleted     BOOLEAN DEFAULT FALSE
            );
            CREATE TABLE IF NOT EXISTS budgets (
                user_id     TEXT NOT NULL,
                cat         TEXT NOT NULL,
                amount      INTEGER NOT NULL,
                updated_at  TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (user_id, cat)
            );
            CREATE INDEX IF NOT EXISTS idx_tx_user    ON transactions(user_id);
            CREATE INDEX IF NOT EXISTS idx_tx_updated ON transactions(updated_at);
        """)

# ---- 認証（シンプルなユーザーID方式） ----
async def get_user_id(x_user_id: str = Header(..., alias="x-user-id")) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="x-user-id header required")
    return x_user_id

# ---- Pydanticモデル ----
class Transaction(BaseModel):
    id: str
    type: str
    amount: int
    memo: str = ""
    date: str
    cat: str
    deleted: bool = False

class SyncRequest(BaseModel):
    transactions: list[Transaction]

class BudgetsRequest(BaseModel):
    budgets: dict[str, int]

# ---- 取引エンドポイント ----

@app.get("/api/transactions")
async def get_transactions(
    since: str = "1970-01-01T00:00:00Z",
    user_id: str = Depends(get_user_id),
):
    """since以降に更新された取引を返す（差分同期用）"""
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, user_id, type, amount, memo, date, cat,
                   updated_at, deleted
            FROM transactions
            WHERE user_id = $1 AND updated_at > $2::timestamptz
            ORDER BY updated_at ASC
            """,
            user_id, since,
        )
    return [dict(r) for r in rows]


@app.post("/api/transactions/sync")
async def sync_transactions(
    body: SyncRequest,
    user_id: str = Depends(get_user_id),
):
    """クライアントの未同期データをまとめてupsert"""
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            for tx in body.transactions:
                await conn.execute(
                    """
                    INSERT INTO transactions
                        (id, user_id, type, amount, memo, date, cat, updated_at, deleted)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,NOW(),$8)
                    ON CONFLICT (id) DO UPDATE SET
                        type       = EXCLUDED.type,
                        amount     = EXCLUDED.amount,
                        memo       = EXCLUDED.memo,
                        date       = EXCLUDED.date,
                        cat        = EXCLUDED.cat,
                        updated_at = NOW(),
                        deleted    = EXCLUDED.deleted
                    """,
                    tx.id, user_id, tx.type, tx.amount,
                    tx.memo, tx.date, tx.cat, tx.deleted,
                )
    return {"synced": len(body.transactions)}


# ---- 予算エンドポイント ----

@app.get("/api/budgets")
async def get_budgets(user_id: str = Depends(get_user_id)):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT cat, amount FROM budgets WHERE user_id = $1",
            user_id,
        )
    return {r["cat"]: r["amount"] for r in rows}


@app.put("/api/budgets")
async def update_budgets(
    body: BudgetsRequest,
    user_id: str = Depends(get_user_id),
):
    async with db_pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM budgets WHERE user_id = $1", user_id
            )
            for cat, amount in body.budgets.items():
                await conn.execute(
                    "INSERT INTO budgets (user_id, cat, amount) VALUES ($1,$2,$3)",
                    user_id, cat, amount,
                )
    return {"ok": True}


# ---- ヘルスチェック ----
@app.get("/api/health")
async def health():
    return {"ok": True}
