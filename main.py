import asyncio
import logging
from aiogram import Bot, Dispatcher
from handlers import router
from database import init_db

# Loglarni ko'rib turish uchun (xatolarni chiqaradi)
logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Bazani har safar tekshirib olish
    init_db()
    
    # 2. Bot tokenini shu yerga qo'yasan
    TOKEN = "8668974814:AAGa1NIw5FZ-74iJq94r1DfHzd0TDVNyOPk"
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # 3. Routerlarni ulash (Handlers bilan bog'laydi)
    dp.include_router(router)
    
    # 4. Botni ishga tushirish
    print("--- BOT ISHGA TUSHDI ---")
    print("Jigar, hamma tizimlar OK! Gazini ber!")
    
    # Eskidan qolib ketgan xabarlarni o'chirib yuborish (skip_updates)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi!")