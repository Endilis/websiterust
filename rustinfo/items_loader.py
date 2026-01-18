import json
from pathlib import Path

ITEMS: dict[str, str] = {}

def load_items(path: str | Path = "items.json") -> None:
    global ITEMS
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # нормализуем ключи в строки
    ITEMS = {str(k): v for k, v in data.items()}

def get_item_name(item_id: int | str) -> str:
    return ITEMS.get(str(item_id), f"ID {item_id}")