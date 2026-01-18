### bot.py
import asyncio.tasks
import aiosqlite
import discord
from io import StringIO
from discord.ext import  tasks
from channel_utils import update_server_periodically, create_category_channels, delete_rustinfo_structure
from config import DISCORD_BOT_TOKEN, reset_request_counters
from database import remove_guild_from_db, add_guild_to_db, init_db, drop_rust_plus_servers_table, update_guild_name
from cache import  update_online_players_cache_for_guild  # ✅ Импортируем общий кэш
from discord.http import HTTPClient
from discord.ext import commands
from plus import setup_plus_module, get_rust_map, check_servers_status, get_entity_info
from FCM import load_all_fcm_from_db, fcm_heartbeat_monitor
authorized_user_id = 348409098640818178
GUILD_ID_ALLOWED = 1336416466605572149
BUMP_BOT_ID = 315926021457051650
BUMP_CHANNEL_ID = 1334251716253847662
TESTER_ROLE_NAME = "Тестер"
requests_to_discord = 0  # 🔄 Глобальный счётчик запросов
original_request = HTTPClient.request
intents = discord.Intents.all()
intents.guilds = True  # Нужно включить!
intents.members = True  # Желательно
intents.messages = True  # 🔥 ← обязательно
intents.message_content = True  # 🔥 ← обязательно для команд
bot = commands.Bot(command_prefix="!", intents=intents,help_command=None)
bot.remove_command("help")

@bot.command(name="info")
async def get_info(ctx, *, device_name: str):
    await ctx.send(f"🔎 Получена информация по устройству: `{device_name}`")
    guild_id = ctx.guild.id
    username = ctx.author.display_name
    guild_name = ctx.guild.name
    buffer, error = await get_entity_info(device_name, guild_id, username, guild_name)
 
    if error:
        await ctx.send(error)
        return

    await ctx.send(file=discord.File(buffer, filename="inventory.png"))
    print("✅ Отправлено изображение инвентаря")

@bot.event
async def on_message(message: discord.Message):
    if (
            message.channel.id != BUMP_CHANNEL_ID
            or message.guild is None
            or message.guild.id != GUILD_ID_ALLOWED
            or message.author.id != BUMP_BOT_ID
    ):
        await bot.process_commands(message)
        return

    # Проверяем содержание сообщения
    if message.embeds:
        embed = message.embeds[0]
        if embed.description and "Top Discord Servers" in embed.description and "Server bumped by @" in embed.description:
            try:
                nickname = embed.description.split("Server bumped by @")[1].split(":")[0].strip()
            except IndexError:
                print("❌ Не удалось извлечь ник из embed.")
                return

        # Ищем участника по нику
        member = discord.utils.find(lambda m: m.name == nickname or m.display_name == nickname, message.guild.members)

        if not member:
            print(f"❌ Участник @{nickname} не найден на сервере.")
            return

        # Отправляем благодарственное сообщение с реальным упоминанием
        thank_message = f"{member.mention} Благодарим за бамп сервера! Каждый голос важен для нас. В будущем вы будете получать бонусы за ваш голос."
        await message.channel.send(thank_message)
        print(f"✅ Отправлено благодарственное сообщение для {member.name}")

        # Запускаем таймер
        await asyncio.sleep(3 * 3600 + 55 * 60)  # 3 часа 55 минут

        # Отправляем напоминание @everyone
        await message.channel.send("@everyone Бампни сервер, твой голос очень важен! Используйте `/bump` 🚀")
        print("✅ Отправлено напоминание о бампе!")

    # Обрабатываем команды дальше
    print(f"Обрабатываем команды до")
    await bot.process_commands(message)
    print(f"Обрабатываем команды дальше")

@bot.event
async def on_member_join(member: discord.Member):
    """📥 Когда новый участник заходит на сервер"""

    # Проверяем, что участник зашёл на правильный сервер
    if member.guild.id != GUILD_ID_ALLOWED:
        return  # ❌ Не обрабатываем других гильдий

    # Название канала для приветствий
    welcome_channel_name = "приветствуем"

    # Название роли, которую нужно выдать
    role_name = "Rust player"

    # Ищем канал
    channel = discord.utils.get(member.guild.text_channels, name=welcome_channel_name)
    if channel:
        await channel.send(f"👋 Добро пожаловать, {member.mention}! Мы рады видеть тебя здесь!")

    # Ищем роль
    role = discord.utils.get(member.guild.roles, name=role_name)
    if role:
        await member.add_roles(role)
        print(f"✅ Выдана роль '{role_name}' участнику {member.name}")
    else:
        print(f"❌ Роль '{role_name}' не найдена на сервере {member.guild.name}.")

