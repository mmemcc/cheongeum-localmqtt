import asyncio
import websockets
import json
from pymongo import MongoClient

mongo = MongoClient("mongodb://mongo:27017/")
db = mongo["esp32_db"]
accel_collection = db["accel_data"]
temp_collection = db["temp_data"]

async def send_data(websocket):
    print("클라이언트 연결됨")
    try:
        while True:
            latest = accel_collection.find().sort("timestamp", -1).limit(1)
            for doc in latest:
                data = {
                    "timestamp": doc.get("timestamp"),
                    "accel_data": doc.get("accel_data")
                }
                await websocket.send(json.dumps(data))
            await asyncio.sleep(1/10)  # 100ms 주기
    except websockets.exceptions.ConnectionClosed:
        print("클라이언트 연결 종료됨")

async def main():
    async with websockets.serve(send_data, "", 8765):
        print("WebSocket 서버 시작됨")
        await asyncio.Future()  # 서버 무한 대기

asyncio.run(main())
