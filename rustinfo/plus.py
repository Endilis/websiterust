from rustplus import RustSocket, ServerDetails, ChatCommand, CommandOptions, Command
import asyncio
from rustplus.exceptions import RequestError  # ✅ Импортируем RequestError
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from discord.ext import tasks
from printer import log_command
import inspect
import logging
from items_loader import load_items, get_item_name

load_items("items.json")  # ← один раз при старте

options = CommandOptions(prefix=".")  # Use whatever prefix you want here
logging.basicConfig(level=logging.ERROR, format="%(asctime)s - %(levelname)s - %(message)s")
sockets = {}  # 🔹 Храним WebSocket-подключения
servers_list = []  # 🔹 Храним список серверов
team_cache = {}  # 🔹 Кеш тиммейтов {главный_steam_id: [тиммейты]}
EMOJIS = {
    1: ":exclamation:",
    2: ":smart.alarm:",
    3: ":storage.monitor:"
}

def draw_inventory_with_items(entity_info):
    """🔄 Рисует инвентарь с предметами и возвращает `BytesIO`"""
    
    rows, cols = 8, 6
    slot_size = 64
    padding = 10
    bg_color = (54, 57, 63)
    slot_color = (100, 100, 100)

    width = cols * slot_size + (cols + 1) * padding
    height = rows * slot_size + (rows + 1) * padding
    inventory_template = Image.new("RGBA", (width, height), bg_color)
    draw = ImageDraw.Draw(inventory_template)

    for row in range(rows):
        for col in range(cols):
            x0 = padding + col * (slot_size + padding)
            y0 = padding + row * (slot_size + padding)
            x1 = x0 + slot_size
            y1 = y0 + slot_size
            draw.rectangle([x0, y0, x1, y1], outline=slot_color, width=2)    
    
    draw = ImageDraw.Draw(inventory_template)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 52)

    slot_size = 64
    padding = 10
    #ВЫВОД В КОНСОЛЬ
    for item in entity_info.items:
        item_id = item.item_id
        quantity = item.quantity
        name = get_item_name(item_id)
        print(f"• {name}: x{quantity}")
    #....................
    for index, item in enumerate(entity_info.items):
        item_id = item.item_id
        quantity = item.quantity

        item_name = get_item_name(item_id)
        if not item_name:
            continue

        try:
            icon = Image.open(f"images/{item_name}.png").convert("RGBA")
            icon = icon.resize((slot_size, slot_size), Image.LANCZOS)
        except FileNotFoundError:
            print(f"❌ Icon for {item_name} not found.")
            continue

        col = index % cols
        row = index // cols
        x = padding + col * (slot_size + padding)
        y = padding + row * (slot_size + padding)

        inventory_template.paste(icon, (x, y), icon)
        draw.text((x + 2, y + slot_size - 18), f"x{quantity}", fill=(255, 255, 255), font=font)
    

    if getattr(entity_info, "has_protection", False):
        original = inventory_template
        new_width = original.width + 300
        new_height = original.height
        new_img = Image.new("RGBA", (new_width, new_height), bg_color)
        new_img.paste(original, (0, 0))
        draw = ImageDraw.Draw(new_img)

        try:
            icon = Image.open("images/toolcupboard.png").convert("RGBA")
            icon = icon.resize((256, 256), Image.LANCZOS)
            icon_x = original.width 
            icon_y = padding
            new_img.paste(icon, (icon_x, icon_y), icon)
        except FileNotFoundError:
            print("❌ toolcupboard.png не найден.")

        slot_x = icon_x
        slot_y = icon_y
        draw.rectangle(
            [slot_x, slot_y, slot_x + 256, slot_y + 256],
            outline=slot_color,
            width=2
        )

        try:
            now = time.time()
            remaining = max(0, int(entity_info.protection_expiry - now))
            days = remaining // 86400
            hours = (remaining % 86400) // 3600
            minutes = (remaining % 3600) // 60
            time_text = f"{days}d {hours}h {minutes}m"

            draw.text((slot_x + 10, slot_y + 256), time_text, fill=(0, 255, 0), font=font_big)
        except Exception as e:
            print("⛔ Ошибка расчёта времени:", e)
        
        inventory_template = new_img

    
    buffer = BytesIO()
    inventory_template.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

