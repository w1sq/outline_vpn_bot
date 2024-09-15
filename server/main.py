import os
import asyncio
import aiohttp
from datetime import datetime
from dotenv import load_dotenv

from pymongo import MongoClient
from outline_vpn.outline_vpn import OutlineVPN
import haversine
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv(dotenv_path="../.env")

mongo = MongoClient(os.getenv("MONGO_URI"))
db = mongo[os.getenv("DB_NAME")]
users = db["users"]
servers = db["servers"]
app = Flask(__name__)

CORS(
    app,
    resources={r"/*": {"origins": "*", "methods": ["GET", "HEAD"], "max_age": 3000}},
)

vpns = {}
vpns_coords = {}


async def setup_vpns():
    docs = list(servers.find({"enabled": True}))
    print("setup vpns", docs)
    for doc in docs:
        vpns[doc["id"]] = OutlineVPN(api_url=doc["api"], cert_sha256=doc["fingerprint"])
        vpns_coords[doc["id"]] = doc["location"]


async def fetch_user_server(token, ip):
    user = users.find_one({"token": token})

    if user is None:
        return {"access": False, "message": "Invalid token.", "connect": None}

    if user["dates"]["sub_until"] < datetime.now():
        for vpn, config in user["configs"].items():
            try:
                vpns[vpn].delete_key(config)
            except Exception as e:
                print(f"Failed to delete user config for VPN {vpn}: {str(e)}")

        users.update_one(
            {"_id": user["_id"]}, {"$set": {"server": "n-best", "configs": {}}}
        )

        return {"access": False, "message": "Subscription has ended.", "connect": None}

    if user["server"] not in vpns:
        user["server"] = "n-best"
        users.update_one({"_id": user["_id"]}, {"$set": {"server": "n-best"}})

    if user["server"] == "n-best":
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://ip-api.com/json/{ip}") as response:
                    data = await response.json()

            best_vpn = min(
                vpns_coords.items(),
                key=lambda x: haversine.haversine(
                    (data["lat"], data["lon"]), (x[1][0], x[1][1]), unit="km"
                ),
            )[0]

            user["server"] = best_vpn
        except Exception as e:
            print(f"Error: {e}")
            return {
                "access": False,
                "message": "Failed to find nearest server. Try again later or manual set location.",
                "connect": None,
            }

    if user["server"] in user["configs"]:
        vpn_user = vpns[user["server"]].get_key(user["configs"][user["server"]])

        if not vpn_user:
            vpn_user = vpns[user["server"]].create_key()

        users.update_one(
            {"_id": user["_id"]},
            {"$set": {f"configs.{user['server']}": vpn_user.key_id}},
        )

        return {"access": True, "message": None, "connect": vpn_user.access_url}
    else:
        vpn_user = vpns[user["server"]].create_key()

        users.update_one(
            {"_id": user["_id"]},
            {"$set": {f"configs.{user['server']}": vpn_user.key_id}},
        )

        return {"access": True, "message": None, "connect": vpn_user.access_url}


@app.route("/<token>")
async def get_user_server(token):
    ip = request.headers.get("cf-connecting-ip", "91.122.4.45")
    print(f"Client connecting from {ip}")

    result = await fetch_user_server(token, ip)

    if not result["access"]:
        print(f"Client get error {result['message']}")
        return jsonify({"error": {"message": result["message"]}}), 400

    print(f"Client connected to {result['connect']}")
    print(request.headers)

    return result["connect"]


if __name__ == "__main__":
    asyncio.run(setup_vpns())
    app.run(port=9127)
