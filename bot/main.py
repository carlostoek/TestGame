import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

from .config import settings
from .database import get_or_create_user, reset_missions

bot = Bot(token=settings.bot_token)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: Message):
    user = get_or_create_user(message.from_user.id)
    await message.answer(f"Bienvenido al bot! Nivel actual: {user.level}")

@dp.message(Command("user"))
async def user_status(message: Message):
    if not message.from_user.id:
        return
    try:
        target_id = int(message.text.split(maxsplit=1)[1])
    except (IndexError, ValueError):
        await message.answer("Uso: /user <id>")
        return
    user = get_or_create_user(target_id)
    await message.answer(f"Usuario {target_id}: nivel {user.level}, puntos {user.points}")

@dp.message(Command("reset"))
async def reset_user(message: Message):
    try:
        target_id = int(message.text.split(maxsplit=1)[1])
    except (IndexError, ValueError):
        await message.answer("Uso: /reset <id>")
        return
    reset_missions(target_id)
    await message.answer(f"Misiones de {target_id} reiniciadas")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
