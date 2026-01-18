### channel_utils.py

from discord import PermissionOverwrite, Embed

from discord.ext import tasks

from battlemetrics import generate_progress_bar

import discord

import aiosqlite

import asyncio

import json

import subprocess

from database import add_server_if_not_exists, set_active_server, get_alert_status, update_or_insert_server_info, add_or_update_guild_channels

from views import ServerSearchView

from cache import online_players_cache

from random import uniform  # Для случайной задержки

import os

from datetime import datetime
semaphore_load_counter = 0
gamedig_cache = {}
MAX_CONCURRENT_UPDATES = 60  # Максимум параллельных обновлений
SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_UPDATES)

if os.name == 'nt':  # Windows

    GAMEDIG_PATH = "C:\\Users\\endil\\AppData\\Roaming\\npm\\gamedig.cmd"

else:  # Unix/Linux/MacOS

    GAMEDIG_PATH = "/usr/local/bin/gamedig"





async def delete_rustinfo_structure(guild: discord.Guild):

    """🧹 Удаляет категорию RustInfo и каналы 'monitoring' и 'alerts', если они существуют"""

    category_name = "──〢・RustInfo"

    channel_names = {"monitoring", "alerts"}



    try:

        rustinfo_category = discord.utils.get(guild.categories, name=category_name)



        if not rustinfo_category:

            print(f"ℹ️ Категория '{category_name}' не найдена на сервере {guild.name}")

            return



        print(f"🧹 Найдена категория: {rustinfo_category.name} (ID: {rustinfo_category.id})")



        # Удаляем каналы внутри категории по имени

        for channel in rustinfo_category.channels:

            if channel.name.lower() in channel_names:

                print(f"🗑 Удаляем канал: {channel.name}")

                await channel.delete()



        # Удаляем саму категорию

        print(f"🗑 Удаляем категорию: {rustinfo_category.name}")

        await rustinfo_category.delete()



        print("✅ Категория и каналы успешно удалены!")



    except discord.Forbidden:

        print("❌ Недостаточно прав для удаления каналов или категории.")

        await send_message_to_guild(

            guild,

            f"❌ У меня нет прав для удаления категории **{category_name}** и её каналов."

        )



    except Exception as e:

        print(f"❌ Ошибка при удалении структуры RustInfo: {e}")

        await send_message_to_guild(

            guild,

            f"❌ Произошла ошибка при удалении структуры **RustInfo**: {e}"

        )





async def send_message_to_guild(guild, message: str):

    """📩 Пытается отправить сообщение владельцу или в первый доступный текстовый канал"""

    try:

        if guild.owner:

            await guild.owner.send(message)

            return

    except:

        pass



    for channel in guild.text_channels:

        if channel.permissions_for(guild.me).send_messages:

            try:

                await channel.send(message)

                return

            except:

                continue



async def create_category_channels(guild):

    permissions = guild.me.guild_permissions



    # 🔒 Проверка на доступ

    if not (permissions.manage_channels and permissions.send_messages and permissions.view_channel):

        msg = (

            f"❌ Бот не имеет необходимых прав на сервере **{guild.name}**.\n"

            f"Требуются:\n"

            f"• Управление каналами\n"

            f"• Просмотр каналов\n"

            f"• Отправка сообщений\n"

            f"Пожалуйста, выдайте права и повторите попытку."

        )

        await send_message_to_guild(guild, msg)

        return



    try:

        top_role = guild.me.top_role

        print(f"🎭 Моя наивысшая роль: {top_role.name} (ID: {top_role.id})")

        print(f"Вход в create_category_channels: {guild.name}")



        # 🛡️ Права доступа

        category_overwrites = {

            guild.default_role: discord.PermissionOverwrite(

                view_channel=False  # ❌ Никто не видит по умолчанию

            ),

            guild.me: discord.PermissionOverwrite(

                view_channel=True,

                manage_channels=True,

                manage_roles=True,

                manage_messages=True,

                read_message_history=True,

                connect=True,

                speak=True,

                use_application_commands=True

            )

        }



        # 🏗️ Создание категории

        category_name = "──〢・RustInfo"

        new_category = await guild.create_category(category_name)

        await new_category.edit(position=0)



        # 📂 Создание каналов

        new_channel_info = await new_category.create_text_channel("Monitoring")

        new_channel_alerts = await new_category.create_text_channel("Alerts")



        # 💾 Сохраняем в БД

        await add_or_update_guild_channels(

            guild.id, new_category.id, new_channel_info.id, new_channel_alerts.id

        )



        print(f"✅ Каналы созданы: {new_category.id}, {new_channel_info.id}, {new_channel_alerts.id}")



    except discord.Forbidden:

        await send_message_to_guild(guild, f"❌ Недостаточно прав для создания категории и каналов в **{guild.name}**.")

    except Exception as e:

        await send_message_to_guild(guild, f"❌ Произошла ошибка при создании каналов: {e}")