async def get_entity_info(device_name, guild_id: int, username: str = None, guild_name: str = None):
    """🔍 Получает карту Rust и возвращает `BytesIO` с уменьшенным изображением"""
    from database import get_server_details, get_entity_by_custom_name
    server_data = await get_server_details(guild_id)
    await log_command(username, inspect.currentframe().f_code.co_name, "", guild_id)
    entity_id = await get_entity_by_custom_name(guild_id, device_name)
    if not entity_id:
        print(f"❌ Устройство {device_name} не найдено в базе данных.")
        return None, "❌ Устройство не найдено в базе данных."
    if not server_data:
        print(f"❌ Сервер {device_name} не найден в базе данных.")
        return None, "❌ Сервер не найден в базе данных."
    
    ip, port, steam_id, player_token = server_data
    try:
        server_details = ServerDetails(ip, port, steam_id, player_token)
        socket = RustSocket(server_details)

        await socket.connect()
        print("✅ Подключено к серверу!")
        print(f"Получаем информацию об устройстве {device_name} ({entity_id})")
        entity_info = await socket.get_entity_info(entity_id[1])
        print(f"{entity_info}")
        #expiry = datetime.datetime.utcfromtimestamp(entity_info.protection_expiry)
        #formatted = expiry.strftime("%Y-%m-%d %H:%M:%S UTC")
        #print(f"🛡 Защита активна до: {formatted}")
        buffer = draw_inventory_with_items(entity_info)
        await socket.disconnect()
        return buffer, None
    except Exception as e:
        print(f"❌ Ошибка получения информации: {e}")
        return None, f"❌ Ошибка при получении информации: {e}"

@tasks.loop(seconds=10)
async def check_servers_status():
    print("🔄 Запускаем проверку серверов...")
    await check_servers_now()

async def check_servers_now():
    """🔄 Проверяет, онлайн ли сервера, и переподключает только отключенные"""
    from database import load_servers_from_db
    print("🔍 Проверяем онлайн-статус серверов...")
    server_list = await load_servers_from_db()
    disconnected_servers = []  # 📌 Храним только отключенные сервера
    for steam_id, socket in list(sockets.items()):
        try:
            server_info = await socket.get_info()
            team_info = await socket.get_team_info()
            # ✅ Проверяем, вернул ли API `None`
            if server_info is None or server_info.name is None:
                raise ValueError(f"❌ Сервер {steam_id} не вернул данные!")

            print(f"✅ Сервер: {server_info.name} 👥 Онлайн: {server_info.players} / {server_info.max_players} : ({server_info.queued_players}) steam_id : {team_info.leader_steam_id}")

        except Exception as e:
            logging.error(f"⚠ Ошибка при получении информации с сервера {steam_id}: {e}")
            print(f"⚠ Сервер {steam_id} недоступен! Добавляем в список на переподключение...")
            disconnected_servers.append(steam_id)  # ❌ Добавляем в список недоступных

    if disconnected_servers:
        print(f"🔄 Найдено {len(disconnected_servers)} отключенных серверов. Переподключаем только их...")
        #server_list = await load_servers_from_db()
        servers_to_reconnect = [s for s in server_list if s["steam_id"] in disconnected_servers]
        print(f"Сервер на рекконект {servers_to_reconnect}")
        await connect_to_servers(servers_to_reconnect)
    else:
        print("✅ Все сервера работают! Переподключение не требуется.")

async def get_main_steam_id(steam_id):
    """🔍 Определяет, какому главному Steam ID принадлежит игрок.
    Если игрок не найден — обновляет кеш `team_cache`."""

    # 1️⃣ Проверяем, есть ли `steam_id` в кэше
    for main_steam_id, teammates in team_cache.items():
        if steam_id in teammates:
            return main_steam_id  # ✅ Найден главный Steam ID

    # 2️⃣ Если нет в кеше — обновляем `team_cache`
    print(f"⚠️ Steam ID {steam_id} не найден в кеше. Обновляем `team_cache`...")

    for steam_id_key, socket in sockets.items():
        try:
            team_info = await socket.get_team_info()
            members = team_info.members or []  # ✅ Безопасная замена None
            teammates = [member.steam_id for member in members]
            team_cache[steam_id_key] = teammates
            print(f"✅ Кеш обновлен для {steam_id_key}: {teammates}")
        except Exception as e:
            print(f"❌ Ошибка обновления `team_cache` для {steam_id_key}: {e}")

    # 3️⃣ После обновления кэша ищем снова
    for main_steam_id, teammates in team_cache.items():
        if steam_id in teammates:
            return main_steam_id  # ✅ Найден после обновления

    return None  # ❌ Если не найден даже после обновления