@bot.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):
    await delete_rustinfo_structure(ctx.guild)
    await create_category_channels(ctx.guild)
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Список команд", color=discord.Color.blue())
    embed.add_field(name="!setup", value="Пересоздание каналов и категории (использовать только при необходимости)", inline=False)
    embed.add_field(name="!map", value="Отображение карты сервера с расположением всех тиммейтов на карте.( если подключен Rust+)", inline=False)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/606094558413062165/1340082982614208614/image-removebg-preview.png")

    await ctx.send(embed=embed)

@bot.command(name="tester")
async def tester(ctx):
    """📌 Добавляет роль Tester пользователю, если он в разрешённой гильдии"""

    # Проверяем, в правильной ли гильдии вызвана команда
    if ctx.guild.id != GUILD_ID_ALLOWED:
        return

    # Получаем объект роли
    role = discord.utils.get(ctx.guild.roles, name=TESTER_ROLE_NAME)
    if role is None:
        await ctx.send("❌ Ошибка: Роль 'Tester' не найдена в гильдии!")
        return

    # Проверяем, есть ли уже роль у пользователя
    if role in ctx.author.roles:
        await ctx.send("❌ У вас уже есть роль Tester!")
    else:
        # Добавляем роль пользователю
        await ctx.author.add_roles(role)
        await ctx.send(f"✅ **Вы     стали тестером данного проекта!** 🎉\n"
                       "🔹 Вам теперь доступны приватные каналы.\n"
                       "🔹 Ознакомьтесь с инструкцией по подключению **Rust+**.")

@bot.command(name="map")
async def send_rust_map(ctx):
    """🗺 Команда !map — Получает карту и отправляет в Discord"""
    await ctx.typing()
    #await ctx.send("📡 Запрос карты... Это может занять несколько секунд.")

    guild_id = ctx.guild.id
    username = ctx.author.display_name
    guild_name = ctx.guild.name

    image_bytes, error = await get_rust_map(guild_id, username, guild_name)

    if error:
        await ctx.send(error)
        return

    if image_bytes is None:
        await ctx.send("⚠️ Ошибка: Карта не была загружена.")
        return

    print("✅ Карта успешно получена, отправляем в Discord...")
    await ctx.send("🗺 **Карта сервера Rust:**", file=discord.File(image_bytes, "rust_map.png"))
    print("Отправлено")

@bot.command(name='alert')
@commands.has_permissions(administrator=True)
async def send_alert(ctx, *, message: str):
    """
    📢 Отправляет embed-уведомление во все гильдии в канал Alerts.
    Использование: !alert <сообщение>
    """
    if ctx.author.id != authorized_user_id:
        await ctx.send("❌ У вас нет доступа к этой команде.")
        return


    embed = discord.Embed(
        title="📢 Новое Уведомление",
        description=f"{message}",  # 📜 Выделение текста как блока кода
        color=discord.Color.orange()
    )
    embed.add_field(
        name="💬",
        value="[Сообщество RustInfo](https://discord.gg/BvujSBJ5wz)",
        inline=False
    )
    embed.set_footer(
        text="🌿 RustInfo Bot — Лучший помощник для игроков Rust!",
        icon_url="https://cdn.discordapp.com/attachments/606094558413062165/1340082982614208614/image-removebg-preview.png"
    )

    sent_count = 0  # Счётчик успешно отправленных сообщений
    for guild in bot.guilds:
        # 🔍 Ищем канал Alerts по имени
        alerts_channel = discord.utils.get(guild.text_channels, name="alerts")
        if alerts_channel:
            try:
                await alerts_channel.send(embed=embed)
                sent_count += 1
                print(f"✅ Уведомление отправлено в {guild.name} ({alerts_channel.name})")
            except discord.Forbidden:
                print(f"❌ Нет прав на отправку в {guild.name} ({alerts_channel.name})")
        else:
            print(f"⚠️ Канал 'Alerts' не найден в {guild.name}.")

    await ctx.send(f"✅ Уведомление успешно отправлено в {sent_count} гильдий из {len(bot.guilds)}.")

