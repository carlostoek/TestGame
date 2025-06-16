from aiogram import Router
from aiogram.filters import Command, BaseFilter
from aiogram.types import Message

from datetime import datetime, timedelta

from bot.config import settings
from bot.database import (
    assign_mission,
    award_achievement,
    add_reward,
    get_monthly_purchase_summary,
)

router = Router()

class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user and message.from_user.id in settings.admin_ids

@router.message(Command("admin"), AdminFilter())
async def admin_panel(message: Message) -> None:
    await message.answer("Panel de administraci\u00f3n activo")


@router.message(Command("createmission"), AdminFilter())
async def create_mission(message: Message) -> None:
    """Create a custom mission for a user."""
    try:
        data = message.text.split(maxsplit=1)[1]
        user_id_str, desc, points_str, days_str = [part.strip() for part in data.split("|")]
        user_id = int(user_id_str)
        points = int(points_str)
        days = int(days_str)
    except Exception:
        await message.answer("Uso: /createmission user_id|descripcion|puntos|dias")
        return
    assign_mission(user_id, desc, points, days_valid=days)
    await message.answer("Misi\u00f3n creada")


@router.message(Command("award"), AdminFilter())
async def award_command(message: Message) -> None:
    """Award an achievement to a user."""
    try:
        data = message.text.split(maxsplit=1)[1]
        user_str, name, desc = [part.strip() for part in data.split("|", 2)]
        user_id = int(user_str)
    except Exception:
        await message.answer("Uso: /award user_id|nombre|descripcion")
        return
    award_achievement(user_id, name, desc)
    await message.answer("Logro otorgado")


@router.message(Command("addreward"), AdminFilter())
async def add_reward_command(message: Message) -> None:
    """Add a new reward to the store."""
    try:
        data = message.text.split(maxsplit=1)[1]
        name, desc, cost_str = [part.strip() for part in data.split("|", 2)]
        cost = int(cost_str)
    except Exception:
        await message.answer("Uso: /addreward nombre|descripcion|costo")
        return
    add_reward(name, desc, cost)
    await message.answer("Recompensa agregada")


@router.message(Command("monthsummary"), AdminFilter())
async def monthly_purchases_command(message: Message) -> None:
    """Show purchase summary for a given month."""
    parts = message.text.split(maxsplit=1)
    if len(parts) > 1:
        try:
            month = datetime.strptime(parts[1], "%Y-%m").date().replace(day=1)
        except ValueError:
            await message.answer("Uso: /monthsummary [YYYY-MM]")
            return
    else:
        first_day_current = datetime.utcnow().date().replace(day=1)
        month = (first_day_current - timedelta(days=1)).replace(day=1)

    summary = get_monthly_purchase_summary(month)
    if not summary:
        await message.answer("Sin compras registradas")
        return

    lines = [f"{reward.name if reward else rid}: {count}" for reward, count in summary]
    await message.answer(f"Resumen de compras {month:%Y-%m}:\n" + "\n".join(lines))