async def setup_plus_module():
    from database import load_servers_from_db
    """🔥 Инициализация Plus-модуля"""
    print("🔄 Загружаем сервера из базы данных...")

    server_list = await load_servers_from_db()  # ✅ Загружаем сервера

    if not server_list:
        print("❌ Ошибка: `server_list` пуст! Проверь `servers.db`.")
        return

    print(f"✅ Загружено {len(server_list)} серверов.")
    await connect_to_servers(server_list)  # ✅ Подключаемся к серверам



async def close_connection(steam_id):
    print("Вход в функцию закрытия")
    """🔌 Закрывает WebSocket-соединение по `steam_id`"""
    if steam_id in sockets:
        socket = sockets[steam_id]
        try:
            await socket.disconnect()  # ✅ Закрываем WebSocket
            sockets.pop(steam_id, None)  # ❌ Удаляем из списка подключенных
            print(f"✅ WebSocket для SteamID {steam_id} закрыт.")
            return True
        except Exception as e:
            print(f"❌ Ошибка при закрытии WebSocket для {steam_id}: {e}")
            return False
    else:
        print(f"⚠️ Соединение с SteamID {steam_id} не найдено.")
        return True

async def connect_to_servers(server_list):
    """🔄 Подключается ко всем серверам и сохраняет WebSocket"""
    print(f"🔍 Проверяем servers_list: {server_list}")

    if not server_list:
        print("❌ Ошибка: `server_list` пуст! Проверь `load_servers_from_db()`.")
        return
    for server in server_list:
        if server["player_token"] in sockets:
            print(f"✅ Сервер {server['ip']} уже подключен, пропускаем")
            continue

        print(f"🔄 Подключаем сервер {server['ip']}...")

        server_details = ServerDetails(
            server["ip"], server["port"], server["steam_id"], server["player_token"]
        )

        socket = RustSocket(server_details, command_options=options)  # ✅ Подключаемся с командами
        success = await close_connection(server_details.player_id)
        if not success:
            print(f"⛔ Прерывание — сокет не закрылся для {server_details.player_id}")
            return
        sockets[server["steam_id"]] = socket
        try:
            await socket.connect()
            info = await socket.get_info()
            print(f"✅ Подключено к серверу {server['ip']}:{server['port']} {server['steam_id']} connect_to_servers {info}")
            await asyncio.sleep(3)
            await socket.send_team_message(" :scientist: Connected :exclamation:")
            print("Отправлено сообщение в чат Connected")

        except Exception as e:
            print(f"⚠ Ошибка при получении информации от сервера: {e}")

    # Регистрируем команды один раз после попыток подключиться ко всем серверам
    await register_commands(server_list)



async def get_rust_map(guild_id: int, username: str = None, guild_name: str = None):
    """🔍 Получает карту Rust и возвращает `BytesIO` с уменьшенным изображением"""
    from database import get_server_details
    server_data = await get_server_details(guild_id)
    await log_command(username, inspect.currentframe().f_code.co_name, "", guild_id)

    if not server_data:
        return None, "❌ Сервер не найден в базе данных."

    ip, port, steam_id, player_token = server_data
    try:
        server_details = ServerDetails(ip, port, steam_id, player_token)
        socket = RustSocket(server_details)

        await socket.connect()
        #print("✅ Подключено к серверу!")

        # 📡 Получаем карту
        map_image = await socket.get_map(add_icons=False, add_team_positions=True, add_grid=True)

        if not isinstance(map_image, Image.Image):
            #print(f"⚠️ Rust+ API вернул ошибку: {map_image}")
            await socket.disconnect()
            return None, f"❌ Ошибка API Rust+: {map_image}"

        await socket.disconnect()
        #print("✅ Карта получена, уменьшаем размер...")

        # 🔻 Уменьшаем разрешение, если слишком большое
        max_size = (2048, 2048)  # Оптимальный размер
        map_image.thumbnail(max_size, Image.LANCZOS)

        # 🔻 Сохраняем в JPEG с качеством 85% (уменьшает вес в 3-4 раза)
        image_bytes = BytesIO()
        map_image.convert("RGB").save(image_bytes, format="JPEG", quality=85)
        image_bytes.seek(0)

        # 📏 Проверяем итоговый размер
        file_size = image_bytes.getbuffer().nbytes / 1024 / 1024
        print(f"📏 Итоговый размер файла: {file_size:.2f} MB")

        return image_bytes, None

    except Exception as e:
        print(f"❌ Ошибка получения карты: {e}")
        return None, f"❌ Ошибка при получении карты: {e}"



