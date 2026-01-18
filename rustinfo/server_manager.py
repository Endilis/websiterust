from plus import connect_to_servers, register_commands
import asyncio

async def start_rust_server(server_list: list[dict]):
    if not server_list:
        print("❌ Список серверов пуст, не подключаем.")
        return

    print(f"🚀 Запуск подключения для {len(server_list)} серверов...")

    await connect_to_servers(server_list)

    # Задержка, чтобы сервер успел активировать pairing-токен
    await asyncio.sleep(3)

    await register_commands(server_list)

    print("✅ Подключение и регистрация завершены.")
