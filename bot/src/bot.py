import asyncio
from datetime import timedelta

from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram import Bot, Dispatcher, html, types, F
from aiogram.client.default import DefaultBotProperties

from db.db import Database
from utils.utils import Utils
from config.settings import config


dp = Dispatcher()
bot = Bot(
    token=config.tg_token.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
db = Database()
utils = Utils(bot, db)
admins = list(map(lambda x: int(x), config.admin_users.get_secret_value().split(",")))


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    print(message)
    await utils.change_lang(message)


@dp.message(Command("promo"))
async def promo_handler(message: types.Message):
    user_id = message.from_user.id
    user = await db.get_or_create_user(user_id)

    if " " not in message.text or len(message.text.split(" ")) != 2:
        return await message.answer("Usage: /promo $code")

    _, code = message.text.split(" ")

    days = await db.activate_promo(user, code)

    if days == 0:
        return await message.answer("Invalid promocode.")
    else:
        await message.answer(f"Promo for {days} days activated.")
        await utils.menu(message)


@dp.message(Command("genpromo"))
async def genpromo_handler(message: types.Message) -> None:
    if message.from_user.id not in admins:
        return await message.answer("Admin role required.")

    if " " not in message.text or len(message.text.split(" ")) != 3:
        return await message.answer(
            "Usage: /genpromo $days[min: 1, max: 99999] $count[min: 1, max: 25]\n\nExample: /genpromo 7 25 ( 25 promo for 7 days )"
        )

    try:
        _, days, count = message.text.split(" ")
        days = int(days)
        count = int(count)

        if 0 >= days or days > 99999:
            return await message.answer(
                "Invalid value in argument $days must be 1-99999"
            )
        if 0 >= count or count > 25:
            return await message.answer("Invalid value in argument $count must be 1-25")
    except:
        return await message.answer(
            "Invalid type in argument $days or $count must be numbers"
        )

    promos = list(map(lambda x: x["id"], await db.gen_promos(days, count)))

    text = f"""Count: {count}
Days: {days}

<code>{'''
'''.join(promos)}</code>"""

    await message.answer(text)


@dp.callback_query()
async def callback_handler(query: types.CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    user = await db.get_or_create_user(user_id)

    if data.startswith("lang:"):
        await db.set_lang(user, data.split(":")[1])
        await utils.menu(query)

    elif data == "back":
        await utils.menu(query)

    elif data == "change_lang":
        await utils.change_lang(query)

    elif data == "select_plan":
        await utils.select_plan(query)

    elif data == "change_location":
        await utils.select_server(query)

    elif data.startswith("server:"):
        await utils.set_server(query)

    elif data == "connect":
        await utils.connect_menu(query)

    elif data.startswith("buy:"):
        await utils.send_invoice_for_buy(query)


@dp.pre_checkout_query()
async def pre_checkout_query(query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(query.id, ok=True)


@dp.message(F.successful_payment)
async def payment_handler(message: types.Message):
    user_id = message.from_user.id
    user = await db.get_or_create_user(user_id)
    payload = message.successful_payment.invoice_payload

    if "payment_sub_" in payload:
        period = int(payload.replace("payment_sub_", ""))

        print("Yeee")
        await db.give_sub_to_user(user, timedelta(days=period))

        await utils.menu(message)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
