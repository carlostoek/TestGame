from aiogram import Router
from aiogram.filters import Command, BaseFilter
from aiogram.types import Message

from bot.config import settings

router = Router()

class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user and message.from_user.id in settings.admin_ids

@router.message(Command("admin"), AdminFilter())
async def admin_panel(message: Message) -> None:
    await message.answer("Panel de administraci\u00f3n activo")
