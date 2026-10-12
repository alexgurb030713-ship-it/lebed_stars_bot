import asyncio
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

# Конфигурация кейсов, цен и шансов выпадения
CASES_CONFIG = {
    "case_1": {
        "name": "Бесплатный кейс",
        "price": 0,
        "drops": [
            {"type": "stars", "val": 10, "weight": 75},
            {"type": "stars", "val": 25, "weight": 10},
            {"type": "item", "val": "🧸 Мишка", "weight": 5},
            {"type": "item", "val": "🎁 Подарок", "weight": 2.5},
            {"type": "item", "val": "🌹 Роза", "weight": 2.5},
            {"type": "item", "val": "❤️ Сердце", "weight": 5},
        ]
    },
    "case_2": {
        "name": "Кейс за 100 звёзд",
        "price": 100,
        "drops": [
            {"type": "stars", "val": 50, "weight": 75},
            {"type": "stars", "val": 75, "weight": 10},
            {"type": "item", "val": "🚀 Ракета", "weight": 5},
            {"type": "item", "val": "💍 Кольцо", "weight": 2.5},
            {"type": "item", "val": "🏆 Кубок", "weight": 2.5},
            {"type": "item", "val": "💎 Алмаз", "weight": 5},
        ]
    },
    "case_3": {
        "name": "Кейс за 500 звёзд",
        "price": 500,
        "drops": [
            {"type": "stars", "val": 250, "weight": 75},
            {"type": "stars", "val": 400, "weight": 10},
            {"type": "item", "val": "🍦 Мороженое", "weight": 5},
            {"type": "item", "val": "🗽 Статуя Свободы", "weight": 2.5},
            {"type": "item", "val": "🕶️ Снуп Догг", "weight": 2.5},
            {"type": "item", "val": "🎅 Шапка Деда Мороза", "weight": 5},
        ]
    }
}

@app.post("/get_user")
async def get_user_data(data: dict):
    user_id = data.get("user_id")
    return await database.get_user(user_id)

@app.post("/inventory")
async def get_inventory(data: dict):
    user_id = data.get("user_id")
    items = await database.get_inventory(user_id)
    return items

@app.get("/top")
async def get_top():
    return await database.get_top_players()

@app.post("/open_case")
async def open_case(data: dict):
    user_id = data.get("user_id")
    case_id = data.get("case_id", "case_1")
    
    if case_id not in CASES_CONFIG:
        raise HTTPException(status_code=400, detail="Неверный кейс")
        
    case_info = CASES_CONFIG[case_id]
    user = await database.get_user(user_id)
    
    if user.get("stars", 0) < case_info["price"]:
        return {"error": "Недостаточно звёзд на балансе!"}
    
    if case_info["price"] > 0:
        await database.update_user_stars(user_id, -case_info["price"])

    drops = case_info["drops"]
    weights = [d["weight"] for d in drops]
    drop = random.choices(drops, weights=weights, k=1)[0]
    
    if drop["type"] == "stars":
        await database.update_user_stars(user_id, drop["val"])
        return {"type": "stars", "amount": drop["val"], "msg": f"Вам выпало {drop['val']} ⭐!"}
    else:
        await database.add_item_to_inventory(user_id, drop["val"])
        return {"type": "item", "name": drop["val"], "msg": f"Вам выпал предмет: {drop['val']}!"}