@bot.command(name='promo')
@commands.has_permissions(administrator=True)
async def promo(ctx):
    """
    📢 Отправляет embed-уведомление во все гильдии в канал Alerts.
    Использование: !alert <сообщение>
    """
    print(f"promo")
    if ctx.author.id != authorized_user_id:
        await ctx.send("❌ У вас нет доступа к этой команде.")
        return

    announcement = (
        "📢 **Открытие уже в это Воскресенье, 06.04.2025!**\n\n"
        "**RS.RUST-CLUB.COM X5 CLANS**\n\n"
        "🗺️ Авторская карта, клановые баталии, горячие перестрелки и войны за территории ждут Вас!\n"
        "🎁 Подпишись на наш DS и получи **подарочный Топ-Premium на 32 дня** в честь открытия!\n\n"
        "🌐 Сайт: https://rs.rust-club.com/?utm_content=ds-link&utm_term=brro-promo\n"
        "💬 Discord: https://discord.gg/rust-club\n\n"
        "🌿 RustInfo Bot — Лучший помощник для игроков Rust!"
    )

    sent_count = 0
    for guild in bot.guilds:
        alerts_channel = discord.utils.get(guild.text_channels, name="alerts")
        if alerts_channel:
            try:
                await alerts_channel.send(content=announcement)
                sent_count += 1
                print(f"✅ Уведомление отправлено в {guild.name} ({alerts_channel.name})")
            except discord.Forbidden:
                print(f"❌ Нет прав на отправку в {guild.name} ({alerts_channel.name})")
        else:
            print(f"⚠️ Канал 'Alerts' не найден в {guild.name}.")

    await ctx.send(f"✅ Уведомление успешно отправлено в {sent_count} гильдий из {len(bot.guilds)}.")

@bot.command(name='rebuild_db')
async def rebuild_db(ctx):
    """🔄 Восстанавливает базу данных и пересоздаёт категорию и каналы для всех гильдий."""

    if ctx.author.id != authorized_user_id:
        await ctx.send("❌ У вас нет доступа к этой команде.")
        return

    await ctx.send("🔄 🔧 Начинаю восстановление базы данных и структуры каналов...")

    async with aiosqlite.connect("servers.db") as db:
        for guild in bot.guilds:
            await ctx.send(f"🏛 Проверка сервера: **{guild.name}** (ID: `{guild.id}`)")

            # 🔐 Проверка прав бота в гильдии
            permissions = guild.me.guild_permissions
            if not (permissions.manage_channels and permissions.manage_roles):
                await ctx.send(f"⚠️ Нет необходимых прав на сервере `{guild.name}`. Пропускаем.")
                continue

            # 🔄 Принудительное обновление кеша каналов
            await guild.fetch_channels()

            # 🔍 Проверяем наличие категории RustInfo
            rustinfo_category = discord.utils.get(guild.categories, name="──〢・RustInfo")
            monitoring_channel = None
            alerts_channel = None

            if rustinfo_category:
                monitoring_channel = discord.utils.get(rustinfo_category.channels, name="monitoring")
                alerts_channel = discord.utils.get(rustinfo_category.channels, name="alerts")

                # 🗑 Удаляем старые каналы monitoring и alerts, если они существуют
                if monitoring_channel:
                    await monitoring_channel.delete()
                    await ctx.send(f"🗑 Канал Monitoring удалён на сервере `{guild.name}`.")
                    await asyncio.sleep(1)

                if alerts_channel:
                    await alerts_channel.delete()
                    await ctx.send(f"🗑 Канал Alerts удалён на сервере `{guild.name}`.")
                    await asyncio.sleep(1)
                # 🗑 Удаляем категорию RustInfo
                await rustinfo_category.delete()
                await ctx.send(f"🗑 Категория RustInfo удалена на сервере `{guild.name}`.")
                await asyncio.sleep(2)

            # 🔧 Создаём категорию и каналы с нуля
            await create_category_channels(guild)
            await guild.fetch_channels()  # Снова обновляем кеш

            # 🔍 Обновляем ссылки на заново созданные каналы
            rustinfo_category = discord.utils.get(guild.categories, name="──〢・RustInfo")
            monitoring_channel = discord.utils.get(rustinfo_category.channels, name="monitoring")
            alerts_channel = discord.utils.get(rustinfo_category.channels, name="alerts")

            # 🛡 Обновляем или добавляем данные в базу данных
            if rustinfo_category and monitoring_channel and alerts_channel:
                await db.execute("""
                    INSERT INTO guilds (guild_id, category_id, channel_info_id, channel_alerts_id, vip)
                    VALUES (?, ?, ?, ?, 0)
                    ON CONFLICT(guild_id) DO UPDATE SET
                        category_id = excluded.category_id,
                        channel_info_id = excluded.channel_info_id,
                        channel_alerts_id = excluded.channel_alerts_id
                """, (guild.id, rustinfo_category.id, monitoring_channel.id, alerts_channel.id))
                await ctx.send(f"✅ Сервер `{guild.name}` успешно восстановлен в базе данных.")
            else:
                await ctx.send(f"❌ Ошибка: Не удалось восстановить структуру для сервера `{guild.name}`.")

            await asyncio.sleep(2)  # ⏳ Небольшая задержка между обработкой серверов

        await db.commit()

    await ctx.send("✅ 🎉 Восстановление базы данных и структуры каналов завершено успешно!")




