### database.py
import aiosqlite
from battlemetrics import switch_battlemetrics_token
import requests

# Подключение к базе данных
#conn = sqlite3.connect("servers.db")
#cursor = conn.cursor()

async def drop_rust_plus_servers_table():
    """Асинхронно удаляет таблицу `rust_plus_servers`, если она существует"""
    async with aiosqlite.connect("servers.db") as db:
        await db.execute("DROP TABLE IF EXISTS rust_plus_servers;")
        await db.execute("DROP TABLE IF EXISTS fcm_tokens;")
        await db.commit()  # ✅ Сохраняем изменения в БД
        print("🗑 Таблица `rust_plus_servers` успешно удалена.")
# ✅ Асинхронное подключение к базе
async def init_db():
    async with aiosqlite.connect("servers.db") as db:
        print("✅ База данных успешно инициализирована!")
        # Создаем таблицы
        await db.execute('''
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id INTEGER NOT NULL PRIMARY KEY,
                guild_name TEXT,
                category_id INTEGER DEFAULT 0,
                alert INTEGER DEFAULT 0,
                channel_info_id INTEGER DEFAULT 0,
                channel_alerts_id INTEGER DEFAULT 0,
                vip INTEGER DEFAULT 0,
                active_server_id INTEGER DEFAULT NULL,
                FOREIGN KEY (active_server_id) REFERENCES servers (server_id) ON DELETE SET NULL
            )
        ''')

        # Добавляем поле guild_name, если его нет
        try:
            await db.execute("ALTER TABLE guilds ADD COLUMN guild_name TEXT")
        except aiosqlite.OperationalError:
            pass  # Поле уже существует

        await db.execute('''
            CREATE TABLE IF NOT EXISTS servers (
                server_id INTEGER NOT NULL PRIMARY KEY,
                server_name TEXT NOT NULL,
                ip TEXT NOT NULL,
                port INTEGER NOT NULL
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS guild_servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                server_id INTEGER NOT NULL,
                FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE,
                FOREIGN KEY (server_id) REFERENCES servers (server_id) ON DELETE CASCADE
            )
        ''')

        await db.execute("""
               CREATE TABLE IF NOT EXISTS players (
                   player_id INTEGER,
                   guild_id INTEGER NOT NULL,
                   player_name TEXT NOT NULL,
                   UNIQUE(guild_id, player_id),
                   FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE
               )
           """)

        await db.execute("""
                    CREATE TABLE IF NOT EXISTS notifications (
                        guild_id INTEGER NOT NULL,
                        player_name TEXT NOT NULL,
                        notify INTEGER NOT NULL DEFAULT 1,
                        PRIMARY KEY (guild_id, player_name)
                    )
                """)
        await db.execute("""
                CREATE TABLE IF NOT EXISTS rust_plus_servers (
                    guild_id INTEGER PRIMARY KEY,
                    ip TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    steam_id INTEGER NOT NULL,
                    player_token INTEGER NOT NULL
                )
            """)
        await db.execute('''
                CREATE TABLE IF NOT EXISTS rust_entities (
                    entity_id INTEGER PRIMARY KEY,
                    guild_id INTEGER NOT NULL,
                    steam_id INTEGER NOT NULL,
                    entity_name TEXT,
                    entity_type INTEGER,
                    custom_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS fcm_tokens (
                guild_id INTEGER PRIMARY KEY,
                expo_push_token TEXT NOT NULL,
                fcm_token TEXT NOT NULL,
                gcm_androidId TEXT NOT NULL,
                gcm_securityToken TEXT NOT NULL,
                rustplus_auth_token TEXT NOT NULL,
                FOREIGN KEY (guild_id) REFERENCES guilds (guild_id) ON DELETE CASCADE
            )
        ''')

async def remove_entity_by_name(steam_id, custom_name):
    """Удаляет устройство(а) по steam_id и имени или все, если custom_name == 'all'"""
    async with aiosqlite.connect("servers.db") as db:
        if custom_name == "all":
            await db.execute("DELETE FROM rust_entities WHERE steam_id = ?", (steam_id,))
            print(f"🗑 Все устройства с steam_id `{steam_id}` удалены из базы данных.")
        else:
            await db.execute("DELETE FROM rust_entities WHERE steam_id = ? AND custom_name = ?", (steam_id, custom_name))
            print(f"🗑 Устройство `{custom_name}` удалено из базы данных.")
        await db.commit()

        
