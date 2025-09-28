from aiogram import Bot
from aiogram import Dispatcher
from aiogram.types import Message, ContentType, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command, CommandStart, StateFilter
import asyncio
from aiogram import F
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
import aiosqlite
import copy
from aiogram.enums import ChatType
import re

role_student = "Ученик"
role_teacher = "Преподаватель"


class FSMFillForm(StatesGroup):
    name = State()
    surname = State()
    role = State()
    clas = State()
    text = State()
    report = State()
    name_smw = State()
    message = State()


async def check_user_in_data(tg_id):
    async with aiosqlite.connect("users.db") as db:
        cursor = await db.execute("SELECT role FROM users WHERE tg_id=?", (tg_id,))
        data = await cursor.fetchone()
        if data is not None:
            return True
        else:
            return False

async def count_check(tg_id):
    async with (aiosqlite.connect("users.db") as db):
        cursor = await db.execute("SELECT study, sport FROM users WHERE tg_id=?", (tg_id,))
        data = await cursor.fetchone()
        if data is None:
            return 0
        else:
            digit_list = [0 if x is None else int(x) for x in data]
            count = sum(digit_list)
            return max(0, min(2, count))

async def create_database():
    async with aiosqlite.connect('users.db') as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (tg_id BIGINT, username TEXT, name TEXT, surname TEXT, role TEXT, clas TEXT, study BOOLEAN, sport BOOLEAN)")
        await db.commit()


async def add_to_database(tg_id, username, name, surname, role, clas):
    async with aiosqlite.connect('users.db') as db:
        cursor = await db.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
        data = await cursor.fetchone()
        if data is not None:
            return
        await db.execute("INSERT INTO users (tg_id, username, name, surname, role, clas) VALUES (?, ?, ?, ?, ?, ?)", (tg_id, username, name, surname, role, clas))
        await db.commit()
