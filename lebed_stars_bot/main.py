import asyncio
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import database
import random
import os
from bot import get_bot_application

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bot_app = get_bot_application()

ADMIN_USERNAMES = ["@Olexser_9", "@Chayok_UKRAINE", "Olexser_9", "Chayok_UKRAINE"]

@app.on_event("startup")
async def startup():
    await database.init_db()
    await bot_app.initialize()
    await bot_app.start()
    asyncio.create_task(bot_app.updater.start_polling(drop_pending_updates=True))

@app.on_event("shutdown")
async def shutdown():
    await bot_app.stop()
    await bot_app.shutdown()

@app.get("/", response_class=HTMLResponse)
async def read_index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Файл index.html не найден</h1>"

ITEM_SELL_PRICES = {
    "🧸 Мишка": 10,
    "🎁 Подарок": 15,
    "🌹 Роза": 10,
    "❤️ Сердце": 10,
    "🚀 Ракета": 75,
    "💍 Кольцо": 75,
    "🏆 Кубок": 75,
    "💎 Алмаз": 75,
    "🍦 Мороженое": 300,
    "🗽 Статуя Свободы": 300,
    "🕶️ Снуп Догг": 300,
    "🎅 Шапка Деда Мороза": 300
}

CASES_CONFIG = {
    "case_1": {
        "name": "Бесплатный кейс",
        "price": 0,
        "cooldown": 86400,
        "drops": [
            {"type": "stars", "val": 1, "weight": 75},
            {"type": "stars", "val": 2, "weight": 10},
            {"type": "item", "val": "🧸 Мишка", "weight": 2.5},
            {"type": "item", "val": "🎁 Подарок", "weight": 2.5},
            {"type": "item", "val": "🌹 Роза", "weight": 2.5},
            {"type": "item", "val": "❤️ Сердце", "weight":2.55},
        ]
    },
    "case_2": {
        "name": "Кейс за 100 звёзд",
        "price": 100,
        "cooldown": 0,
        "drops": [
            {"type": "stars", "val": 50, "weight": 75},
            {"type": "stars", "val": 75, "weight": 10},
            {"type": "item", "val": "🚀 Ракета", "weight":2.55},
            {"type": "item", "val": "💍 Кольцо", "weight": 2.5},
            {"type": "item", "val": "🏆 Кубок", "weight": 2.5},
            {"type": "item", "val": "💎 Алмаз", "weight": 2.5},
        ]
    },
    "case_3": {
        "name": "Кейс за 500 звёзд",
        "price": 500,
        "cooldown": 0,
        "drops": [
            {"type": "stars", "val": 250, "weight": 75},
            {"type": "stars", "val": 400, "weight": 10},
            {"type": "item", "val": "🍦 Мороженое", "weight":2.55},
            {"type": "item", "val": "🗽 Статуя Свободы", "weight": 2.5},
            {"type": "item", "val": "🕶️ Снуп Догг", "weight": 2.5},
            {"type": "item", "val": "🎅 Шапка Деда Мороза", "weight":2.55},
        ]
    }
}

@app.post("/get_user")
async def get_user_data(data: dict):
    user_id = data.get("user_id")
    username = data.get("username", "Игрок")
    user_data = await database.get_user(user_id, username)
    
    # Флаг админа
    clean_username = username.lstrip("@")
    is_admin = clean_username in [a.lstrip("@") for a in ADMIN_USERNAMES]
    user_data["is_admin"] = is_admin
    return user_data

@app.post("/inventory")
async def get_inventory(data: dict):
    user_id = data.get("user_id")
    return await database.get_inventory(user_id)

@app.get("/top")
async def get_top():
    return await database.get_top_players()

@app.post("/sell_item")
async def sell_item(data: dict):
    user_id = data.get("user_id")
    item_id = data.get("item_id")
    
    item_name = await database.remove_item_from_inventory(item_id, user_id)
    if not item_name:
        raise HTTPException(status_code=400, detail="Предмет не найден")
        
    price = ITEM_SELL_PRICES.get(item_name, 10)
    await database.update_user_stars(user_id, price)
    return {"msg": f"Вы успешно продали {item_name} за {price} ⭐!", "added_stars": price}

