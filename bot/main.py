import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

from typing import Optional

from .config import settings
from .database import (
    get_or_create_user,
    reset_missions,
    assign_mission,
    get_active_missions,
    complete_mission,
    update_mission_progress,
    calculate_reward,
    remove_expired_missions,
    get_missions_near_expiry,
    mark_warning_sent,
)

bot = Bot(token=settings.bot_token)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_handler(message: Message):
    user = get_or_create_user(message.from_user.id)
    if not get_active_missions(user.id):
        assign_mission(
            user.id,
            "Env\u00eda un mensaje en el canal",
            2,
            days_valid=1,
            mission_type="message",
            goal=5,
        )
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
    await message.answer(
        f"Usuario {target_id}: nivel {user.level}, puntos {user.points}"
    )


@dp.message(Command("reset"))
async def reset_user(message: Message):
    try:
        target_id = int(message.text.split(maxsplit=1)[1])
    except (IndexError, ValueError):
        await message.answer("Uso: /reset <id>")
        return
    reset_missions(target_id)
    await message.answer(f"Misiones de {target_id} reiniciadas")


@dp.message(Command("missions"))
async def missions_list(message: Message):
    user = get_or_create_user(message.from_user.id)
    missions = get_active_missions(user.id)
    if not missions:
        await message.answer("No tienes misiones activas")
        return
    text_lines = [
        f"ID {m.id}: {m.description} [{m.progress}/{m.goal}] (+{calculate_reward(m)} puntos)"
        for m in missions
    ]
    await message.answer(
        "\n".join(text_lines) + f"\nPuntos: {user.points} Nivel: {user.level}"
    )


@dp.message(Command("progress"))
async def progress_command(message: Message):
    try:
        mission_id = int(message.text.split(maxsplit=2)[1])
    except (IndexError, ValueError):
        await message.answer("Uso: /progress <id_mision>")
        return
    mission = update_mission_progress(message.from_user.id, mission_id)
    if not mission:
        await message.answer("Misi\u00f3n no v\u00e1lida")
        return
    if mission.progress >= mission.goal:
        reward = calculate_reward(mission)
        await message.answer(f"Misi\u00f3n completada! Ganaste {reward} puntos")
    else:
        await message.answer(f"Progreso actualizado: {mission.progress}/{mission.goal}")


@dp.message(Command("complete"))
async def complete_command(message: Message):
    try:
        mission_id = int(message.text.split(maxsplit=1)[1])
    except (IndexError, ValueError):
        await message.answer("Uso: /complete <id_mision>")
        return
    mission = complete_mission(message.from_user.id, mission_id)
    if not mission:
        await message.answer("Misi\u00f3n no v\u00e1lida")
        return
    reward = calculate_reward(mission)
    await message.answer(f"Misi\u00f3n completada! Ganaste {reward} puntos")


async def scheduler():
    """Background task to clean expired missions and warn users."""
    while True:
        remove_expired_missions()
        missions = get_missions_near_expiry(24)
        for m in missions:
            await bot.send_message(
                m.user_id,
                f"La misi\u00f3n '{m.description}' expirar\u00e1 pronto",
            )
            mark_warning_sent(m.id)
        await asyncio.sleep(3600)


async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
