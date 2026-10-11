import aiosqlite

DB_NAME = "game.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                stars INTEGER DEFAULT 0,
                balance_stars REAL DEFAULT 0,
                free_case_time TEXT DEFAULT ''
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_name TEXT,
                reward_stars INTEGER
            )
        """)
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT stars, balance_stars, free_case_time FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return {"stars": row[0], "balance_stars": row[1], "free_case_time": row[2]}
            await db.execute("INSERT INTO users (user_id, stars, balance_stars, free_case_time) VALUES (?, 0, 0, '')", (user_id,))
            await db.commit()
            return {"stars": 0, "balance_stars": 0, "free_case_time": ""}

async def open_case(user_id: int, reward_stars: int, item_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        user = await get_user(user_id)
        new_stars = user["stars"] + reward_stars
        new_balance = user["balance_stars"] + reward_stars
        
        # Обновляем общий баланс звезд
        await db.execute("UPDATE users SET stars = ?, balance_stars = ? WHERE user_id = ?", (new_stars, new_balance, user_id))
        # Добавляем предмет в инвентарь
        await db.execute("INSERT INTO inventory (user_id, item_name, reward_stars) VALUES (?, ?, ?)", (user_id, item_name, reward_stars))
        await db.commit()
        
        return {"stars": new_stars, "balance_stars": new_balance, "reward": reward_stars, "item": item_name}

async def get_inventory(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT item_name, reward_stars FROM inventory WHERE user_id = ? ORDER BY id DESC", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [{"item_name": row[0], "reward_stars": row[1]} for row in rows]

async def get_top_players():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, stars FROM users ORDER BY stars DESC LIMIT 10") as cursor:
            rows = await cursor.fetchall()
            return [{"user_id": row[0], "stars": row[1]} for row in rows]