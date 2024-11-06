from datetime import datetime
from typing import List

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from db.db import User, Server
from locales.strings import i18n


def change_lang_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🇷🇺 Продолжить на Русском", callback_data="lang:ru")
    )

    builder.row(
        InlineKeyboardButton(text="🇪🇺 Continue in English", callback_data="lang:en")
    )

    builder.row(InlineKeyboardButton(text="🇨🇳 继续使用中文", callback_data="lang:cn"))

    return builder.as_markup()


def pay_keyboard(user: User) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text=i18n("pay", user["lang"]), pay=True))

    return builder.as_markup()


def chunkify(my_list, n):
    return [my_list[i * n : (i + 1) * n] for i in range((len(my_list) + n - 1) // n)]


def server_keyboard(user: User, servers: List[Server]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    servers = list(map(lambda x: x["id"], servers))
    # servers.remove("n-hongkong")

    builder.row(
        InlineKeyboardButton(
            text=i18n("n-best", user["lang"]), callback_data=f"server:n-best"
        )
    )

    for server_chunk in chunkify(servers, 2):
        buttons = []

        buttons.append(
            InlineKeyboardButton(
                text=i18n(server_chunk[0], user["lang"]),
                callback_data=f"server:{server_chunk[0]}",
            )
        )

        if len(server_chunk) == 2:
            buttons.append(
                InlineKeyboardButton(
                    text=i18n(server_chunk[1], user["lang"]),
                    callback_data=f"server:{server_chunk[1]}",
                )
            )

        builder.row(*buttons)

    builder.row(
        InlineKeyboardButton(text=i18n("back", user["lang"]), callback_data=f"back")
    )

    return builder.as_markup()


def back_keyboard(user: User) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text=i18n("back", user["lang"]), callback_data=f"back")
    )

    return builder.as_markup()


def plan_keyboard(user: User) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=i18n("buy_1_day", user["lang"]), callback_data="buy:1"
        ),
        InlineKeyboardButton(
            text=i18n("buy_30_day", user["lang"]), callback_data="buy:30"
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=i18n("buy_90_day", user["lang"]), callback_data="buy:90"
        ),
        InlineKeyboardButton(
            text=i18n("buy_360_day", user["lang"]), callback_data="buy:360"
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text=i18n("fragment", user["lang"]),
            url="https://fragment.com/stars",
        )
    )

    builder.row(
        InlineKeyboardButton(text=i18n("back", user["lang"]), callback_data="back")
    )

    return builder.as_markup()


def menu_keyboard(user: User) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if datetime.now() > user["dates"]["sub_until"]:
        builder.row(
            InlineKeyboardButton(
                text=i18n("buy", user["lang"]), callback_data="select_plan"
            )
        )

        builder.row(
            InlineKeyboardButton(
                text=i18n("lang", user["lang"]), callback_data="change_lang"
            )
        )

    else:
        builder.row(
            InlineKeyboardButton(
                text=i18n("connect", user["lang"]), callback_data="connect"
            )
        )

        builder.row(
            InlineKeyboardButton(
                text=i18n("location", user["lang"]), callback_data="change_location"
            )
        )

        builder.row(
            InlineKeyboardButton(
                text=i18n("lang", user["lang"]), callback_data="change_lang"
            )
        )

    return builder.as_markup()
