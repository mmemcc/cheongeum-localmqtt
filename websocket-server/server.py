import asyncio
import websockets
import json
from pymongo import MongoClient

mongo = MongoClient("mongodb://mongo:27017/")
db = mongo["esp32_db"]
accel_collection = db["accel_data"]
env_collection = db["env_data"]
relay_collection = db["relay_data"]


last_sent_id = None  # ObjectId 기준으로 순차 전송

async def send_data(websocket):
    global last_sent_id 
    print("클라이언트 연결됨")
    try:
        while True:

            data = {}
            accel_doc = accel_collection.find_one(sort=[("_id", -1)])


            env_doc = env_collection.find_one(sort=[("timestamp", -1)])
            
            relay_doc = relay_collection.find_one(sort=[("timestamp", -1)])

            

            if accel_doc and accel_doc["_id"] != last_sent_id:
                last_sent_id = accel_doc["_id"]  # 중복 방지용 업데이트
                data["accel"] = {
                    "timestamp": accel_doc["timestamp"],
                    "accel_data": accel_doc["accel_data"]
                }

            if env_doc:
                data["env"] = {
                    "timestamp": env_doc.get("timestamp"),
                    "temp_data": {
                        k: v for k, v in env_doc.items() if k.startswith("temp")
                    },
                    "current_data": {
                        k: v for k, v in env_doc.items() if k.startswith("current")
                    }
                }
            
            if relay_doc:
                relay_data = {
                    "us": relay_doc.get("us"),
                    **{k: v for k, v in relay_doc.items() if k.startswith("relay")}
                }
                data["relay"] = {
                    "timestamp": relay_doc.get("timestamp"),
                    "relay_data": relay_data
                }
                
            if data:
                await websocket.send(json.dumps(data, default=str))  # timestamp 처리용

            await asyncio.sleep(1)
            
    except websockets.exceptions.ConnectionClosed:
        print("클라이언트 연결 종료됨")

async def main():
    async with websockets.serve(send_data, "", 8765):
        print("WebSocket 서버 시작됨")
        await asyncio.Future()  # 서버 무한 대기

asyncio.run(main())
