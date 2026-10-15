import aiosqlite
import time

DB_NAME = "database.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                stars INTEGER DEFAULT 0,
                last_free_open REAL DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_name TEXT
            )
        """)
        await db.commit()

async def get_user(user_id: int, username: str = ""):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT stars, last_free_open, username FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                # Если юзернейм изменился, обновим его в базе
                if username and row[2] != username:
                    await db.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
                    await db.commit()
                return {"user_id": user_id, "username": username or row[2], "stars": row[0], "last_free_open": row[1]}
            
            # Если пользователя нет — создаем
            await db.execute("INSERT INTO users (user_id, username, stars, last_free_open) VALUES (?, ?, ?, ?)", (user_id, username, 0, 0))
            await db.commit()
            return {"user_id": user_id, "username": username, "stars": 0, "last_free_open": 0}

async def update_user_stars(user_id: int, amount: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET stars = stars + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()

async def update_last_free_open(user_id: int, timestamp: float):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET last_free_open = ? WHERE user_id = ?", (timestamp, user_id))
        await db.commit()

async def add_item_to_inventory(user_id: int, item_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO inventory (user_id, item_name) VALUES (?, ?)", (user_id, item_name))
        await db.commit()

async def get_inventory(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT item_name FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

async def get_top_players(limit: int = 10):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT user_id, username, stars FROM users ORDER BY stars DESC LIMIT ?", 
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{"user_id": row[0], "username": row[1], "stars": row[2]} for row in rows]