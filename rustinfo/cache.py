from battlemetrics import get_online_players
from database import get_alert_status, get_alerts_channel_id
import discord
from datetime import datetime
online_players_cache = {}

def format_datetime(date_str: str) -> str:
    """Форматирует дату из строки '2025-02-23T18:41:23.628Z' в '2025-02-23 18:41:23'."""
    try:
        # 🕒 Удаляем 'Z' и преобразуем в читаемый формат
        dt = datetime.strptime(date_str.replace('Z', ''), "%Y-%m-%dT%H:%M:%S.%f")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return date_str  # 🔄 Если ошибка — возвращаем исходную строку


async def update_online_players_cache_for_guild(bot, guild_id: int):
    """🔔 Обновляет кэш и отправляет Embed с аватаром бота при изменении статуса игроков."""
    global online_players_cache
    current_online_players = await get_online_players(guild_id)
    previous_online_players = online_players_cache.get(guild_id, [])

    current_players_dict = {player["id"]: player for player in current_online_players}
    previous_players_dict = {player["id"]: player for player in previous_online_players}

    all_player_ids = set(current_players_dict.keys()) | set(previous_players_dict.keys())

    alert_status = await get_alert_status(guild_id)
    if alert_status == 1:
        alerts_channel_id = await get_alerts_channel_id(guild_id)
        guild = bot.get_guild(guild_id)
        if guild and alerts_channel_id:
            alerts_channel = guild.get_channel(alerts_channel_id)
            if alerts_channel:
                for player_id in all_player_ids:
                    current_player = current_players_dict.get(player_id)
                    previous_player = previous_players_dict.get(player_id)

                    # 🟢 Игрок вошёл на сервер
                    if current_player and (not previous_player or previous_player["status"] == "offline") and current_player["status"] == "online":
                        embed = discord.Embed(
                            title="🟢 Игрок зашёл на сервер",
                            color=discord.Color.green()
                        )
                        embed.set_author(name=bot.user.name, icon_url=bot.user.avatar.url)  # 📌 Аватар бота
                        embed.add_field(name="🎮 Игрок", value=f"**{current_player['name']}**", inline=True)
                        embed.add_field(name="🆔 ID", value=f"`{current_player['id']}`", inline=True)
                        embed.add_field(name="🌐 Сервер", value=f"`{current_player['server']}`", inline=False)
                        embed.add_field(name="🕒 Последний вход", value=f"`{format_datetime(current_player['last_seen'])}`", inline=True)
                        embed.set_footer(text="🔔 Статус: Онлайн ✅")
                        await alerts_channel.send(embed=embed)

                    # 🔴 Игрок покинул сервер
                    elif previous_player and previous_player["status"] == "online" and (not current_player or current_player["status"] == "offline"):
                        embed = discord.Embed(
                            title="🔴 Игрок покинул сервер",
                            color=discord.Color.red()
                        )
                        embed.set_author(name=bot.user.name, icon_url=bot.user.avatar.url)  # 📌 Аватар бота
                        embed.add_field(name="🎮 Игрок", value=f"**{previous_player['name']}**", inline=True)
                        embed.add_field(name="🆔 ID", value=f"`{previous_player['id']}`", inline=True)
                        embed.add_field(name="🌐 Последний сервер", value=f"`{previous_player['server']}`", inline=False)
                        embed.add_field(name="🕒 Последний вход", value=f"`{format_datetime(previous_player['last_seen'])}`", inline=True)
                        embed.set_footer(text="🔔 Статус: Оффлайн ❌")
                        await alerts_channel.send(embed=embed)

    online_players_cache[guild_id] = current_online_players