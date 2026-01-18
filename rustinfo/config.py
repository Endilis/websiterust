import os
from dotenv import load_dotenv
import time
from discord.ext import tasks
current_token_index = 0
requests_count = 0  # 🔹 Глобальный счетчик запросов
requests_failed = 0  # 🔥 Счетчик отказов (429 Too Many Requests)
last_request_time = time.time()
# Загружаем переменные окружения из .env
load_dotenv()

# Получаем токены из окружения
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
BATTLEMETRICS_TOKENS = os.getenv("BATTLEMETRICS_TOKENS").split(",")  # 🔹 Список токенов
SERVER_ID = int(os.getenv("SERVER_ID", 0))
# Webhook URL для дублирования логов в канал Discord (оставьте пустым, чтобы отключить)
LOG_WEBHOOK_URL = os.getenv("LOG_WEBHOOK_URL", "").strip()
#LOG_WEBHOOK_URL = os.getenv("LOG_WEBHOOK_URL", "").strip()
# Проверяем, загружены ли данные
if not DISCORD_BOT_TOKEN:
    raise ValueError("Ошибка: DISCORD_BOT_TOKEN не найден в .env файле!")
if not BATTLEMETRICS_TOKENS:
    raise ValueError("Ошибка: BATTLEMETRICS_TOKEN не найден в .env файле!")

def switch_battlemetrics_token():
    """Переключает токен BattleMetrics, если лимит запросов превышен."""
    global current_token_index, requests_count, last_request_time

    elapsed_time = time.time() - last_request_time  # 🔄 Сколько времени прошло с последнего сброса

    # 🔹 Если прошло больше 60 секунд — сброс счётчика
    if elapsed_time > 60:
        requests_count = 0
        last_request_time = time.time()
        return BATTLEMETRICS_TOKENS[current_token_index]

    # 🔹 Если запросов больше 60 — переключаем токен
    if requests_count >= 60:
        current_token_index = (current_token_index + 1) % len(BATTLEMETRICS_TOKENS)
        requests_count = 0  # ✅ Обнуляем счетчик
        last_request_time = time.time()
        print(f"🔄 Переключение токена BattleMetrics! Новый токен: {current_token_index + 1}/{len(BATTLEMETRICS_TOKENS)}")

    return BATTLEMETRICS_TOKENS[current_token_index]

@tasks.loop(minutes=1)
async def reset_request_counters():
    """Сбрасывает счетчики запросов и отказов каждую минуту и выводит статистику."""
    global requests_count, requests_failed
    print(f"📊 Запросов за последнюю минуту: {requests_count}")
    print(f"❌ Отказов за последнюю минуту: {requests_failed}")
    requests_count = 0
    requests_failed = 0

async def track_api_request(response_status):
    """Отслеживает количество запросов и отказов к API BattleMetrics."""
    global requests_count, requests_failed
    requests_count += 1
    if response_status >= 400:
        requests_failed += 1

