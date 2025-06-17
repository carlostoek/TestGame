import sys, pathlib
ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import asyncio
from types import SimpleNamespace

import pytest

from bot.admin import (
    AdminFilter,
    create_mission,
    award_command,
    add_reward_command,
    monthly_purchases_command,
)
from bot import admin as admin_module


class FakeUser:
    def __init__(self, user_id):
        self.id = user_id


class FakeMessage:
    def __init__(self, text, user_id=1):
        self.text = text
        self.from_user = FakeUser(user_id)
        self.responses = []

    async def answer(self, text):
        self.responses.append(text)


def run(coro):
    return asyncio.run(coro)


def test_admin_filter():
    f = AdminFilter()
    msg = FakeMessage("/admin", user_id=42)
    admin_module.settings.admin_ids = [42]
    assert run(f(msg)) is True

    msg2 = FakeMessage("/admin", user_id=99)
    assert run(f(msg2)) is False


def test_create_mission_success(monkeypatch):
    recorded = {}

    def fake_assign(user_id, desc, points, days_valid):
        recorded['args'] = (user_id, desc, points, days_valid)

    monkeypatch.setattr(admin_module, 'assign_mission', fake_assign)

    msg = FakeMessage("/createmission 5|Do something|10|2")
    run(create_mission(msg))
    assert recorded['args'] == (5, 'Do something', 10, 2)
    assert msg.responses == ["Misi\u00f3n creada"]


def test_create_mission_invalid(monkeypatch):
    msg = FakeMessage("/createmission wrong format")
    run(create_mission(msg))
    assert msg.responses == ["Uso: /createmission user_id|descripcion|puntos|dias"]


def test_award_command(monkeypatch):
    called = {}

    def fake_award(user_id, name, desc):
        called['args'] = (user_id, name, desc)

    monkeypatch.setattr(admin_module, 'award_achievement', fake_award)

    msg = FakeMessage("/award 3|Hero|For bravery")
    run(award_command(msg))
    assert called['args'] == (3, 'Hero', 'For bravery')
    assert msg.responses == ["Logro otorgado"]


def test_add_reward_command(monkeypatch):
    called = {}

    def fake_add(name, desc, cost):
        called['args'] = (name, desc, cost)

    monkeypatch.setattr(admin_module, 'add_reward', fake_add)

    msg = FakeMessage("/addreward Sword|Sharp blade|50")
    run(add_reward_command(msg))
    assert called['args'] == ('Sword', 'Sharp blade', 50)
    assert msg.responses == ["Recompensa agregada"]


def test_monthly_purchases_command(monkeypatch):
    month = SimpleNamespace(name='Sword')

    def fake_summary(m):
        return [(month, 2)]

    monkeypatch.setattr(admin_module, 'get_monthly_purchase_summary', fake_summary)

    msg = FakeMessage("/monthsummary 2023-05")
    run(monthly_purchases_command(msg))
    assert msg.responses == ["Resumen de compras 2023-05:\nSword: 2"]


def test_monthly_purchases_invalid(monkeypatch):
    msg = FakeMessage("/monthsummary wrong")
    run(monthly_purchases_command(msg))
    assert msg.responses == ["Uso: /monthsummary [YYYY-MM]"]


def test_monthly_purchases_empty(monkeypatch):
    monkeypatch.setattr(admin_module, 'get_monthly_purchase_summary', lambda m: [])

    msg = FakeMessage("/monthsummary 2023-05")
    run(monthly_purchases_command(msg))
    assert msg.responses == ["Sin compras registradas"]