async def update_server_info(guild, server_id):

    """Обновляет информацию о сервере в Discord с учетом списка игроков и их статуса (онлайн/оффлайн)."""

    guild_id = guild.id

    alert_status = await get_alert_status(guild_id)

    # ✅ Получаем список онлайн-игроков через API BattleMetrics

    online_players = online_players_cache.get(guild_id)

    # 🔍 1. Получаем `channel_id` из базы

    async with aiosqlite.connect("servers.db") as db:

        async with db.execute("SELECT channel_info_id FROM guilds WHERE guild_id = ?", (guild.id,)) as cursor:

            channel_row = await cursor.fetchone()



    if not channel_row:

        print(f"⚠ Ошибка: Канал не найден в базе для гильдии {guild.name}.")

        return



    channel_id = channel_row[0]

    channel = guild.get_channel(channel_id)

    if not channel:

        print(f"⚠ Ошибка: Канал с ID {channel_id} не найден в гильдии {guild.name}.")

        return



    # 🔍 2. Проверяем, выбран ли сервер

    if server_id is None or server_id == 0:

        embed = discord.Embed(

            title="🔧 RustInfo Bot — Ваш помощник в мире Rust! [ver. 0.0.3]",

            description="✨ *Тестовый режим* — работа бота может быть **нестабильной**. Пожалуйста, учитывайте это при использовании.",

            color=discord.Color.blue()

        )



        embed.set_thumbnail(

            url="https://cdn.discordapp.com/attachments/606094558413062165/1340082982614208614/image-removebg-preview.png"

        )



        embed.add_field(

            name="🔍 Что умеет этот бот?",

            value=(

                "📈 **Мониторинг сервера** — показывает информацию о выбранном сервере и обновляет данные каждые **10 секунд**.\n"

                "🎮 **Поиск игроков** — быстрый поиск игроков по имени на выбранном сервере.\n"

                "🟢 **Статус игроков** — отображает список игроков и их статус (**онлайн/оффлайн**) с обновлением каждые **2–4 минуты**."

            ),

            inline=False

        )



        embed.add_field(

            name="🛠 Как получить ID сервера?",

            value=(

                "1️⃣ Перейдите на сайт 👉 [BattleMetrics](https://www.battlemetrics.com/servers/rust)\n"

                "2️⃣ Найдите нужный сервер в списке.\n"

                "3️⃣ Скопируйте **ID сервера** из поисковой строки браузера."

            ),

            inline=False

        )



        embed.add_field(

            name="🔑 Как добавить сервер?",

            value=(

                "1️⃣ Нажмите кнопку **[Найти сервер]** ниже.\n"

                "2️⃣ Вставьте ранее скопированный **ID сервера**.\n"

                "3️⃣ ✅ Готово! Теперь бот будет отображать информацию по выбранному серверу."

            ),

            inline=False

        )

        embed.set_image(

            url="https://cdn.discordapp.com/attachments/1340093391278440541/1340667188910227557/image.png?ex=67b3311e&is=67b1df9e&hm=01fba7f88bec99b2f43c92b11a1b5673d3e5383a203ea0230587baf65d588b8f&")

        embed.set_footer(text="✨ RustInfo Bot — Ваш надежный помощник в мире Rust! 🔥🌿")





        existing_message = None



        if channel.permissions_for(channel.guild.me).view_channel and channel.permissions_for(

                channel.guild.me).read_message_history:

            try:

                async for message in channel.history(limit=5):

                    if message.embeds and message.embeds[0].title:

                        existing_message = message

                        break

            except discord.Forbidden:

                print(f"❌ Нет доступа к истории сообщений в `{channel.name}`.")

            except discord.HTTPException as e:

                print(f"⚠️ Ошибка при получении истории сообщений: {e}")

        else:

            print(f"⚠️ Боту не хватает прав для чтения истории сообщений или просмотра канала `{channel.name}`.")



        view = ServerSearchView(buttons_to_show=["find_server"])  # Кнопки для сервера







        if existing_message:

            try:

                await existing_message.edit(embed=embed, view=view)

                print(f"✅{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} Сообщение обновлено на канале {guild.name}.")

                await asyncio.sleep(3)

            except discord.NotFound:

                print(f"⚠ Сообщение не найдено (404), создаем новое!")

                existing_message = None  # Создаем новое сообщение

        else:

            try:

                await channel.purge(limit=5)  # 🧹 Очищаем последние 5 сообщений

            except discord.NotFound:

                print(f"⚠ Сообщение уже удалено (404) в канале {channel.name}")

            except discord.Forbidden:

                print(f"❌ Бот не имеет прав на удаление сообщений в {channel.name}")

            except discord.HTTPException as e:

                print(f"❌ Ошибка при удалении сообщений: {e}")



            await channel.send(embed=embed, view=view)  # 📤 Отправляем новое сообщение

            print(f"✅ Новое сообщение отправлено в канал {guild.name}.")

        #print(f"{guild.name} не использует бота.")

        return



    # 🔍 3. Ищем сервер в базе

    server_record = await add_server_if_not_exists(server_id)



    if not server_record:

        print(f"❌ Ошибка: Сервер {server_id} не найден в BattleMetrics API.")

        await channel.send(

            f"❌ Ошибка: Сервер с ID `{server_id}` не найден в BattleMetrics API. Пожалуйста, попробуйте снова."

        )

        server_id = 0

        # ✅ Обновляем active_server_id в базе данных на 0

        await set_active_server(guild.id, server_id)



        return



    server_name, ip, port = server_record

    # 🛠 4. Получаем данные через `gamedig`
    if guild_id not in gamedig_cache:
        gamedig_cache[guild_id] = {"count": 0, "old_data": None}
    # Инициализируем словарь для данных gamedig — чтобы не оставлять тут кортеж из БД
    server_data = {}
    try:
              
        result = await asyncio.to_thread(  
            subprocess.run, [GAMEDIG_PATH, "--type", "rust", "--host", ip, "--port", str(port)],
            capture_output=True, text=True, check=True
        )
        
        #print(f"🔍 Получаем данные сервера {server_name} ({ip}:{port}) через gamedig...")
        server_data = json.loads(result.stdout)
        
        if "name" in server_data:
            gamedig_cache[guild_id]["count"] = 0
            gamedig_cache[guild_id]["old_data"] = server_data
            
            
        if server_data["error"] == "Failed all 2 attempts":
            gamedig_cache[guild_id]["count"] += 1
            count = gamedig_cache[guild_id]["count"]
            print(f"❌[GAMEDIG] - [{guild.name}] Попытка: [{count}]")

            if count <= 5 and gamedig_cache[guild_id]["old_data"]:
                print("🔁 Используем сохранённые старые данные")
                server_data = gamedig_cache[guild_id]["old_data"]
            else:
                old_data = gamedig_cache[guild_id].get("old_data")
                server_name = old_data.get("name", "Unknown") if old_data else "Unknown"
                print(f"❌[GAMEDIG] - [{guild.name}] сервер {server_name} отключен")
                server_data = server_data

    except Exception as e:
        pass
        


    # 📥 5. Извлекаем данные о сервере

    players = server_data.get("numplayers", "?")

    max_players = server_data.get("maxplayers", "?")

    status = "🟢 Онлайн" if server_data.get("ping") is not None else "🔴 Оффлайн"

    map_name = server_data.get("map", "Неизвестно")

    connect = server_data.get("connect", "Неизвестно")

    ping = server_data.get("ping", "?")

    version = server_data.get("version", "?")



    # 📝 6. Создаем прогресс-бар

    progress_bar = generate_progress_bar(players, max_players)



    # 📋 7. Проверяем онлайн-статус игроков из базы



    # 📝 8. Создаем Embed

    embed = discord.Embed(

        title=f"ℹ Сервер: {server_name}",

        color=discord.Color.green() if status == "🟢 Онлайн" else discord.Color.red()

    )

    embed.add_field(name="📊 Загруженность сервера", value=f"`{progress_bar}`", inline=False)

    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/606094558413062165/1340082982614208614/image-removebg-preview.png")

    embed.add_field(name="Статус", value=status, inline=True)

    embed.add_field(name="🎮 Версия игры:", value=f"`{version}`", inline=True)

    embed.add_field(name="👥 Игроков онлайн", value=f"{players} / {max_players}", inline=True)

    embed.add_field(name="🗺️ Карта", value=map_name, inline=True)

    embed.add_field(name="📡 Пинг:", value=f"`{ping}` мс", inline=True)
    
    embed.add_field(name="Браузер", value=f"[Battlemetrics](https://www.battlemetrics.com/servers/rust/{server_id})", inline=True)

    embed.add_field(name="🌎 IP адрес", value=f"```client.connect {connect}```", inline=False)

    embed.add_field(

        name="🔗 Полезные ссылки",

        value=(

            "[🤖 Добавить Бота RustInfo](https://discord.com/oauth2/authorize?client_id=1334943377124495421&permissions=8&integration_type=0&scope=bot) | "

            "[💬 Поддержка бота](https://discord.gg/BvujSBJ5wz)"

        ),

        inline=False

    )

    embed.add_field(

        name="📋 Статус игроков   Обновление(2~4 мин)",

        value="\n".join(  # 🔄 Добавляем двойной перевод строки между игроками

            [

                (

                    f"🟢 **{player['name']}**     "

                    f"🆔  `{player['id']}`\n"

                    f"🌐 Сервер: `{player['server']}`\n"

                    #f"⏱ Время в игре: `{player['time_played']} мин`\n"

                    #f"🕒 Последний вход: `{player['last_seen']}`"

                ) if player['status'] == "online"

                else (

                    f"🔴 **{player['name']}**     "

                    f"🆔  `{player['id']}`\n"

                    #f"🌐 Последний сервер: `{player['server']}`\n"

                    #f"🕒 Последний вход: `{player['last_seen']}`"

                )

                for player in online_players

            ]

        ) if online_players else "Нет данных об игроках.",

        inline=True

    )

    embed.set_footer(text="🌿 RustInfo Bot — Лучший помощник для игроков Rust!")

    #await channel.purge(limit=5)

    #123

    # 🔍 9. Проверяем, есть ли старый Embed в канале

    existing_message = None

    async for message in channel.history(limit=5):

        if message.embeds and message.embeds[0].title == f"ℹ Сервер: {server_name}":

            existing_message = message

            break

    view = ServerSearchView(alert_status=alert_status)  # Кнопки для сервера

    #print(f"на канале {guild.name} уведомления  {alert_status}")



    if existing_message:

        try:

            await existing_message.edit(embed=embed, view=view)

            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ✅ Сообщение обновлено на канале {guild.name}.")

        except discord.NotFound:

            print(f"⚠ Сообщение не найдено (404), создаем новое!")

            existing_message = None  # Создаем новое сообщение

    else:

        try:

            await channel.purge(limit=5)  # 🧹 Очищаем последние 5 сообщений

        except discord.NotFound:

            print(f"⚠ Сообщение уже удалено (404) в канале {channel.name}")

        except discord.Forbidden:

            print(f"❌ Бот не имеет прав на удаление сообщений в {channel.name}")

        except discord.HTTPException as e:

            print(f"❌ Ошибка при удалении сообщений: {e}")



        # await channel.send(embed=embed, view=view)  # 📤 Отправляем новое сообщение

        await channel.send(embed=embed, view=view)



        print(f"✅ Новое сообщение отправлено в канал {guild.name}.")