@bot.command(name="remove_vip")
async def remove_vip(ctx, guild_id: int):
    print("remove_vip")
    """🔓 Снимает VIP-статус для указанной гильдии: !remove_vip <guild_id>"""
    if ctx.author.id != authorized_user_id:
        await ctx.send("❌ У вас нет доступа к этой команде.")
        return

    async with aiosqlite.connect("servers.db") as db:
        # 🏃 Проверяем, существует ли гильдия
        async with db.execute("SELECT guild_id FROM guilds WHERE guild_id = ?", (guild_id,)) as cursor:
            if not await cursor.fetchone():
                await ctx.send(f"❌ Гильдия с ID `{guild_id}` не найдена в базе данных.")
                return

        # 🔓 Обновляем VIP-статус на 0
        await db.execute("UPDATE guilds SET vip = 0 WHERE guild_id = ?", (guild_id,))
        await db.commit()
    await ctx.send(f"🌟 VIP-статус **выключён** для гильдии с ID `{guild_id}`.")
@bot.command(name="set_vip")
async def set_vip(ctx, guild_id: int):
    """🌟 Устанавливает VIP-статус для указанной гильдии: !set_vip <guild_id>"""
    if ctx.author.id != authorized_user_id:
        await ctx.send("❌ У вас нет доступа к этой команде.")
        return

    async with aiosqlite.connect("servers.db") as db:
        # 🏃 Проверяем, существует ли гильдия
        async with db.execute("SELECT guild_id FROM guilds WHERE guild_id = ?", (guild_id,)) as cursor:
            if not await cursor.fetchone():
                await ctx.send(f"❌ Гильдия с ID `{guild_id}` не найдена в базе данных.")
                return

        # 🌟 Обновляем VIP-статус
        await db.execute("UPDATE guilds SET vip = 1 WHERE guild_id = ?", (guild_id,))
        await db.commit()

    await ctx.send(f"🌟 VIP-статус **включён** для гильдии с ID `{guild_id}`.")


@bot.command()
async def owner(ctx):
    await ctx.send("Mr.Borro мой создатель  ID: 348409098640818178")
