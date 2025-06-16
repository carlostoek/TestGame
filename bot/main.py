import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message

from typing import Optional
from datetime import datetime, timedelta

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
    assign_daily_missions,
    assign_weekly_missions,
    get_top_users,
    award_achievement,
    get_user_achievements,
    get_rewards,
    redeem_reward,
    add_reward,
    get_weekly_mission,
    record_user_message,
    get_weekly_activity,
    get_user_weekly_stat,
    reward_top_weekly_users,
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


@dp.message(Command("weekly"))
async def weekly_mission(message: Message):
    """Show the current weekly mission for the user."""
    user_id = message.from_user.id
    mission = get_weekly_mission(user_id)
    if not mission:
        await message.answer("No tienes un reto semanal asignado actualmente")
        return
    reward = calculate_reward(mission)
    await message.answer(
        f"Reto semanal: {mission.description}\n"
        f"Progreso: {mission.progress}/{mission.goal} (+{reward} pts)"
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


@dp.message(Command("createmission"))
async def create_mission(message: Message):
    """Allow admins to create custom missions for a user."""
    if message.from_user.id not in settings.admin_ids:
        await message.answer("No autorizado")
        return
    try:
        data = message.text.split(maxsplit=1)[1]
        user_id_str, desc, points_str, days_str = [
            part.strip() for part in data.split("|")
        ]
        user_id = int(user_id_str)
        points = int(points_str)
        days = int(days_str)
    except Exception:
        await message.answer("Uso: /createmission user_id|descripcion|puntos|dias")
        return
    assign_mission(user_id, desc, points, days_valid=days)
    await message.answer("Misi\u00f3n creada")


@dp.message(Command("ranking"))
async def ranking_command(message: Message):
    """Show top users by points."""
    users = get_top_users(10)
    if not users:
        await message.answer("No hay usuarios registrados")
        return
    lines = [f"{idx + 1}. {u.id} - {u.points} pts" for idx, u in enumerate(users)]
    await message.answer("Ranking:\n" + "\n".join(lines))


@dp.message(Command("award"))
async def award_command(message: Message):
    """Allow admins to award an achievement to a user."""
    if message.from_user.id not in settings.admin_ids:
        await message.answer("No autorizado")
        return
    try:
        data = message.text.split(maxsplit=1)[1]
        user_str, name, desc = [part.strip() for part in data.split("|", 2)]
        user_id = int(user_str)
    except Exception:
        await message.answer("Uso: /award user_id|nombre|descripcion")
        return
    award_achievement(user_id, name, desc)
    await message.answer("Logro otorgado")


@dp.message(Command("achievements"))
async def achievements_command(message: Message):
    """Show the achievements of a user."""
    user_id = message.from_user.id
    achievements = get_user_achievements(user_id)
    if not achievements:
        await message.answer("A\u00fan no tienes logros")
        return
    lines = [f"{a.name}: {a.description}" for a in achievements]
    await message.answer("Tus logros:\n" + "\n".join(lines))


@dp.message(Command("weeklystats"))
async def weekly_stats_command(message: Message):
    """Show weekly activity statistics."""
    user_id = message.from_user.id
    stat = get_user_weekly_stat(user_id)
    count = stat.message_count if stat else 0
    top = get_weekly_activity(5)
    lines = [f"{idx+1}. {s.user_id} - {s.message_count}" for idx, s in enumerate(top)]
    text = f"Mensajes esta semana: {count}"
    if lines:
        text += "\nTop actividad:\n" + "\n".join(lines)
    await message.answer(text)


@dp.message(Command("store"))
async def store_command(message: Message):
    """List available rewards."""
    rewards = get_rewards()
    if not rewards:
        await message.answer("La tienda est\u00e1 vac\u00eda")
        return
    lines = [f"{r.id}. {r.name} - {r.cost} pts" for r in rewards]
    await message.answer("Tienda:\n" + "\n".join(lines))


@dp.message(Command("buy"))
async def buy_command(message: Message):
    """Redeem a reward using points."""
    try:
        reward_id = int(message.text.split(maxsplit=1)[1])
    except (IndexError, ValueError):
        await message.answer("Uso: /buy <id_recompensa>")
        return
    success = redeem_reward(message.from_user.id, reward_id)
    if success:
        await message.answer("Recompensa canjeada con \u00e9xito")
    else:
        await message.answer("No tienes suficientes puntos o recompensa inv\u00e1lida")


@dp.message(~Command())
async def track_messages(message: Message):
    """Track user activity on every message."""
    if message.from_user and message.chat.type in {"private", "group", "supergroup"}:
        record_user_message(message.from_user.id)


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


async def daily_mission_scheduler():
    """Assign daily missions to all users once per day."""
    last_day = datetime.utcnow().date()
    while True:
        current_day = datetime.utcnow().date()
        if current_day != last_day:
            assign_daily_missions(
                "Misi\u00f3n diaria: env\u00eda 3 mensajes",
                points=5,
                goal=3,
            )
            last_day = current_day
        await asyncio.sleep(3600)


async def weekly_mission_scheduler():
    """Assign weekly missions to all users once per week."""
    last_week = datetime.utcnow().date() - timedelta(days=datetime.utcnow().weekday())
    while True:
        current_week = datetime.utcnow().date() - timedelta(days=datetime.utcnow().weekday())
        if current_week != last_week:
            assign_weekly_missions(
                "Reto semanal: participa con 10 mensajes",
                points=20,
                goal=10,
            )
            last_week = current_week
        await asyncio.sleep(3600)


async def weekly_summary_scheduler():
    """Send weekly activity summary to the configured channel."""
    last_week = datetime.utcnow().date() - timedelta(days=datetime.utcnow().weekday())
    while True:
        current_week = datetime.utcnow().date() - timedelta(days=datetime.utcnow().weekday())
        if current_week != last_week:
            if settings.notify_channel_id:
                stats = get_weekly_activity(5, week=last_week)
                lines = [f"{idx+1}. {s.user_id} - {s.message_count}" for idx, s in enumerate(stats)]
                text = "Resumen de actividad semanal:\n" + ("\n".join(lines) if lines else "Sin actividad")
                await bot.send_message(settings.notify_channel_id, text)
            bonus = 10
            rewarded = reward_top_weekly_users(last_week, points=bonus)
            for user in rewarded:
                await bot.send_message(
                    user.id,
                    f"\u00a1Felicidades! Fuiste de los m\u00e1s activos y ganas {bonus} puntos extra",
                )
            last_week = current_week
        await asyncio.sleep(3600)


async def main():
    asyncio.create_task(scheduler())
    asyncio.create_task(daily_mission_scheduler())
    asyncio.create_task(weekly_mission_scheduler())
    asyncio.create_task(weekly_summary_scheduler())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