async def register_commands(server_list):
    from database import get_entity_by_custom_name, get_guild_by_steam_id, save_entity, get_entities_by_steam_id, remove_entity_by_name
    from pairing_cache import pending_pairings
    from FCM import ENTITY_EMOJIS
    from views import send_switch_embed
    from bot import bot
    """✅ Регистрирует команды для всех серверов"""
    for server in server_list:
        server_details = ServerDetails(
            server["ip"], server["port"], server["steam_id"], server["player_token"]
        )
        @Command(server_details)
        async def remove(command: ChatCommand):
            main_steam_id = await get_main_steam_id(command.sender_steam_id)  # Получаем главный Steam ID
            socket = sockets.get(main_steam_id)
            guild_id = await get_guild_by_steam_id(main_steam_id)
            await log_command(command.sender_name, inspect.currentframe().f_code.co_name, socket, guild_id, command.sender_steam_id)
            if len(command.args) != 1:
                if socket:
                    await socket.send_team_message("Use .remove <name> To remove device. or .remove <all>")
                    return
            if command.args[0] == "all":
                if socket:
                    await socket.send_team_message("All devices removed")
                    await remove_entity_by_name(main_steam_id, "all")
                    return
            if socket:
                entities = await get_entities_by_steam_id(main_steam_id)
                device_name = command.args[0]
                match = next(((name, type) for name, type in entities if name == device_name), None)
                if match is None:
                    await socket.send_team_message(f"Device <{device_name}> not found. Use .devices to see all devices")
                    return
                else:
                    name, type = match
                    emoji = ENTITY_EMOJIS.get(type)
                    await socket.send_team_message(f"Device {emoji} <{name}> removed")
                    await remove_entity_by_name(main_steam_id, name)
                    
                return

        @Command(server_details)
        async def devices(command: ChatCommand):
            main_steam_id = await get_main_steam_id(command.sender_steam_id)  # Получаем главный Steam ID
            socket = sockets.get(main_steam_id)
            guild_id = await get_guild_by_steam_id(main_steam_id)
            await log_command(command.sender_name, inspect.currentframe().f_code.co_name, socket, guild_id, command.sender_steam_id)

            # 📥 Получаем устройства из базы по основному steam_id
            entities = await get_entities_by_steam_id(main_steam_id)
            if not entities:
                emoji = EMOJIS.get(1)
                await socket.send_team_message(f"{emoji} No devices found")
                return

            await socket.send_team_message("Device List:")
            for ent in entities:
                name = ent[0]
                emoji = ENTITY_EMOJIS.get(ent[1])
                message = f"{emoji}  <{name}>"
                await socket.send_team_message(message)
                await asyncio.sleep(1)

            name = command.sender_name

        @Command(server_details)
        async def sw(command: ChatCommand):
            main_steam_id = await get_main_steam_id(command.sender_steam_id)  # Получаем главный Steam ID
            socket = sockets.get(main_steam_id)
            guild_id = await get_guild_by_steam_id(main_steam_id)
            await log_command(command.sender_name, inspect.currentframe().f_code.co_name, socket, guild_id, command.sender_steam_id)
            if len(command.args) != 2 or command.args[1] not in ("0", "1"):
                if socket:
                    await socket.send_team_message("Use .sw <name> <0|1> to <off|on>")
                return

            custom_name = command.args[0]
            value = command.args[1] == "1"
            guild_id = await get_guild_by_steam_id(main_steam_id)
            entity = await get_entity_by_custom_name(guild_id, custom_name)
            emoji = ENTITY_EMOJIS.get(entity[0]) if entity else ":exclamation:"
            if not entity:
                await socket.send_team_message(f"{emoji} Not found: <{custom_name}>")
                return

            entity_id = entity[1]
            if socket:
                await socket.set_entity_value(entity_id, value)
                await socket.send_team_message(f"{emoji} {custom_name} {'<On>' if value else '<Off>'}")


        @Command(server_details)
        async def add(command: ChatCommand):
            main_steam_id = await get_main_steam_id(command.sender_steam_id)  # Получаем главный Steam ID
            socket = sockets.get(main_steam_id)
            guild_id = await get_guild_by_steam_id(main_steam_id)
            await log_command(command.sender_name, inspect.currentframe().f_code.co_name, socket, guild_id, command.sender_steam_id)
            if not command.args:
                await socket.send_team_message(":exclamation: Use .add <name>")
                return
            if command.args == ["all"]:
                await socket.send_team_message(":exclamation: Use another <name> ")
                return
            custom_name = command.args[0]

            guild_id = await get_guild_by_steam_id(main_steam_id)
            if not guild_id:
                await socket.send_team_message("❌ Не удалось определить Discord-сервер.")
                return

            for entity_id, data in pending_pairings.copy().items():
                if data["steam_id"] == main_steam_id and data["guild_id"] == guild_id:
                    await save_entity(
                        guild_id=guild_id,
                        steam_id=main_steam_id,
                        entity_id=entity_id,
                        entity_name=data["entity_name"],
                        entity_type=data["entity_type"],
                        custom_name=custom_name
                    )
                    pending_pairings.pop(entity_id, None)
                    socket = sockets.get(main_steam_id)
                    if socket:
                        await send_switch_embed(bot, guild_id, custom_name)
                        await socket.send_team_message(f" :wiretool: Device '{custom_name}' successfully registered.")
                    return
            
            emoji = EMOJIS.get(1)
            await socket.send_team_message(f"{emoji} No devices found")

        @Command(server_details)
        async def pop(command: ChatCommand):
            main_steam_id = await get_main_steam_id(command.sender_steam_id)  # Получаем главный Steam ID
            socket = sockets.get(main_steam_id)
            guild_id = await get_guild_by_steam_id(main_steam_id)
            
            # Получаем информацию о канале
            channel_name = None
            channel_id = getattr(command, 'channel_id', None)
            if channel_id:
                try:
                    channel = await bot.fetch_channel(channel_id)
                    channel_name = channel.name if channel else None
                except:
                    pass
            
            await log_command(command.sender_name, inspect.currentframe().f_code.co_name, socket, guild_id, command.sender_steam_id)
            if not main_steam_id:
                print(f"❌ Ошибка: не удалось определить сервер для {main_steam_id}")
                return
            try:
                info = await socket.get_info()
            except Exception as e:
                print(f"POP⚠ Ошибка при получении информации от сервера: {e}")
                return
            await socket.send_team_message(f" :heartrock: Online:{info.players}/{info.max_players} Queue({info.queued_players}) ")


        @Command(server_details)
        async def help(command: ChatCommand):
            main_steam_id = await get_main_steam_id(command.sender_steam_id)  # Получаем главный Steam ID
            socket = sockets.get(main_steam_id)
            guild_id = await get_guild_by_steam_id(main_steam_id)
            await log_command(command.sender_name, inspect.currentframe().f_code.co_name, socket, guild_id, command.sender_steam_id)
            if not socket:
                print(f"❌ Ошибка: сервер с Steam ID {main_steam_id} не найден!")
                return
            await socket.send_team_message(f"Commands: .help, .add <name>, .remove <name>, .devices, .sw <name> <0|1>, .pop, .time")

        @Command(server_details)
        async def time(command: ChatCommand):
            """📌 Команда !time — показывает игровое время и оставшееся реальное время до заката/рассвета"""
            main_steam_id = await get_main_steam_id(command.sender_steam_id)  # Получаем главный Steam ID
            socket = sockets.get(main_steam_id)
            guild_id = await get_guild_by_steam_id(main_steam_id)
            await log_command(command.sender_name, inspect.currentframe().f_code.co_name, socket, guild_id, command.sender_steam_id)
            try:
                game_time = await socket.get_time()

                current_time = game_time.raw_time  # Текущее время (float)
                sunrise_time = float(game_time.sunrise.split(":")[0])  # Часы восхода (07:00)
                sunset_time = float(game_time.sunset.split(":")[0])  # Часы заката (19:00)

                day_length = 30  # Фиксированная длина дня (30 реальных минут)
                night_length = 15  # Фиксированная длина ночи (15 реальных минут)

                # Определяем, день или ночь
                if sunrise_time <= current_time < sunset_time:
                    # Сейчас день, считаем время до заката
                    time_until_sunset = sunset_time - current_time
                    real_minutes_until_sunset = (time_until_sunset / (sunset_time - sunrise_time)) * day_length
                    print(f"Проверка{server_details}")
                    message = (f"Game Time: [{game_time.time}] :electric.digitalclock:                "
                               f"SunSet in  {real_minutes_until_sunset:.0f} min.:torch:")
                else:
                    # Сейчас ночь, считаем время до рассвета
                    if current_time >= sunset_time:
                        time_until_sunrise = (24 - current_time) + sunrise_time  # До 7 утра
                    else:
                        time_until_sunrise = sunrise_time - current_time

                    real_minutes_until_sunrise = (time_until_sunrise / (24 - sunset_time + sunrise_time)) * night_length

                    message = (f"Game Time: [{game_time.time}] :electric.digitalclock:"
                               f"SunRise: {real_minutes_until_sunrise:.0f} min.:torch: ")

                await socket.send_team_message(message)

            except Exception as e:
                print(f"❌ Ошибка выполнения команды !time на сервере {server['ip']}: {e}")
