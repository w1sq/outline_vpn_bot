import express from "express";
import { MongoClient } from "mongodb";
import { OutlineVPN } from "outlinevpn-api";
import { config } from "dotenv";
import haversine from "haversine";
import axios from "axios";
import cors from "cors";

const corsOptions = {
    origin: '*',
    methods: ['GET', 'HEAD'],
    allowedHeaders: '*',
    maxAge: 3000
};

config({ path: "../.env" });
const mongo = new MongoClient(process.env.MONGO_URI);
const db = mongo.db(process.env.DB_NAME);
const users = db.collection("users");
const servers = db.collection("servers");
const server = express();

server.use(cors(corsOptions));

const vpns = {};
const vpnsCoords = {}
const setupVpns = async () => {
    const docs = await servers.find({ enabled: true }).toArray();

    console.log("setup vpns", docs);
    for (const doc of docs) {
        vpns[doc.id] = new OutlineVPN({
            apiUrl: doc.api,
            fingerprint: doc.fingerprint
        })
        vpnsCoords[doc.id] = doc.location;
    }
}

const fetchUserServer = async (token, ip) => {
    // console.log("users", await users.find({}).toArray());
    const user = await users.findOne({ token: token });

    if (!user) {
        return {
            access: false,
            message: "Invalid token.",
            connect: null
        };
    }

    if (new Date() > user.dates.sub_until) {
        for (const vpn in user.configs) {
            try {
                await vpns[vpn].deleteUser(user.configs[vpn]);
            } catch {}
        }

        await users.updateOne(
            {
                "_id": user["_id"]
            },
            {
                "$set": {
                    "server": "n-best",
                    "configs": {}
                }
            }
        )

        return {
            access: false,
            message: "Subscription has ended.",
            connect: null
        };
    }

    if (!(user.server in vpns)) {
        user.server = "n-best";

        await users.updateOne(
            {
                "_id": user["_id"]
            },
            {
                "$set": {
                    "server": "n-best"
                }
            }
        )
    }

    if (user.server == "n-best") {
        try {
            // console.log(`http://ip-api.com/json/${ip}`);
            const { data } = await axios.get(`http://ip-api.com/json/${ip}`);

            let bestVpn = "";
            let bestDist = 999999999999999;
            for (const vpn in vpnsCoords) {
                const coords = vpnsCoords[vpn];

                const distance = haversine(
                    {
                        latitude: data["lat"], 
                        longitude: data["lon"] 
                    },
                    {
                        latitude: coords[0],
                        longitude: coords[1]
                    },
                    { 
                        unit: 'meter'
                    }
                )

                if (bestDist > distance / 1000) {
                    bestDist = distance / 1000
                    bestVpn = vpn
                }
            }

            user.server = bestVpn;
        } catch (e) {
            console.error(e)
            return {
                access: false,
                message: "Failed to find nearest server. Try again later or manual set location.",
                connect: null
            };
        }
    }
    
    if (user.server in user.configs) {
        // console.debug("Server in configs");

        let vpnUser = await vpns[user.server].getUser(user.configs[user.server]);

        if (!vpnUser) {
            console.debug("Server-side config not found creating new");
            vpnUser = await vpns[user.server].createUser();
        }

        const field = `configs.${user.server}`;
        await users.updateOne(
            {
                "_id": user["_id"]
            },
            {
                "$set": {
                    [field]: vpnUser.id
                }
            }
        )

        // console.debug("Setting config for user");

        return {
            access: true,
            message: null,
            connect: vpnUser.accessUrl
        };
    } else {
        // console.debug("Server not in configs creating new");
        let vpnUser = await vpns[user.server].createUser();

        const field = `configs.${user.server}`;
        await users.updateOne(
            {
                "_id": user["_id"]
            },
            {
                "$set": {
                    [field]: vpnUser.id
                }
            }
        )

        // console.debug("Setting config for user");

        return {
            access: true,
            message: null,
            connect: vpnUser.accessUrl
        };
    }
}

server.get("/:token", async (req, res) => {
    let ip = "91.122.4.45"
    if ("cf-connecting-ip" in req.headers) {
        ip = req.headers["cf-connecting-ip"];
        console.log("Client connecting from", ip)
    }

    const { access, message, connect } = await fetchUserServer(req.params.token, ip);

    if (!access) {
        console.log("Client get error", message)
        return res.json({
            "error": {
              "message": message
            }
        });
    }
    
    console.log("Client connected to", connect)

    console.log(req.headers);

    return res.send(connect);
})

server.listen(9127, async () => {
    await mongo.connect();
    await setupVpns()
})