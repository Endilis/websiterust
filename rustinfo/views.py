### views.py
import discord
import asyncio
import json
import aiosqlite
from discord.ui import Button, View, Modal, Select, TextInput
from database import delete_player, get_players_from_guild, get_info_channel_id, save_fcm_details, set_active_server
from database import add_player_to_db, check_player_exists, is_guild_vip, get_player_count_for_guild
from FCM import start_fcm_for_guild

class SwitchView(View):
    def __init__(self):
        super().__init__(timeout=None)  # Бессрочный View

    @discord.ui.button(label="Включить", style=discord.ButtonStyle.green, custom_id="switch_on")
    async def switch_on(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🟢 Включить", ephemeral=True)

    @discord.ui.button(label="Выключить", style=discord.ButtonStyle.red, custom_id="switch_off")
    async def switch_off(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔴 Выключить", ephemeral=True)

# 🎯 Функция для отправки embed + кнопок
async def send_switch_embed(bot, guild_id: int, device_name: str):
    guild = bot.get_guild(guild_id)
    if not guild:
        print(f"❌ Гильдия {guild_id} не найдена")
        return

    category = discord.utils.get(guild.categories, name="──〢・RustInfo")
    if not category:
        print(f"❌ Категория 'RustInfo' не найдена")
        return

    channel = discord.utils.get(guild.text_channels, name="rustplus")
    if not channel:
        channel = await category.create_text_channel(name="rustplus")
        print(f"✅ Создан канал 'rustplus' в {guild.name}")

    embed = discord.Embed(
        title="Smart Switch",
        description=f"Имя устройства: **{device_name}**",
        color=discord.Color.green()
    )

    await channel.send(embed=embed, view=SwitchView())

class RustPlusModal(Modal, title="🔗 Подключение к Rust+"):
    """Модальное окно для ввода данных сервера Rust+"""

    rust_data = TextInput(label="Введите JSON", style=discord.TextStyle.long)

    async def on_submit(self, interaction: discord.Interaction):
        """Обрабатывает ввод JSON-данных и сохраняет их в БД"""
        try:
            print("✅ Кнопка нажата")
            fcm_details = json.loads(self.rust_data.value)  # ✅ Парсим JSON сразу в fcm_details
            guild_id = interaction.guild.id  # ✅ Получаем ID гильдии

            await save_fcm_details(guild_id, fcm_details)
            print("Запись произведена успешно, переходим к старту FCM...")
            await start_fcm_for_guild(guild_id, fcm_details)
            print("Выполнен старт FCM...")
            await interaction.response.send_message("✅ Данные Rust+ сохранены!", ephemeral=True)
            #print(fcm_details)
        except json.JSONDecodeError:
            await interaction.response.send_message("❌ Ошибка: Некорректный JSON!", ephemeral=True)
        except KeyError as e:
            await interaction.response.send_message(f"❌ Ошибка: Отсутствует ключ {e} в JSON!", ephemeral=True)


class PlayerSearchModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Поиск игрока")
        self.nickname = discord.ui.TextInput(label="Введите ник игрока", placeholder="Player123")
        self.add_item(self.nickname)

    async def on_submit(self, interaction: discord.Interaction):
        from battlemetrics import search_player_by_nickname
        """Обрабатывает ввод ника и сразу выводит информацию об игроках"""
        nickname = self.nickname.value.strip()
        guild_id = interaction.guild.id

        await interaction.response.defer(ephemeral=True)  # Делаем ответ "в обработке"

        # Поиск игроков в BattleMetrics
        players = await search_player_by_nickname(nickname)

        if not players:
            await interaction.followup.send("❌ Игроки с таким ником не найдены!", ephemeral=True)
            return

        # ✅ Создаём Embed с информацией сразу
        embed = discord.Embed(title="📌 Найденные игроки", color=discord.Color.blue())
        view = PlayerSelectView(players, guild_id, interaction)

        for index, player in enumerate(players[:5]):  # Максимум 5 игроков
            embed.add_field(
                name=f"{index + 1}. {player['name']}",
                value=(
                    f"**ID:** `{player['id']}`\n"
                    f"**Статус:** {player['is_online']}\n"
                    f"**Сервер:** {player['server_name']}\n"
                    f"**Последний вход:** {player['last_seen']}"
                ),
                inline=False
            )

        # ✅ Отправляем сообщение с полной информацией и кнопками выбора
        message = await interaction.followup.send(embed=embed, view=view)
        view.set_message(message)  # Устанавливаем сообщение в `View` для удаления


class PlayerSelectView(discord.ui.View):
    """Класс для управления кнопками выбора игрока с проверкой лимита."""
    def __init__(self, players, guild_id, interaction):
        super().__init__(timeout=60)  # Кнопки активны 60 секунд
        self.players = players
        self.guild_id = guild_id
        self.interaction = interaction
        self.message = None

        for index, player in enumerate(players[:5]):  # Максимум 5 игроков
            button = discord.ui.Button(
                label=f"Выбрать {index + 1}",
                style=discord.ButtonStyle.primary,
                custom_id=f"select_player_{player['id']}"
            )
            button.callback = self.player_button_callback
            self.add_item(button)

    def set_message(self, message):
        """Устанавливает сообщение для удаления после выбора игрока."""
        self.message = message

    async def player_button_callback(self, interaction: discord.Interaction):
        from cache import update_online_players_cache_for_guild
        """Обрабатывает выбор игрока с проверкой лимита для VIP и обычных гильдий."""
        player_id = interaction.data["custom_id"].split("_")[-1]
        selected_player = next(p for p in self.players if p["id"] == player_id)

        async with aiosqlite.connect("servers.db") as db:
            if await check_player_exists(db, self.guild_id, selected_player["id"]):
                if self.message:
                    await self.message.delete()
                await interaction.response.send_message("Этот игрок уже добавлен!", ephemeral=True)
                return

            current_count = await get_player_count_for_guild(self.guild_id)
            vip_status = await is_guild_vip(self.guild_id)
            max_players = 8 if vip_status else 3

            if current_count >= max_players:
                await interaction.response.send_message(
                    f"❌ Достигнут лимит: {max_players} игроков для {'VIP' if vip_status else 'обычной'} гильдии.",
                    ephemeral=True
                )
                return

            await add_player_to_db(db, self.guild_id, selected_player["name"], selected_player["id"])
            await update_online_players_cache_for_guild(interaction.client, self.guild_id)

        if self.message:
            await self.message.delete()

        await interaction.response.send_message(f"✅ Игрок **{selected_player['name']}** добавлен в базу данных!", ephemeral=True)


# Класс выпадающего списка для удаления игрока
class PlayerSelect(Select):
    def __init__(self, players, message):
        self.message = message
        options = [discord.SelectOption(label=player) for player in players]
        super().__init__(placeholder="Выберите игрока для удаления", options=options)

    async def callback(self, interaction: discord.Interaction):
        await delete_player(interaction.guild.id, self.values[0])
        await interaction.response.send_message(f"Игрок `{self.values[0]}` удалён из базы данных.", ephemeral=True)
        await asyncio.sleep(1)
        await self.message.delete()

# Представление (View) с кнопкой удаления
class DeletePlayerView(View):
    def __init__(self, players, message):
        super().__init__()
        self.add_item(PlayerSelect(players, message))

# Кнопка удаления игроков
class DeleteButton(View):
    def __init__(self):
        super().__init__()
        self.add_item(Button(label="Удалить игрока", style=discord.ButtonStyle.danger, custom_id="delete_player"))

    @discord.ui.button(label="Удалить игрока", style=discord.ButtonStyle.danger)
    async def delete_player_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        players = await get_players_from_guild(interaction.guild.id)
        if not players:
            await interaction.response.send_message("Нет доступных игроков для удаления.", ephemeral=True)
            return
        message = await interaction.channel.send("Выберите игрока для удаления:")
        await message.edit(view=DeletePlayerView(players, message))


# Модальное окно для ввода ID сервера
class ServerIDModal(Modal, title="Поиск сервера"):
    server_id = TextInput(label="Введите ID сервера", placeholder="Например, 1234567890")

    async def on_submit(self, interaction: discord.Interaction):
        from channel_utils import update_server_info
        # Проверяем, что введенное значение - это число
        if self.server_id.value.isdigit():
            server_id = int(self.server_id.value)
            guild_id = interaction.guild.id  # Получаем ID сервера
            await set_active_server(guild_id, server_id)

            # Отправляем подтверждение пользователю
            await interaction.response.send_message(f"Вы успешно ввели ID сервера: {server_id}", ephemeral=True)
            print(f"Server ID {server_id} saved for guild {guild_id}")

            # Запускаем задачу для обновления Embed-сообщения
            await update_server_info(interaction.guild, server_id)
        else:
            # Если введено не число, отправляем сообщение об ошибке
            await interaction.response.send_message(
                "Ошибка! Введенный ID сервера должен быть числом. Пожалуйста, попробуйте снова.",
                ephemeral=True
            )


class ServerSearchView(View):
    def __init__(self, alert_status=0, buttons_to_show=None):
        super().__init__(timeout=None)
        # Верхний ряд кнопок
        self.find_server_button = Button(label="🔍 Найти сервер", style=discord.ButtonStyle.success)
        self.find_player_button = Button(label="🎮 Поиск игрока", style=discord.ButtonStyle.primary)
        self.delete_player_button = Button(label="🗑 Удалить игрока", style=discord.ButtonStyle.danger)

        # 🔗 Назначаем callbacks
        self.find_server_button.callback = self.find_server_callback
        self.find_player_button.callback = self.search_player_callback
        self.delete_player_button.callback = self.delete_player_callback

        # ⚡ Если кнопки не указаны, добавляем все верхние кнопки
        if buttons_to_show is None:
            buttons_to_show = ["find_server", "find_player", "delete_player", "notifications", "button5", "button6"]

        # 🎛 Добавляем верхние кнопки в зависимости от параметра buttons_to_show
        if "find_server" in buttons_to_show:
            self.add_item(self.find_server_button)
        if "find_player" in buttons_to_show:
            self.add_item(self.find_player_button)
        if "delete_player" in buttons_to_show:
            self.add_item(self.delete_player_button)

        # Нижний ряд кнопок (row=1) — Добавляем, ТОЛЬКО если они указаны
        if "notifications" in buttons_to_show:
            self.button4 = Button(
                label="Уведомления 🔔" if alert_status else "Уведомления 🔕",
                style=discord.ButtonStyle.danger if alert_status else discord.ButtonStyle.success,
                row=1
            )
            self.button4.callback = self.button4_callback
            self.add_item(self.button4)

        if "button5" in buttons_to_show:
            self.button5 = Button(label="🧹 Очистить чат", style=discord.ButtonStyle.secondary, row=1)
            self.button5.callback = self.button5_callback
            self.add_item(self.button5)

        if "button6" in buttons_to_show:
            self.rust_plus_button = Button(label="✨Rust+", style=discord.ButtonStyle.secondary, row=1)
            self.rust_plus_button.callback = self.rust_plus_callback
            self.add_item(self.rust_plus_button)

    # 🏃 Callback для кнопки "Найти сервер"
    async def find_server_callback(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        server_name = interaction.guild.name
        print(f"🔍 Кнопка 'Найти сервер' нажата на сервере: {server_name} (ID: {guild_id})")
        await interaction.response.send_modal(ServerIDModal())

    # 🔎 Callback для кнопки "Поиск игрока"
    async def search_player_callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PlayerSearchModal())

    # 🗑 Callback для кнопки "Удалить игрока"
    async def delete_player_callback(self, interaction: discord.Interaction):
        players = await get_players_from_guild(interaction.guild.id)
        if not players:
            await interaction.response.send_message("❌ Нет доступных игроков для удаления.", ephemeral=True)
            return
        unique_players = list(set(players))
        message = await interaction.channel.send("🗑 Выберите игрока для удаления:")
        await message.edit(view=DeletePlayerView(unique_players, message))

    # 🔔 Callback для кнопки уведомлений
    async def button4_callback(self, interaction: discord.Interaction):
        from database import toggle_alert, get_alert_status
        new_value = await toggle_alert(interaction.guild.id)

        # 🔄 Обновляем кнопку без обновления всего embed
        self.button4.label = "Уведомления 🔔" if new_value else "Уведомления 🔕"
        self.button4.style = discord.ButtonStyle.danger if new_value else discord.ButtonStyle.success

        await interaction.response.edit_message(view=self)

    async def button5_callback(self, interaction: discord.Interaction):
        """🧹 Обработчик кнопки очистки чата 'info' с корректной обработкой взаимодействия."""
        guild_id = interaction.guild.id
        channel_info_id = await get_info_channel_id(guild_id)
        info_channel = interaction.guild.get_channel(channel_info_id)

        # ✅ Продлеваем время обработки взаимодействия
        await interaction.response.defer(ephemeral=True)

        if info_channel:
            try:
                # 🧹 Очищаем последние 100 сообщений
                deleted = await info_channel.purge(limit=100)
                # ✅ Используем followup для отправки ответа
                await interaction.followup.send(
                    f"✅ Успешно очищено {len(deleted)} сообщений в чате **{info_channel.name}**.",
                    ephemeral=True
                )
            except discord.Forbidden:
                await interaction.followup.send(
                    "❌ У меня нет прав на удаление сообщений в этом канале.", ephemeral=True
                )
            except Exception as e:
                await interaction.followup.send(
                    f"⚠ Ошибка при очистке чата: {str(e)}", ephemeral=True
                )
        else:
            await interaction.followup.send("❌ Канал 'info' не найден.", ephemeral=True)

    async def rust_plus_callback(self, interaction: discord.Interaction):
        """Открывает модальное окно для подключения к Rust+"""
        await interaction.response.send_modal(RustPlusModal())
        #await interaction.response.send_message("Ну просил же...", ephemeral=True)