async def safe_update_server(bot, guild_id, channel_id, server_id):
    async with SEMAPHORE:
        global semaphore_load_counter
        semaphore_load_counter += 1
        #print(f"🔢 Семафор загрузил: {semaphore_load_counter}")
        guild = bot.get_guild(guild_id)
        if guild is None:
            print(f"⚠️ Сервер с ID {guild_id} не найден. Возможно, бот был удалён.")
            return
        try:
            await update_server_info(guild, server_id)
            
        except Exception as e:
            print(f"❌ Ошибка при обновлении сервера {server_id} для гильдии {guild_id}: {e}")


@tasks.loop(seconds=30)
async def update_server_periodically(bot):
    global semaphore_load_counter
    try:
        async with aiosqlite.connect("servers.db") as db:
            async with db.execute("SELECT guild_id, channel_info_id, active_server_id FROM guilds") as cursor:
                guilds = await cursor.fetchall()

        tasks_list = [
            safe_update_server(bot, guild_id, channel_id, server_id)
            for guild_id, channel_id, server_id in guilds
        ]

        await asyncio.gather(*tasks_list)
        print("✅ Цикл обновления завершён.\n")
        print(f"📊 Всего серверов загружено в семафор: {semaphore_load_counter}")
        semaphore_load_counter = 0  # сбрасываем на следующий цикл

    except Exception as e:
        print(f"❌ Ошибка в `update_server_periodically`: {e}")

