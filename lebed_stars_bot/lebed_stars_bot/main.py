import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import database
import random
import os
import bot  # Подключаем наш файл bot.py

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # 1. Инициализируем базу данных
    await database.init_db()
    
    # 2. Запускаем Telegram-бота в фоновом режиме
    asyncio.create_task(bot.start_bot())

@app.get("/", response_class=HTMLResponse)
async def read_index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Файл index.html не найден</h1>"

@app.post("/get_user")
async def get_user_data(data: dict):
    user_id = data.get("user_id")
    return await database.get_user(user_id)

@app.post("/inventory")
async def get_inventory(data: dict):
    user_id = data.get("user_id")
    return await database.get_inventory(user_id)

@app.post("/open_case")
async def open_case(data: dict):
    user_id = data.get("user_id")
    possible_drops = [
        {"name": "🍀 Счастливый клевер", "stars": 1},
        {"name": "🎁 Золотой подарок", "stars": 5},
        {"name": "👑 Корона кейса", "stars": 25},
        {"name": "💎 Легендарная звезда", "stars": 50}
    ]
    drop = random.choices(possible_drops, weights=[50, 30, 15, 5], k=1)[0]
    return await database.open_case(user_id, drop["stars"], drop["name"])

@app.get("/top")
async def get_top():
    return await database.get_top_players()