#Админская команда для получения информации
@bot.command()
async def guildinfo(ctx):
    """Выводит информацию о всех каналах с количеством пользователей с доступом."""
    authorized_user_id = 348409098640818178
    if ctx.author.id != authorized_user_id:
        await ctx.send("❌ У вас нет доступа к этой команде.")
        return

    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT guild_id, channel_info_id FROM guilds") as cursor:
            guilds = await cursor.fetchall()

    if not guilds:
        await ctx.send("⚠ Нет данных о гильдиях в базе данных.")
        return

    total_members_count = 0
    users_with_access_count = 0
    result_lines = []

    for guild_id, channel_id in guilds:
        guild = bot.get_guild(guild_id)
        if not guild:
            result_lines.append(f"\n❌ Гильдия с ID `{guild_id}` не найдена у бота.")
            continue
        await update_guild_name(guild_id, guild.name)
        admins = [
            member.display_name
            for member in guild.members
            if member.guild_permissions.administrator
        ]
        admins_formatted = ", ".join(admins) if admins else "Нет администраторов"
        channel = guild.get_channel(channel_id)
        if not channel:
            result_lines.append(
                f"\n📛 **Гильдия:** {guild.name}\n"
                f"⚠ Канал с ID `{channel_id}` не найден."
            )
            continue

        accessible_members = [m for m in guild.members if channel.permissions_for(m).read_messages]
        total_members = guild.member_count
        users_with_access = len(accessible_members)
        total_members_count += total_members
        users_with_access_count += users_with_access

        result_lines.append(
            f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏛 **Гильдия:** {guild.name}\n"
            f"📂 **Канал:** {channel.name} ({channel.id})\n"
            f"👥 **Пользователи с доступом:** {users_with_access}\n"
            f"🌐 **Общее количество участников:** {total_members}\n"
            f"🛡 **Администраторы:** {admins_formatted}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

    result_message = "\n".join(result_lines)

    # Итоги
    await ctx.send(f"👥 Общее количество пользователей: `{total_members_count}`")
    await ctx.send(f"✅ Пользователей с доступом: `{users_with_access_count}`")

    if len(result_message) <= 4000:
        await ctx.send(result_message)
    else:
        # 📎 Отправка как файл
        file = discord.File(fp=StringIO(result_message), filename="guildinfo.txt")
        await ctx.send("📄 Список слишком длинный — отправлено как файл:", file=file)

@bot.command()
async def remove_guild(ctx, guild_id: int):
    """Удаляет все данные гильдии из БД по guild_id (только для создателя)"""
    if ctx.author.id != authorized_user_id:
        await ctx.send("❌ У вас нет доступа к этой команде.")
        return
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT guild_id FROM guilds WHERE guild_id = ?", (guild_id,)) as cursor:
            if not await cursor.fetchone():
                await ctx.send(f"❌ Гильдия с ID `{guild_id}` не найдена в базе данных.")
                return

    await remove_guild_from_db(guild_id)
    await ctx.send(f"✅ Все данные гильдии с ID `{guild_id}` удалены из базы данных.")

@tasks.loop(seconds=60)
async def update_online_players_cache(bot):
    """
    🔄 Периодически обновляет кэш онлайн-игроков для всех гильдий
    и отправляет уведомления о смене статуса игроков при необходимости.
    """
    async with aiosqlite.connect("servers.db") as db:
        async with db.execute("SELECT guild_id FROM guilds") as cursor:
            guilds = await cursor.fetchall()

    for (guild_id,) in guilds:
        await update_online_players_cache_for_guild(bot, guild_id)
    #print(f"🌐 Кэш обновлён: {online_players_cache}")


@bot.event
async def on_ready():
    update_online_players_cache.start(bot)  # 🚀 Запуск обновления онлайн-игроков раз в 5 минут
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,name=f"Смотрит за {len(bot.guilds)} серверами"))
    if not update_server_periodically.is_running():
        update_server_periodically.start(bot)
    reset_request_counters.start()
    check_servers_status.start()
    await load_all_fcm_from_db() #Запуск FCM для всех гильдий при старте
    await setup_plus_module()
    if not fcm_heartbeat_monitor.is_running():
        fcm_heartbeat_monitor.start()
    print(f"✅ {bot.user} запущен и работает на {len(bot.guilds)} серверах!")
    print(f"✅ {bot.user} Инициализация базы данных, выполнена успешно!")
@bot.event
async def on_guild_remove(guild):
    # Обновляем статус бота
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=f"Смотрит за {len(bot.guilds)} серверами"))
    # Удаляем сервер из базы данных
    await remove_guild_from_db(guild.id)
# Функция обработки присоединения бота к серверу
@bot.event
async def on_guild_join(guild):
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=f"Смотрит за {len(bot.guilds)} серверами"))
    await add_guild_to_db(bot, guild)
    # Обновляем статус бота
    #await ensure_text_channel(guild)
    await create_category_channels(guild)




async def main():
    #await drop_rust_plus_servers_table()
    #await asyncio.sleep(5)
    await init_db()
    """🔥 Основная функция бота"""
    try:


        print("🚀 Запускаем Discord-бота...")
        await bot.start(DISCORD_BOT_TOKEN)
        #await asyncio.gather(bot.start(DISCORD_BOT_TOKEN))  # ✅ Запускаем бота

    except asyncio.CancelledError:
        print("⚠️ Бот остановлен (CancelledError). Завершаем работу...")
    except KeyboardInterrupt:
        print("🛑 Бот остановлен вручную (Ctrl+C)")
    finally:
        print("✅ Очистка ресурсов и закрытие бота...")

if __name__ == "__main__":
    try:
        asyncio.run(main())  # ✅ Запускаем бота
    except KeyboardInterrupt:
        print("🛑 Бот был закрыт вручную. Выход...")
