from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


START_HERE_BUTTON = "🚀 Начни здесь"

CATEGORIES_BUTTON = "📋 Категории"
ADD_SUBCATEGORIES_BUTTON = "➕ Добавить подкатегории"
SHEET_BUTTON = "📊 Таблица"
HELP_BUTTON = "❓ Помощь"

BACK_TO_MENU_BUTTON = "↩️ Назад в меню"


def get_start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=START_HERE_BUTTON),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Нажмите «Начни здесь»",
    )


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=CATEGORIES_BUTTON),
                KeyboardButton(text=ADD_SUBCATEGORIES_BUTTON),
            ],
            [
                KeyboardButton(text=SHEET_BUTTON),
                KeyboardButton(text=HELP_BUTTON),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Напишите расход или выберите действие",
    )


def get_scenario_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BACK_TO_MENU_BUTTON),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Введите данные или вернитесь в меню",
    )