@app.post("/open_case")
async def open_case(data: dict):
    user_id = data.get("user_id")
    case_id = data.get("case_id", "case_1")
    
    if case_id not in CASES_CONFIG:
        raise HTTPException(status_code=400, detail="Неверный кейс")
        
    case_info = CASES_CONFIG[case_id]
    user = await database.get_user(user_id)
    current_time = time.time()
    
    if case_id == "case_1":
        last_open = user.get("last_free_open", 0)
        time_passed = current_time - last_open
        if time_passed < case_info["cooldown"]:
            remaining = int(case_info["cooldown"] - time_passed)
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            return {"error": f"Бесплатный кейс будет доступен через {hours} ч. {minutes} мин."}
    
    if user.get("stars", 0) < case_info["price"]:
        return {"error": "Недостаточно звёзд на балансе!"}
    
    if case_info["price"] > 0:
        await database.update_user_stars(user_id, -case_info["price"])

    if case_id == "case_1":
        await database.update_last_free_open(user_id, current_time)

    drops = case_info["drops"]
    weights = [d["weight"] for d in drops]
    drop = random.choices(drops, weights=weights, k=1)[0]
    
    if drop["type"] == "stars":
        await database.update_user_stars(user_id, drop["val"])
        return {"type": "stars", "amount": drop["val"], "msg": f"Вам выпало {drop['val']} ⭐!"}
    else:
        await database.add_item_to_inventory(user_id, drop["val"])
        return {"type": "item", "name": drop["val"], "msg": f"Вам выпал предмет: {drop['val']}!"}

# --- ЭНДПОИНТЫ АДМИН-ПАНЕЛИ ---

@app.post("/admin/give_stars")
async def admin_give_stars(data: dict):
    admin_username = data.get("admin_username", "").lstrip("@")
    if admin_username not in [a.lstrip("@") for a in ADMIN_USERNAMES]:
        raise HTTPException(status_code=403, detail="Нет прав доступа")

    target = data.get("target")
    amount = int(data.get("amount", 0))

    user = await database.get_user_by_id_or_username(str(target))
    if not user:
        return {"error": "Пользователь не найден"}

    await database.update_user_stars(user["user_id"], amount)
    return {"msg": f"Успешно вычислено/добавлено {amount} ⭐ пользователю {user['username'] or user['user_id']}!"}

@app.post("/admin/give_item")
async def admin_give_item(data: dict):
    admin_username = data.get("admin_username", "").lstrip("@")
    if admin_username not in [a.lstrip("@") for a in ADMIN_USERNAMES]:
        raise HTTPException(status_code=403, detail="Нет прав доступа")

    target = data.get("target")
    item_name = data.get("item_name")

    user = await database.get_user_by_id_or_username(str(target))
    if not user:
        return {"error": "Пользователь не найден"}

    await database.add_item_to_inventory(user["user_id"], item_name)
    return {"msg": f"Предмет {item_name} успешно выдан пользователю {user['username'] or user['user_id']}!"}

@app.post("/admin/create_promo")
async def admin_create_promo(data: dict):
    admin_username = data.get("admin_username", "").lstrip("@")
    if admin_username not in [a.lstrip("@") for a in ADMIN_USERNAMES]:
        raise HTTPException(status_code=403, detail="Нет прав доступа")

    code = data.get("code")
    stars = int(data.get("stars", 0))
    max_uses = int(data.get("max_uses", 1))

    await database.add_promo_code(code, stars, max_uses)
    return {"msg": f"Промокод '{code.upper()}' на {stars} ⭐ (лимит: {max_uses}) успешно создан!"}

@app.post("/use_promo")
async def use_promo(data: dict):
    user_id = data.get("user_id")
    code = data.get("code", "")
    if not code:
        return {"error": "Введите промокод"}
    return await database.activate_promo_code(user_id, code)