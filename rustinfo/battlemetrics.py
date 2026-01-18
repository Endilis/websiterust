### battlemetrics.py
import aiohttp
from config import switch_battlemetrics_token, track_api_request
from datetime import datetime, timedelta
from database import get_player_ids_from_db
import json

#Поиск игрока по всей базе Battlemetrics
async def search_player_by_nickname(nickname):
    """Ищет игрока по точному совпадению ника и получает информацию о нем"""
    headers = {"Authorization": f"Bearer {switch_battlemetrics_token()}"}

    # 🔍 Используем точное совпадение, оборачивая ник в кавычки
    search_url = f"https://api.battlemetrics.com/players?filter[search]=\"{nickname}\"&page[size]=100&include=server&sort=-lastSeen"

    async with aiohttp.ClientSession() as session:
        async with session.get(search_url, headers=headers) as response:
            await track_api_request(response.status)
            if response.status != 200:
                print(f"Ошибка запроса: {response.status}")
                return []

            data = await response.json()
            players_info = []
            now = datetime.utcnow()  # Текущее время
            for player in data.get("data", []):
                attributes = player.get("attributes", {})
                player_name = attributes.get("name", "")

                # ✅ Дополнительно проверяем совпадение (если API не сработает идеально)
                if player_name != nickname:
                    continue

                player_id = player["id"]
                relationships = player.get("relationships", {})
                last_seen = "Неизвестно"
                is_online = False
                server_name = "Не играет"

                # ✅ Проверяем, есть ли информация о сервере
                server_data = relationships.get("servers", {}).get("data", [])
                if server_data:
                    latest_server = max(server_data, key=lambda s: s.get("meta", {}).get("lastSeen", "0000-00-00T00:00:00"))  # Берём последний сервер
                    meta_data = latest_server.get("meta", {})

                    # ✅ Проверяем последний вход и онлайн статус
                    last_seen_raw = meta_data.get("lastSeen", "Неизвестно")
                    if last_seen_raw != "Неизвестно":
                        try:
                            last_seen_dt = datetime.strptime(last_seen_raw[:19], "%Y-%m-%dT%H:%M:%S")
                            last_seen = last_seen_dt.strftime("%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            last_seen = "Формат даты неизвестен"
                            last_seen_dt = None
                    else:
                        last_seen_dt = None

                    if meta_data.get("online", False):
                        is_online = True
                    elif last_seen_dt and (now - last_seen_dt) < timedelta(minutes=10):
                        is_online = True  # Если `last_seen` меньше 10 минут — считаем, что онлайн

                    # ✅ Находим название сервера в `included`
                    for included in data.get("included", []):
                        if included["id"] == latest_server.get("id") and included["type"] == "server":
                            server_name = included.get("attributes", {}).get("name", "Неизвестно")
                            break

                players_info.append({
                    "id": player_id,
                    "name": player_name,
                    "is_online": "🟢 Онлайн" if is_online else "🔴 Оффлайн",
                    "server_name": server_name,
                    "last_seen": last_seen
                })
    #print(players_info)
    return players_info




async def fetch_battlemetrics_data(server_id):
    """Запрашивает данные с BattleMetrics API и считает отказы"""
    headers = {"Authorization": f"Bearer {switch_battlemetrics_token()}"}
    url = f"https://api.battlemetrics.com/servers/{server_id}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                await track_api_request(response.status)
                if response.status == 200:
                    return await response.json()

                print(f"⚠ Ошибка API: {response.status}")
                return None

    except aiohttp.ClientError as e:
        print(f"❌ Ошибка сети: {e}")
        return None
    except Exception as e:
        print(f"🚨 Неизвестная ошибка: {e}")
        return None


def generate_progress_bar(players, max_players, bar_length=20):
    """Генерирует прогресс-бар для количества игроков на сервере."""

    # ✅ Если players — это список, берём его длину
    if isinstance(players, list):
        players = len(players)

    # ✅ Проверяем, что players — это число
    if not isinstance(players,  int):
        players = 0  # Если нет, устанавливаем 0
    if not isinstance(max_players,  int):
        max_players = 0  # Если нет, устанавливаем 0
    # ✅ Преобразуем max_players в int, если это строка или None
    try:
        max_players = int(max_players)      
    except (ValueError, TypeError):
        max_players = 1  # 🔹 Если ошибка, ставим 1 (чтобы избежать деления на 0)

    # ✅ Защита от деления на 0
    if max_players <= 0:
        max_players = 1

    # ✅ Ограничиваем количество игроков, чтобы не превышало `max_players`
    players = min(players, max_players)

    # 🔹 Генерируем прогресс-бар
    filled = int((players / max_players) * bar_length) if max_players > 0 else 0
    empty = bar_length - filled
    return "🟩" * filled + "🟥" * empty  # 🟩 Заполненная часть | 🟥 Пустая часть


def get_progress_image(players, max_players):
    """Определяет, какой спрайт прогресс-бара использовать"""
    # Если players - список, берем его длину
    if isinstance(players, list):
        players = len(players)

    # Преобразуем max_players в int, если это строка
    try:
        max_players = int(max_players)
    except ValueError:
        max_players = 1  # Защита от деления на 0

    # Если игроков больше, чем максимум, ограничиваем их
    players = min(players, max_players)

    # Вычисляем процент заполненности
    percent = int((players / max_players) * 100) if max_players > 0 else 0

    # Приводим к ближайшему значению (0%, 10%, 20% ... 100%)
    progress_level = (percent // 10) * 10

    # Загружаем соответствующее изображение (URL должны быть загружены заранее)
    image_urls = {
        0: "https://cdn.discordapp.com/attachments/1340093391278440541/1340093456420442162/progress_0.png?ex=67b11ac9&is=67afc949&hm=e6867c7dc685b2cdac74f7259c663d6a4bb3ec79eb502f83a92b3e980a748ab3&",
        10: "https://cdn.discordapp.com/attachments/1340093391278440541/1340093509301960785/progress_10.png?ex=67b11ad6&is=67afc956&hm=809f9578aaf36abddae766248172710f475f1336884e8f142d6c3f3df60d925e&",
        20: "https://cdn.discordapp.com/attachments/1340093391278440541/1340093525181599745/progress_20.png?ex=67b11ada&is=67afc95a&hm=8d7871253b3ad70f960b8faba90fa09d1a573b2f8ce3816f8e7cd0792dd1198f&",
        30: "https://cdn.discordapp.com/attachments/1340093391278440541/1340093544442101882/progress_30.png?ex=67b11ade&is=67afc95e&hm=f1f939e80fddbcdc55b2953869911616f3fa8feb43243d23cc9014311fa2b3c7&",
        40: "https://cdn.discordapp.com/attachments/1340093391278440541/1340093565589655654/progress_40.png?ex=67b11ae3&is=67afc963&hm=7ce61334f1dabeb86998548efce06e6b9915f7d3b57b94ea55d3786a479bc560&",
        50: "https://cdn.discordapp.com/attachments/1340093391278440541/1340093579430989844/progress_50.png?ex=67b11ae7&is=67afc967&hm=df628e8c46b4301b1dd16cc8bfe14f8b96d75cba4cecb22515032b2ee6952f88&",
        60: "https://cdn.discordapp.com/attachments/1340093391278440541/1340093602864304168/progress_60.png?ex=67b11aec&is=67afc96c&hm=535dffd9a591d7860163d9446320e04908a748f49157e8d7a8931a01fc959b65&",
        70: "https://cdn.discordapp.com/attachments/1340093391278440541/1340093622376464527/progress_70.png?ex=67b11af1&is=67afc971&hm=e579f105bfe20c20259a528c43e8040648e7832c4f50c241cb3acb0473cb2498&",
        80: "https://cdn.discordapp.com/attachments/1340093391278440541/1340093734200803408/progress_80.png?ex=67b11b0b&is=67afc98b&hm=8b81cc611c6838dc0f8f147f41fb8f1baebf74f3989fc0550e5b0242d69b5ed5&",
        90: "https://cdn.discordapp.com/attachments/1340093391278440541/1340093745403531344/progress_90.png?ex=67b11b0e&is=67afc98e&hm=c8b7c0a36b7b451075e8697347c6513e6c16b24ef2dd2aa4a9f0bbd924bfbb22&",
        100: "https://cdn.discordapp.com/attachments/1340093391278440541/1340093762012975175/progress_100.png?ex=67b11b12&is=67afc992&hm=b79358a9694bbcf9e41493e255a839fcea092b9c5f1f970276a061e762bd336b&"
    }

    return image_urls.get(progress_level, image_urls[0])  # По умолчанию 0%
#url = f"https://api.battlemetrics.com/players/152198002?include=server"

 # ✅ Проверяем онлайн-статус по наличию '"online":true'

async def get_online_players(guild_id: int):
    """Запрашивает актуальный статус игроков из базы данных по их ID с учетом логики по online и lastSeen."""
    global requests_count
    player_ids = await get_player_ids_from_db(guild_id)
    online_players = []
    headers = {
        "Authorization": f"Bearer {switch_battlemetrics_token()}",
        "Accept": "application/vnd.api+json"
    }
    async with aiohttp.ClientSession() as session:
        for player_id in player_ids:
            url = f"https://api.battlemetrics.com/players/{player_id}?include=server,identifier"
            async with session.get(url, headers=headers) as response:
                await track_api_request(response.status)
                if response.status == 200:
                    text_response = await response.text()
                    data = json.loads(text_response)

                    player_data = data.get("data", {})
                    player_name = player_data.get("attributes", {}).get("name", "Неизвестно")
                    player_id_str = player_data.get("id", "Неизвестно")
                    is_online = '"online":true' in text_response


                    # ✅ Извлекаем данные о серверах
                    servers = data.get("included", [])
                    last_server = "Неизвестно"
                    last_seen = "Неизвестно"
                    time_played = 0

                    if servers:
                        # Сортируем по lastSeen, чтобы получить последний сервер
                        sorted_servers = sorted(
                            servers,
                            key=lambda x: x.get("meta", {}).get("lastSeen", ""),
                            reverse=True
                        )
                        latest_server = sorted_servers[0]
                        last_server = latest_server.get("attributes", {}).get("name", "Неизвестно")
                        last_seen = latest_server.get("meta", {}).get("lastSeen", "Неизвестно")
                        time_played = latest_server.get("meta", {}).get("timePlayed", 0)

                    # ✅ Формируем вывод в зависимости от статуса онлайн
                    online_players.append(
                        {
                            "id": player_id_str,  # 🆔 Явное указание ID
                            "name": player_name,  # 👤 Имя игрока
                            "status": "online" if is_online else "offline",  # 🟢🔴 Статус онлайн/оффлайн
                            "server": last_server,  # 🌐 Сервер
                            "last_seen": last_seen,  # 🕒 Последний вход
                            "time_played": time_played  # ⏱ Время в игре
                        }
                    )

    #print(online_players)
    return online_players

