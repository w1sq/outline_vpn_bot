from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import dotenv_values
from typing import TypedDict, List, Dict
from datetime import datetime, timedelta
from shortuuid import uuid
from uuid import uuid4


env = dotenv_values("../.env")


class UserDates(TypedDict):
    created_at: datetime
    sub_until: datetime

class User(TypedDict):
    id: int
    token: str
    dates: UserDates
    configs: Dict[str, str]
    server: str | None
    lang: str

class Server(TypedDict):
    id: str
    api: str
    fingerprint: str
    enabled: bool


class Promo(TypedDict):
    id: str
    days: int


class Database:
    def __init__(self) -> None:
        self.cli = AsyncIOMotorClient(env["MONGO_URI"])
        self.db = self.cli.get_database(env["DB_NAME"])
        self.users = self.db.get_collection("users")
        self.servers = self.db.get_collection("servers")
        self.promos = self.db.get_collection("promos")

    async def create_indexes(self):
        await self.users.create_index("id", unique=True)
        await self.users.create_index("token", unique=True)
        await self.servers.create_index("id", unique=True)
        await self.promos.create_index("id", unique=True)

    async def activate_promo(self, user: User, promo: str):
        promoDoc = await self.promos.find_one({"id": promo})

        if not promoDoc:
            return 0
        
        await self.promos.delete_one({"id": promo})

        await self.give_sub_to_user(user, timedelta(days=promoDoc["days"]))

        return promoDoc["days"]
    
    async def gen_promos(self, days: int, count: int) -> List[Promo]:
        promos = []
        for _ in range(count):
            promos.append({
                "id": str(uuid4()),
                "days": days
            })

        await self.promos.insert_many(promos)

        return promos

    async def server_list(self) -> List[Server]:
        l = []
        cursor = self.servers.find({ "enabled": True })

        async for server in cursor:
            l.append(server)

        return l
    
    async def set_server(self, user: User, id: str):
        await self.users.update_one(
            {
                "_id": user["_id"]
            },
            {
                "$set": {
                    "server": id
                }
            }
        )
    
    def user_have_sub(self, user: User) -> bool:
        return user["dates"]["sub_until"] > datetime.now()
    
    async def set_lang(self, user: User, lang: str):
        await self.users.update_one(
            {
                "_id": user["_id"]
            },
            {
                "$set": {
                    "lang": lang
                }
            }
        )

    async def give_sub_to_user(self, user: User, delta: timedelta):
        start_time = datetime.now()

        if user["dates"]["sub_until"] > start_time:
            start_time = user["dates"]["sub_until"]
        
        await self.users.update_one(
            {
                "_id": user["_id"]
            },
            {
                "$set": {
                    "dates.sub_until": start_time + delta
                }
            }
        )

    async def get_or_create_user(self, id: int) -> User:
        user = await self.users.find_one({ "id": id })

        if not user:
            user = {
                "id": id,
                "token": uuid(),
                "dates": {
                    "created_at": datetime.now(),
                    "sub_until": datetime.now()
                },
                "configs": {},
                "server": "n-best",
                "lang": "ru"
            }

            await self.users.insert_one(user)

        return user