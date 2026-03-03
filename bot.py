import os
import logging
import zipfile
import shutil
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import FSInputFile
from aiohttp import web

# --- НАСТРОЙКИ И ЛОГИ ---
logging.basicConfig(level=logging.INFO)
# Токен берется из настроек Render (Environment Variables)
API_TOKEN = os.getenv("BOT_TOKEN")
BASE_APK = "base.apk"  # Файл движка Hambrenik

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (Костыль против "засыпания") ---
async def handle(request):
    return web.Response(text="Hambrenik Engine: UnderGames Packer is Running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    # Render дает порт в переменную окружения PORT
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"Веб-сервер запущен на порту {port}")

# --- ЛОГИКА СБОРКИ APK ---
def build_apk(love_file_path, output_apk_path):
    if not os.path.exists(BASE_APK):
        raise FileNotFoundError(f"Критическая ошибка: {BASE_APK} не найден!")
    
    # Копируем чистую базу движка
    shutil.copy(BASE_APK, output_apk_path)
    
    # Вшиваем проект .love внутрь архива APK
    with zipfile.ZipFile(output_apk_path, 'a') as apk:
        # Путь assets/game.love стандартный для Love2D/Humber
        apk.write(love_file_path, 'assets/game.love')

# --- ОБРАБОТКА ФАЙЛОВ ---
@dp.message(F.document)
async def handle_docs(message: types.Message):
    file_name = message.document.file_name
    
    if not file_name.endswith('.love'):
        await message.answer("⚠️ Бро, это не .love файл. Пришли проект игры!")
        return

    status_msg = await message.answer("🛠 Начинаю сборку APK на движке Hambrenik...")

    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    
    input_love = f"temp_{message.from_user.id}.love"
    output_apk = f"Humber_{file_name.replace('.love', '.apk')}"

    try:
        # Скачиваем файл пользователя
        await bot.download_file(file.file_path, input_love)

        # Собираем APK (запускаем в отдельном потоке, чтобы не вешать бота)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, build_apk, input_love, output_apk)

        # Отправляем результат
        result_file = FSInputFile(output_apk)
        await bot.send_document(message.chat.id, result_file, caption="✅ Готово! Твой APK на движке Hambrenik.")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка сборки: {e}")
        logging.error(f"Error: {e}")
    finally:
        # Удаляем временный мусор
        if os.path.exists(input_love): os.remove(input_love)
        if os.path.exists(output_apk): os.remove(output_apk)
        await status_msg.delete()

@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот UnderGames. Пришли мне .love файл, и я упакую его в APK.")

# --- ЗАПУСК ---
async def main():
    if not API_TOKEN:
        logging.error("BOT_TOKEN не найден! Проверь Environment Variables в Render.")
        return

    # Запускаем веб-сервер и бота одновременно
    await start_web_server()
    logging.info("Бот запущен и готов к работе...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")
