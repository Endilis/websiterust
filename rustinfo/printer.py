from datetime import datetime
from colorama import Fore, Style
import threading
import requests
import re
from config import LOG_WEBHOOK_URL
from database import get_guild_name

DISCORD_COLOR = "\033[38;2;88;101;242m"
RESET_COLOR = "\033[0m"


def _strip_ansi(s: str) -> str:
    return re.sub(r"\x1B\[[0-9;;]*[A-Za-z]", "", s)


def _post_webhook(url: str, content: str) -> None:
    try:
        requests.post(url, json={"content": content}, timeout=5)
    except Exception:
        # Не поднимаем исключения из логера
        pass


def _send_to_webhook_async(message: str) -> None:
    if not LOG_WEBHOOK_URL:
        return
    t = threading.Thread(target=_post_webhook, args=(LOG_WEBHOOK_URL, message), daemon=True)
    t.start()


async def log_command(name: str, command: str, socket, guild_id, steam_id=None):
    now = datetime.now().strftime("%H:%M:%S")
    time_colored = f"{Fore.LIGHTBLACK_EX}[{now}]{Style.RESET_ALL}"
    
    # Получаем название гильдии
    guild_name = await get_guild_name(guild_id) or f"ID {guild_id}"
    
    name_colored = f"{Fore.RED}{name}{Style.RESET_ALL}"
    command_colored = f"{Fore.RED}<{command}>{Style.RESET_ALL}"
    guild_id_colored = f"{DISCORD_COLOR}<{guild_name} ({guild_id})>{RESET_COLOR}"
    steam_id_str = f" SteamID: {steam_id}" if steam_id else ""

    if socket and hasattr(socket, "server_details"):
        ip = getattr(socket.server_details, "ip", "None")
        port = getattr(socket.server_details, "port", "None")
    else:
        ip = "None"
        port = "None"

    formatted = f"{time_colored} [Rust+] {name_colored} - [{guild_id_colored}]{steam_id_str} использовал {command_colored} на сервере: {ip}:{port}"
    print(formatted)

    # plain для Discord — без цветовых кодов
    steam_profile = f" https://steamcommunity.com/profiles/{steam_id}/" if steam_id else ""
    plain = _strip_ansi(f"[{now}] [Rust+] [{guild_name} ({guild_id})] {name}{steam_profile} использовал <{command}> на сервере: {ip}:{port}")
    _send_to_webhook_async(plain)