async def get_entities_by_steam_id(steam_id):
    async with aiosqlite.connect('servers.db') as db:
        async with db.execute(
            "SELECT custom_name, entity_type FROM rust_entities WHERE steam_id = ?", (steam_id,)
        ) as cursor:
            result = await cursor.fetchall()
            return result  # (custom_name, entity_type) или None

async def get_guild_by_steam_id(steam_id):
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute(
            "SELECT guild_id FROM rust_plus_servers WHERE steam_id = ?", (steam_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_entity_by_custom_name(guild_id, custom_name):
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("""
            SELECT entity_type, entity_id, steam_id FROM rust_entities
            WHERE guild_id = ? AND custom_name = ?
        """, (guild_id, custom_name)) as cursor:
            return await cursor.fetchone()  # (entity_id, steam_id)

async def save_entity(guild_id, steam_id, entity_id, entity_name, entity_type, custom_name=None):
    async with aiosqlite.connect("servers.db") as db:
        await db.execute("""
            INSERT OR REPLACE INTO rust_entities (
                entity_id, guild_id, steam_id, entity_name, entity_type, custom_name
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (entity_id, guild_id, steam_id, entity_name, entity_type, custom_name))
        await db.commit()
        print(f"✅ Устройство сохранено: entity_id={entity_id}, custom={custom_name}")

async def load_all_fcm_data():
    fcm_data_list = []
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT guild_id, expo_push_token, fcm_token, gcm_androidId, gcm_securityToken, rustplus_auth_token FROM fcm_tokens") as cursor:
            async for row in cursor:
                guild_id, expo_token, fcm_token, android_id, security_token, auth_token = row
                fcm_details = {
                    "expo_push_token": expo_token,
                    "fcm_credentials": {
                        "fcm": {"token": fcm_token},
                        "gcm": {
                            "androidId": android_id,
                            "securityToken": security_token
                        }
                    },
                    "rustplus_auth_token": auth_token
                }
                fcm_data_list.append((guild_id, fcm_details))
    return fcm_data_list

async def save_fcm_details(guild_id, fcm_details):
    """Сохраняет или обновляет FCM-данные для определённой guild_id."""
    async with aiosqlite.connect("servers.db") as db:
        await db.execute("""
            INSERT INTO fcm_tokens (guild_id, expo_push_token, fcm_token, gcm_androidId, gcm_securityToken, rustplus_auth_token)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                expo_push_token = excluded.expo_push_token,
                fcm_token = excluded.fcm_token,
                gcm_androidId = excluded.gcm_androidId,
                gcm_securityToken = excluded.gcm_securityToken,
                rustplus_auth_token = excluded.rustplus_auth_token
        """, (
            guild_id,
            fcm_details["expo_push_token"],
            fcm_details["fcm_credentials"]["fcm"]["token"],
            fcm_details["fcm_credentials"]["gcm"]["androidId"],
            fcm_details["fcm_credentials"]["gcm"]["securityToken"],
            fcm_details["rustplus_auth_token"]
        ))
        await db.commit()
        print("Запись в базу данных")

# Запись данных в базу

async def save_rust_server_info(guild_id, ip, port, steam_id, player_token):
        """Сохраняет или обновляет информацию о Rust+ сервере в базе данных"""
        print(f"Сохранение данных для {guild_id} IP: {ip} PORT: {port} STEAM ID: {steam_id}")
        async with aiosqlite.connect("servers.db") as db:
            await db.execute("""
                        INSERT INTO rust_plus_servers (guild_id, ip, port, steam_id, player_token)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(guild_id) DO UPDATE SET
                            ip = excluded.ip,
                            port = excluded.port,
                            steam_id = excluded.steam_id,
                            player_token = excluded.player_token
                    """, (guild_id, ip, port, steam_id, player_token))
            await db.commit()
            print(f"Сервер сохранен в базу данных: {guild_id}")

async def get_server_details(guild_id):
    """📡 Ищет данные о сервере Rust+ по `guild_id` в базе данных"""
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute(
            "SELECT ip, port, steam_id, player_token FROM rust_plus_servers WHERE guild_id = ?", (guild_id,)
        ) as cursor:
            server_data = await cursor.fetchone()
            return server_data if server_data else None

#Получение списка для Rust+
async def load_servers_from_db():
    """🔄 Загружает список серверов из БД асинхронно"""
    servers = []
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT ip, port, steam_id, player_token FROM rust_plus_servers") as cursor:
            async for row in cursor:
                servers.append({
                    "ip": row[0],
                    "port": row[1],
                    "steam_id": row[2],
                    "player_token": row[3]
                })
    print(f"✅ Загружено {len(servers)} серверов из БД")
    return servers  # ✅ Возвращаем список серверов




"""Получает ID канала 'Alerts' для указанной гильдии."""
async def get_alerts_channel_id(guild_id: int):
    """Получает ID канала 'Alerts' для указанной гильдии."""
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT channel_alerts_id FROM guilds WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
"""🌟 Проверяет, является ли гильдия VIP."""
async def is_guild_vip(guild_id: int) -> bool:
    """🌟 Проверяет, является ли гильдия VIP."""
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT vip FROM guilds WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] == 1 if row else False
"""📊 Возвращает количество игроков в гильдии."""
async def get_player_count_for_guild(guild_id: int) -> int:
    """📊 Возвращает количество игроков в гильдии."""
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute(
            "SELECT COUNT(*) FROM players WHERE guild_id = ?", (guild_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0


#Изменение Уведомлений
""" Переключает значение столбца alert для заданной guild.
    Если текущее значение 1, то переключает на 0 и наоборот.
    """
async def toggle_alert(guild_id: int):
    """
    Переключает значение столбца alert для заданной guild.
    Если текущее значение 1, то переключает на 0 и наоборот.
    """
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT alert FROM guilds WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
        current = row[0] if row else 0
        new_value = 0 if current == 1 else 1
        await db.execute("UPDATE guilds SET alert = ? WHERE guild_id = ?", (new_value, guild_id))
        await db.commit()
    return new_value
#Получение состояния Уведомлений
"""Получает текущее состояние уведомлений для гильдии."""
async def get_alert_status(guild_id: int):
    """Получает текущее состояние уведомлений для гильдии."""
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT alert FROM guilds WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0  # 0 - выключено, 1 - включено

#Получаем ID (используется при добавлении нового ДС канала)
async def get_category_channels_ids(guild):
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute(
            "SELECT category_id, channel_info_id, channel_alerts_id FROM guilds WHERE guild_id = ?",
            (guild.id,)
        ) as cursor:
            result = await cursor.fetchone()  # Получаем одну строку результата
            if result:
                category_id, channel_info_id, channel_alerts_id = result
                return category_id, channel_info_id, channel_alerts_id
            else:
                return None  # Если данных нет, возвращаем None
#Обновляем или добавляем ID (используется при добавлении нового ДС канала)
async def add_or_update_guild_channels(guild_id, category_id, channel_info_id, channel_alerts_id):
    async with aiosqlite.connect("servers.db") as db:
        # 🔄 Добавить или обновить запись для конкретного guild_id
        await db.execute("""
            INSERT INTO guilds (guild_id, category_id, channel_info_id, channel_alerts_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                category_id = excluded.category_id,
                channel_info_id = excluded.channel_info_id,
                channel_alerts_id = excluded.channel_alerts_id
        """, (int(guild_id), int(category_id), int(channel_info_id), int(channel_alerts_id)))

        # 💾 Сохраняем изменения
        await db.commit()
        print(f"✅ Данные для guild_id `{guild_id}` успешно добавлены или обновлены.")

# ✅ Функция проверяет и добавляет сервер в базу, если его нет
async def add_server_if_not_exists(server_id):
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT server_name, ip, port FROM servers WHERE server_id = ?", (server_id,)) as cursor:
            server = await cursor.fetchone()

        if not server:
            # 🟢 Если сервера нет в базе, запрашиваем API BattleMetrics
            headers = {"Authorization": f"Bearer {switch_battlemetrics_token()}"}
            url = f"https://api.battlemetrics.com/servers/{server_id}"

            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                return None  # ❌ Сервер не найден

            data = response.json()
            server_name = data["data"]["attributes"]["name"]
            ip = data["data"]["attributes"]["ip"]
            port = data["data"]["attributes"]["portQuery"]

            # ✅ Добавляем сервер в базу
            await db.execute("INSERT INTO servers (server_id, server_name, ip, port) VALUES (?, ?, ?, ?)",
                             (server_id, server_name, ip, port))
            await db.commit()
            return (server_name, ip, port)
        else:
            return server  # 🔹 Возвращаем найденные данные

# ✅ Функция изменяет active_server_id для данной гильдии
async def set_active_server(guild_id, server_id):
    async with aiosqlite.connect("servers.db") as db:
        await db.execute("UPDATE guilds SET active_server_id = ? WHERE guild_id = ?", (server_id, guild_id))
        await db.commit()


#Поиск сервера в БД (обновленный)
async def find_server(server_id):
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT server_name, ip, port FROM servers WHERE server_id = ? LIMIT 1;", (server_id,)) as cursor:
            return await cursor.fetchone()

async def add_server_to_guild(guild_id, server_id):
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT server_name, ip, port FROM servers WHERE server_id = ?", (server_id,)) as cursor:
            server = await cursor.fetchone()

        if not server:
            import requests
            headers = {"Authorization": f"Bearer {switch_battlemetrics_token()}"}
            url = f"https://api.battlemetrics.com/servers/{server_id}"
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                return "Ошибка! Сервер не найден в BattleMetrics."

            data = response.json()
            server_name = data["data"]["attributes"]["name"]
            ip = data["data"]["attributes"]["ip"]
            port = data["data"]["attributes"]["portQuery"]

            await db.execute("INSERT INTO servers (server_id, server_name, ip, port) VALUES (?, ?, ?, ?)",
                             (server_id, server_name, ip, port))
            await db.commit()
        else:
            server_name, ip, port = server

        await db.execute("INSERT OR IGNORE INTO guild_servers (guild_id, server_id) VALUES (?, ?)", (guild_id, server_id))

        async with db.execute("SELECT active_server_id FROM guilds WHERE guild_id = ?", (guild_id,)) as cursor:
            active_server = await cursor.fetchone()

        if not active_server or active_server[0] is None:
            await db.execute("UPDATE guilds SET active_server_id = ? WHERE guild_id = ?", (server_id, guild_id))

        await db.commit()
        return f"Сервер {server_name} ({ip}:{port}) добавлен в избранное!"

async def get_info_channel_id(guild_id: int):
    """Получает ID канала 'info' для указанной гильдии."""
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT channel_info_id FROM guilds WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def get_guild_servers(guild_id):
    """Возвращает список серверов, привязанных к указанной гильдии (guild_id)"""
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("""
            SELECT s.server_id, s.server_name, s.ip, s.port
            FROM guild_servers gs
            JOIN servers s ON gs.server_id = s.server_id
            WHERE gs.guild_id = ?
            ORDER BY s.server_name ASC
        """, (guild_id,)) as cursor:
            servers = await cursor.fetchall()  # ✅ Асинхронный `fetchall()`

    return servers  # ✅ Теперь код не блокирует бота


async def add_guild_to_db(bot, guild):
    """Добавляет гильдию в базу данных, если её там нет"""
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT 1 FROM guilds WHERE guild_id = ?", (guild.id,)) as cursor:
            exists = await cursor.fetchone()

        if exists:
            # Всегда обновляем guild_name на актуальное название
            await db.execute("UPDATE guilds SET guild_name = ? WHERE guild_id = ?", (guild.name, guild.id))
            await db.commit()
            print(f"🔄 Обновлено название гильдии {guild.id}: {guild.name}")
            return

        # ✅ Добавляем новую запись
        await db.execute("INSERT INTO guilds (guild_id, guild_name) VALUES (?, ?)", (guild.id, guild.name))
        await db.commit()

        print(f"✅ Гильдия {guild.id} добавлена в базу данных.")



async def get_guild_name(guild_id):
    """Получает название гильдии по guild_id"""
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT guild_name FROM guilds WHERE guild_id = ?", (guild_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None


async def update_guild_name(guild_id, guild_name):
    """Обновляет название гильдии в базе данных"""
    async with aiosqlite.connect("servers.db") as db:
        await db.execute("UPDATE guilds SET guild_name = ? WHERE guild_id = ?", (guild_name, guild_id))
        await db.commit()


async def remove_guild_from_db(guild_id):
    async with aiosqlite.connect("servers.db") as conn:
        # Удаляем связанные данные
        await conn.execute("DELETE FROM rust_plus_servers WHERE guild_id = ?", (guild_id,))
        await conn.execute("DELETE FROM rust_entities WHERE guild_id = ?", (guild_id,))
        await conn.execute("DELETE FROM notifications WHERE guild_id = ?", (guild_id,))
        # Удаляем гильдию (остальные таблицы имеют CASCADE)
        await conn.execute("DELETE FROM guilds WHERE guild_id = ?", (guild_id,))
        await conn.commit()
    print(f"🔍 guild_id: {guild_id} ({type(guild_id)})")
    print(f"✅ Удалена гильдия и все связанные данные из базы данных: {guild_id}")


# Функция получения списка ID игроков
async def get_player_ids_from_db(guild_id):
    """Получает список ID игроков из базы данных."""
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT player_id FROM players WHERE guild_id = ?", (guild_id,)) as cursor:
            players = await cursor.fetchall()
            return [row[0] for row in players] if players else []

# Функция получения списка игроков
async def get_players_from_guild(guild_id):
    """Асинхронно получает список игроков из гильдии"""
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT player_name FROM players WHERE guild_id = ?", (guild_id,)) as cursor:
            players = await cursor.fetchall()
            return [row[0] for row in players]  # ✅ Возвращаем список имен

async def add_player_to_db(db, guild_id, player_name, player_id):
    """Добавляет игрока в базу данных, позволяя одинаковым игрокам быть в разных гильдиях."""
    await db.execute("""
            INSERT INTO players (guild_id, player_name, player_id)
            VALUES (?, ?, ?)
            ON CONFLICT(guild_id, player_id) DO UPDATE SET
                player_name = excluded.player_name
        """, (guild_id, player_name, player_id))
    await db.commit()
    print(f"✅ Игрок {player_name} (ID: {player_id}) добавлен или обновлён в гильдии {guild_id}.")


async def check_player_exists(db, guild_id, player_id):
    """Проверяет, есть ли игрок с таким ID в базе"""
    async with db.execute("SELECT 1 FROM players WHERE guild_id = ? AND player_id = ?", (guild_id, player_id)) as cursor:
        return await cursor.fetchone() is not None

# Функция удаления игрока


async def delete_player(guild_id, player_name):
    """Удаляет игрока из базы данных по `guild_id` и `player_name`"""
    async with aiosqlite.connect("servers.db") as db:
        await db.execute("DELETE FROM players WHERE guild_id = ? AND player_name = ?", (guild_id, player_name))
        await db.commit()
        print(f"🗑 Игрок `{player_name}` удалён из гильдии {guild_id}.")


# Функция получения всех гильдий и игроков
async def get_all_guilds_and_players():
    """Выводит все гильдии и их игроков из базы данных"""
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT guild_id FROM guilds") as cursor:
            guilds = await cursor.fetchall()  # ✅ Делаем `await` для `fetchall()`

        for guild in guilds:
            guild_id = guild[0]
            print(f"🎮 Гильдия ID: {guild_id}")

            async with db.execute("SELECT player_name FROM players WHERE guild_id = ?", (guild_id,)) as cursor:
                players = await cursor.fetchall()  # ✅ Делаем `await` для `fetchall()`

            if players:
                print("📋 Список игроков:")
                for player in players:
                    print(f"  - {player[0]}")
            else:
                print("❌ Нет игроков в этой гильдии.")
            print()


# Функция обновления или вставки данных о сервере
async def update_or_insert_server_info(guild_id, new_channel_id, server_id):
    """Обновляет или добавляет информацию о сервере в таблице `guilds`"""
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT 1 FROM guilds WHERE guild_id = ?", (guild_id,)) as cursor:
            existing_record = await cursor.fetchone()  # ✅ Асинхронный `fetchone()`

        if existing_record:
            await db.execute("UPDATE guilds SET channel_id = ? WHERE guild_id = ?", (new_channel_id, guild_id))
            print(f"✅ Обновлен `channel_id` для `guild_id`: {guild_id}")
        else:
            await db.execute(
                "INSERT INTO guilds (guild_id, channel_id, active_server_id) VALUES (?, ?, ?)",
                (guild_id, new_channel_id, server_id),
            )
            print(f"✅ Вставлена новая запись для `guild_id`: {guild_id}")

        await db.commit()  # ✅ Асинхронный `commit()`




