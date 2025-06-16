from aiogram import Router, F
from aiogram.filters import Command, BaseFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.config import settings
from bot.database import (
    get_or_create_user,
    get_active_missions,
    calculate_reward,
    get_user_achievements,
)


router = Router()


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user and message.from_user.id in settings.admin_ids


# -- User Menu --
@router.message(Command("menu"))
async def user_menu(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Misiones", callback_data="user_missions")],
            [InlineKeyboardButton(text="Progreso", callback_data="user_progress")],
            [InlineKeyboardButton(text="Insignias", callback_data="user_badges")],
            [InlineKeyboardButton(text="Perfil", callback_data="user_profile")],
        ]
    )
    await message.answer("\u00bfQu\u00e9 deseas consultar?", reply_markup=keyboard)


@router.callback_query(F.data == "user_missions")
async def cb_user_missions(query: CallbackQuery) -> None:
    user = get_or_create_user(query.from_user.id)
    missions = get_active_missions(user.id)
    if not missions:
        await query.message.edit_text("No tienes misiones activas")
        return
    lines = [
        f"ID {m.id}: {m.description} [{m.progress}/{m.goal}] (+{calculate_reward(m)} pts)"
        for m in missions
    ]
    await query.message.edit_text("Tus misiones:\n" + "\n".join(lines))


@router.callback_query(F.data == "user_progress")
async def cb_user_progress(query: CallbackQuery) -> None:
    user = get_or_create_user(query.from_user.id)
    text = f"Nivel: {user.level}\nPuntos: {user.points}"
    await query.message.edit_text(text)


@router.callback_query(F.data == "user_badges")
async def cb_user_badges(query: CallbackQuery) -> None:
    badges = get_user_achievements(query.from_user.id)
    if not badges:
        await query.message.edit_text("A\u00fan no tienes insignias")
        return
    lines = [f"{b.name}: {b.description}" for b in badges]
    await query.message.edit_text("Tus insignias:\n" + "\n".join(lines))


@router.callback_query(F.data == "user_profile")
async def cb_user_profile(query: CallbackQuery) -> None:
    user = get_or_create_user(query.from_user.id)
    badges = get_user_achievements(query.from_user.id)
    text = (
        f"ID: {user.id}\nNivel: {user.level}\nPuntos: {user.points}\n"
        f"Insignias: {len(badges)}"
    )
    await query.message.edit_text(text)


# -- Admin Menu --
@router.message(Command("adminmenu"), AdminFilter())
async def admin_menu(message: Message) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Usuarios", callback_data="admin_users")],
            [InlineKeyboardButton(text="Misiones", callback_data="admin_missions")],
            [InlineKeyboardButton(text="Recompensas", callback_data="admin_rewards")],
            [InlineKeyboardButton(text="Budgets", callback_data="admin_budgets")],
            [InlineKeyboardButton(text="Estad\u00edsticas", callback_data="admin_stats")],
        ]
    )
    await message.answer("Men\u00fa de administraci\u00f3n", reply_markup=keyboard)


@router.callback_query(F.data == "admin_users")
async def cb_admin_users(query: CallbackQuery) -> None:
    await query.message.edit_text("Gest\u00f3n de usuarios (pendiente de implementar)")


@router.callback_query(F.data == "admin_missions")
async def cb_admin_missions(query: CallbackQuery) -> None:
    await query.message.edit_text("Gest\u00f3n de misiones (pendiente de implementar)")


@router.callback_query(F.data == "admin_rewards")
async def cb_admin_rewards(query: CallbackQuery) -> None:
    await query.message.edit_text("Gest\u00f3n de recompensas (pendiente de implementar)")


@router.callback_query(F.data == "admin_budgets")
async def cb_admin_budgets(query: CallbackQuery) -> None:
    await query.message.edit_text("Budgets (pendiente de implementar)")


@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(query: CallbackQuery) -> None:
    await query.message.edit_text("Estad\u00edsticas (pendiente de implementar)")
