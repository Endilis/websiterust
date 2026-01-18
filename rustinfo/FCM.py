import asyncio
import json
from rustplus import FCMListener
from database import load_all_fcm_data, save_rust_server_info, get_server_details
from discord.ext import tasks
from plus import sockets, check_servers_now, connect_to_servers
from pairing_cache import pending_pairings
from server_manager import start_rust_server
listeners = {}
loop = asyncio.get_event_loop() 
ENTITY_EMOJIS = {
    1: ":smart.switch:",
    2: ":smart.alarm:",
    3: ":storage.monitor:"
}

from push_receiver import PushReceiver 

print("MAX_SILENT_INTERVAL_SECS =", PushReceiver.MAX_SILENT_INTERVAL_SECS)


# ✅ Глобальный event loop, захватывается при импорте (в главном потоке)
main_loop = asyncio.get_event_loop()

class FCM(FCMListener):
    def __init__(self, fcm_details, guild_id, loop):  # добавили loop
        super().__init__(fcm_details)
        self.guild_id = guild_id
        self.loop = loop

    def on_notification(self, obj, notification, data_message):
        print("📥 handle_notification вызван")
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.handle_notification(notification),
                self.loop  # ✅ правильный loop из основного потока
            )
            future.add_done_callback(lambda f: print(
                f"✅ Обработка завершена" if not f.exception() else f"❌ Ошибка: {f.exception()}"
            ))
        except Exception as e:
            print(f"⚠ Ошибка запуска корутины из потока: {e}")

    async def handle_notification(self, notification):
        from database import get_entities_by_steam_id
        print("Вход в функцию handle_notification")
        if notification.get("message") == "Tap to pair with this device.":
            parsed_body = json.loads(notification["body"])
            entity_id = int(parsed_body["entityId"])
            entity_type = int(parsed_body["entityType"])
            entity_name = parsed_body["entityName"]
            steam_id = int(parsed_body["playerId"])

            # запоминаем pairing
            pending_pairings[entity_id] = {
                "guild_id": self.guild_id,
                "steam_id": steam_id,
                "entity_type": entity_type,
                "entity_name": entity_name
            }
            emoji = ENTITY_EMOJIS.get(entity_type)
            message = f"{emoji} ready to pair. Use .add <name> to register"

            socket = sockets.get(steam_id)
            if socket:
                await socket.send_team_message(message)

        if notification.get("message") != "Tap to pair with this server.":
            return
            
        try:
            parsed_body = json.loads(notification["body"])
        except Exception as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            return

        ip = parsed_body.get("ip")
        port = int(parsed_body.get("port"))
        steam_id = int(parsed_body.get("playerId"))
        token = int(parsed_body.get("playerToken"))

        fcm_server = [{
            "ip": ip,
            "port": port,
            "steam_id": steam_id,
            "player_token": token
        }]
        old_server_details = await get_server_details(self.guild_id)
        if old_server_details:
            old_ip, old_port, old_steam_id, old_token = old_server_details
            old_server = [{
                "ip": old_ip,
                "port": old_port,
                "steam_id": old_steam_id,
                "player_token": old_token
            }]

            if old_server == fcm_server:
                print("🔹 FCM сервер уже подключен. Игнорируем уведомление.")

                return  # Ничего не делаем!

        await save_rust_server_info(self.guild_id, ip, port, steam_id, token)
        await connect_to_servers(fcm_server)
        print(f"✅ Подключение сервера: {ip}:{port} (Steam ID: {steam_id})")


        if notification.get("message") == "Your base is under attack!":
            print("🔔 Получено уведомление о тревоге!")

            try:
                parsed_body = json.loads(notification["body"])
            except Exception as e:
                print(f"❌ Ошибка парсинга JSON: {e}")
                return

            ip = parsed_body.get("ip")
            port = int(parsed_body.get("port"))
            steam_id = int(parsed_body.get("playerId", 0))  # если есть
            entity_type = 2  # Smart Alarm

            # Получаем имя устройства
            entity = await get_entities_by_steam_id(steam_id)
            name = entity["custom_name"] or entity["entity_name"] if entity else "Unknown"

            socket = sockets.get(steam_id)
            if socket:
                await socket.send_team_message(f"🚨 Alarm {name}")
                print(f"✅ Alarm message sent: Alarm {name}")
            else:
                print(f"⚠️ Нет активного сокета для Steam ID: {steam_id}")


@tasks.loop(minutes=1)
async def fcm_heartbeat_monitor():
    from database import load_all_fcm_data

    print("🩺 [FCM Monitor] Проверяем статус Listener'ов...")

    fcm_data_list = await load_all_fcm_data()

    for guild_id, _ in fcm_data_list:
        listener = listeners.get(guild_id)
        if not listener:
            print(f"❌ Гильдия {guild_id}: Listener отсутствует")
            continue
            
        thread = getattr(listener, "thread", None)
        if thread and thread.is_alive():
            print(f"✅ Гильдия {guild_id}: Listener активен")
        else:
            print(f"❌ Гильдия {guild_id}: Listener мёртв")


async def start_fcm_for_guild(guild_id, fcm_details):
    loop = asyncio.get_running_loop()  # ✅ получаем активный loop
    listener = FCM(fcm_details, guild_id, loop)  # ✅ передаём его
    try:
        listener.start()  # запускает listener в потоке
        listeners[guild_id] = listener
        print(f"✅ FCMListener запущен для гильдии {guild_id}")
    except Exception as e:
        print(f"❌ Ошибка запуска FCM для {guild_id}: {e}")



async def load_all_fcm_from_db():
    fcm_data_list = await load_all_fcm_data()
    for guild_id, fcm_details in fcm_data_list:
        await start_fcm_for_guild(guild_id, fcm_details)
