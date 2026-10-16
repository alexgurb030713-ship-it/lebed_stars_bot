import aiosqlite

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
        # Таблица промокодов
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                stars INTEGER,
                max_uses INTEGER,
                used_count INTEGER DEFAULT 0
            )
        """)
        # История активаций промокодов пользователями
        await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_history (
                code TEXT,
                user_id INTEGER,
                PRIMARY KEY (code, user_id)
            )
        """)
        await db.commit()

async def get_user(user_id: int, username: str = ""):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT stars, last_free_open, username FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                if username and row[2] != username:
                    await db.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
                    await db.commit()
                return {"user_id": user_id, "username": username or row[2], "stars": row[0], "last_free_open": row[1]}
            
            await db.execute("INSERT INTO users (user_id, username, stars, last_free_open) VALUES (?, ?, ?, ?)", (user_id, username, 0, 0))
            await db.commit()
            return {"user_id": user_id, "username": username, "stars": 0, "last_free_open": 0}

async def get_user_by_id_or_username(identifier: str):
    async with aiosqlite.connect(DB_NAME) as db:
        clean_id = identifier.strip()
        if clean_id.isdigit():
            user_id = int(clean_id)
            async with db.execute("SELECT user_id, username, stars FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {"user_id": row[0], "username": row[1], "stars": row[2]}
        else:
            username = clean_id.lstrip("@")
            async with db.execute("SELECT user_id, username, stars FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(username) = LOWER(?)", (username, f"@{username}")) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {"user_id": row[0], "username": row[1], "stars": row[2]}
    return None

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
        async with db.execute("SELECT id, item_name FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [{"id": row[0], "name": row[1]} for row in rows]

async def remove_item_from_inventory(item_id: int, user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT item_name FROM inventory WHERE id = ? AND user_id = ?", (item_id, user_id)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            item_name = row[0]
            await db.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
            await db.commit()
            return item_name

async def get_top_players(limit: int = 10):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT user_id, username, stars FROM users ORDER BY stars DESC LIMIT ?", 
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{"user_id": row[0], "username": row[1], "stars": row[2]} for row in rows]

# Функции админки и промокодов
async def add_promo_code(code: str, stars: int, max_uses: int):
    async with aiosqlite.connect(DB_NAME) as db:
        code_upper = code.strip().upper()
        await db.execute(
            "INSERT OR REPLACE INTO promo_codes (code, stars, max_uses, used_count) VALUES (?, ?, ?, 0)",
            (code_upper, stars, max_uses)
        )
        await db.commit()

async def activate_promo_code(user_id: int, code: str):
    async with aiosqlite.connect(DB_NAME) as db:
        code_upper = code.strip().upper()
        
        # Проверяем сущестование промокода
        async with db.execute("SELECT stars, max_uses, used_count FROM promo_codes WHERE code = ?", (code_upper,)) as cursor:
            promo = await cursor.fetchone()
            if not promo:
                return {"error": "Промокод не существует"}
            
            stars, max_uses, used_count = promo

        if used_count >= max_uses:
            return {"error": "Лимит активаций промокода исчерпан"}

        # Проверяем, активировал ли уже юзер
        async with db.execute("SELECT 1 FROM promo_history WHERE code = ? AND user_id = ?", (code_upper, user_id)) as cursor:
            if await cursor.fetchone():
                return {"error": "Вы уже активировали этот промокод"}

        # Начисляем бонус
        await db.execute("INSERT INTO promo_history (code, user_id) VALUES (?, ?)", (code_upper, user_id))
        await db.execute("UPDATE promo_codes SET used_count = used_count + 1 WHERE code = ?", (code_upper,))
        await db.execute("UPDATE users SET stars = stars + ? WHERE user_id = ?", (stars, user_id))
        await db.commit()

        return {"msg": f"Промокод активирован! Вам зачислено {stars} ⭐"}