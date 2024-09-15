from aiogram import Bot, types

from db import Database
from keyboards import *
from i18n import i18n
from uuid import uuid4


class Utils:
    def __init__(self, bot: Bot, db: Database) -> None:
        self.db = db
        self.bot = bot
        self.photo_key = str(uuid4())

    def banner(self, key: str) -> str:
        return f"https://raw.githubusercontent.com/qweme32/haovpn-style/main/{key}.png?anti_cache_key=${self.photo_key}"

    async def change_lang(self, event: types.Message | types.CallbackQuery):
        user_id = event.from_user.id
        await self.db.get_or_create_user(user_id)

        await self.bot.send_photo(
            user_id,
            types.FSInputFile("images/hello.png"),
            reply_markup=change_lang_keyboard(),
        )

        if isinstance(event, types.Message):
            await event.delete()
        else:
            await event.message.delete()

    async def select_plan(self, query: types.CallbackQuery):
        user_id = query.from_user.id
        user = await self.db.get_or_create_user(user_id)

        await self.bot.send_photo(
            user_id,
            types.FSInputFile("images/subscription.png"),
            reply_markup=plan_keyboard(user),
        )

        await query.message.delete()

    async def select_server(self, query: types.CallbackQuery):
        user_id = query.from_user.id
        user = await self.db.get_or_create_user(user_id)
        servers = await self.db.server_list()

        await self.bot.send_photo(
            user_id,
            types.FSInputFile("images/location.png"),
            reply_markup=server_keyboard(user, servers),
        )

        await query.message.delete()

    async def set_server(self, query: types.CallbackQuery):
        user_id = query.from_user.id
        user = await self.db.get_or_create_user(user_id)
        _, server = query.data.split(":")

        await self.db.set_server(user, server)
        await self.menu(query)

    async def connect_menu(self, query: types.CallbackQuery):
        user_id = query.from_user.id
        user = await self.db.get_or_create_user(user_id)

        await self.bot.send_photo(
            user_id,
            types.FSInputFile("images/connect.png"),
            caption=i18n("connect_menu", user["lang"], token=user["token"]),
            reply_markup=back_keyboard(user),
        )

        await query.message.delete()

    async def send_invoice_for_buy(self, query: types.CallbackQuery):
        user_id = query.from_user.id
        user = await self.db.get_or_create_user(user_id)

        period = int(query.data.split(":")[1])

        price = 1000

        if period == 1:
            price = 5  # 5
        elif period == 30:
            price = 75  # 100
        elif period == 90:
            price = 200
        elif period == 360:
            price = 500

        prices = [types.LabeledPrice(label="XTR", amount=price)]

        await self.bot.send_invoice(
            chat_id=user_id,
            title="Kuai VPN Subscription",
            description=i18n(f"desc_{period}_day", user["lang"]),
            prices=prices,
            provider_token="",
            payload=f"payment_sub_{period}",
            currency="XTR",
            reply_markup=pay_keyboard(user),
        )

    async def menu(self, query: types.CallbackQuery):
        user_id = query.from_user.id
        user = await self.db.get_or_create_user(user_id)
        tkey = "onboarding" if datetime.now() > user["dates"]["sub_until"] else "menu"

        await self.bot.send_photo(
            user_id,
            types.FSInputFile("images/menu.png"),
            caption=i18n(
                tkey,
                user["lang"],
                until=user["dates"]["sub_until"].isoformat().split("T")[0],
                server=i18n(str(user["server"]), user["lang"]),
            ),
            reply_markup=menu_keyboard(user),
        )

        try:
            await query.message.delete()
        except:
            pass
