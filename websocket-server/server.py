import asyncio
import websockets
import json
from pymongo import MongoClient

mongo = MongoClient("mongodb://mongo:27017/")
db = mongo["esp32_db"]
accel_collection = db["accel_data"]
temp_collection = db["env_data"]
relay_collection = db["relay_data"]


last_sent_id = None  # ObjectId 기준으로 순차 전송

async def send_data(websocket):
    global last_sent_id 
    print("클라이언트 연결됨")
    try:
        while True:
            # 새로 들어온 accel document 찾기
            query = {}
            if last_sent_id:
                query["_id"] = {"$gt": last_sent_id}
            
            accel_doc = accel_collection.find_one(
                query,
                sort=[("_id", 1)]  # ObjectId 기준 오름차순 (시간 순서와 유사)
            )

            temp_doc = temp_collection.find_one(sort=[("timestamp", -1)])
            
            relay_doc = relay_collection.find_one(sort=[("timestamp", -1)])

            data = {}

            if accel_doc:
                last_sent_id = accel_doc["_id"]  # 다음 루프부터 이 이후만 찾도록

                data["accel"] = {
                    "timestamp": accel_doc["timestamp"],
                    "accel_data": accel_doc["accel_data"]  # 1600개 통째로 보냄
                }

            if temp_doc:
                data["temp"] = {
                    "timestamp": temp_doc.get("timestamp"),
                    "env_data": {
                        k: v for k, v in temp_doc.items() if k.startswith("temp")
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
