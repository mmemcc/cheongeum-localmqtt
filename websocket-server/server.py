import asyncio
import websockets
import json
from pymongo import MongoClient
from datetime import datetime, timezone

mongo = MongoClient("mongodb://mongo:27017/")
db = mongo["esp32_db"]
db_server = mongo["server_db"]
accel_collection = db["accel_data"]
env_collection = db["env_data"]
relay_collection = db["relay_data"]
server_collection = db_server["relay_control_data"]
mode_collection = db_server["mode_control_data"]
target_temp_collection = db_server["target_temp_data"]
last_sent_id_accel = None
last_sent_id_env = None
last_sent_id_relay = None

async def send_sensor_data(websocket):
    global last_sent_id_accel, last_sent_id_env, last_sent_id_relay
    try:
        while True:
            data = {}
            accel_doc = accel_collection.find_one(sort=[("_id", -1)])
            env_doc = env_collection.find_one(sort=[("timestamp", -1)])
            relay_doc = relay_collection.find_one(sort=[("timestamp", -1)])

            if accel_doc and accel_doc["_id"] != last_sent_id_accel:
                last_sent_id_accel = accel_doc["_id"]
                data["accel"] = {
                    "timestamp": accel_doc["timestamp"],
                    "accel_data": accel_doc["accel_data"]
                }

            if env_doc and env_doc["_id"] != last_sent_id_env:
                last_sent_id_env = env_doc["_id"]
                data["env"] = {
                    "timestamp": env_doc.get("timestamp"),
                    "temp_data": {k: v for k, v in env_doc.items() if k.startswith("temp")},
                    "current_data": {k: v for k, v in env_doc.items() if k.startswith("current")},
                    "inside_data": {k: v for k, v in env_doc.items() if k.startswith("humi_temp")}
                }

            if relay_doc and relay_doc["_id"] != last_sent_id_relay:
                last_sent_id_relay = relay_doc["_id"]
                relay_data = {
                    "us": relay_doc.get("us"),
                    **{k: v for k, v in relay_doc.items() if k.startswith("relay")}
                }
                data["relay"] = {
                    "timestamp": relay_doc.get("timestamp"),
                    "relay_data": relay_data
                }

            if data:
                await websocket.send(json.dumps(data, default=str))
            await asyncio.sleep(0.01)
    except websockets.exceptions.ConnectionClosed:
        print("클라이언트 연결 종료됨 (send_sensor_data)")

async def receive_commands(websocket):
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                print(data)
                if data.get("type") == "relay_control":
                    relay = data.get("relay")  # relay1, relay2, ...
                    control = data.get("state")  # 0 or 1
                    # DB에 저장
                    relay_control_doc = {
                        "relay": relay,
                        "control": control,
                        "timestamp": datetime.now(timezone.utc)
                    }
                    server_collection.insert_one(relay_control_doc)
                    print(f"릴레이 제어 명령 저장: {relay_control_doc}")

                if data.get("type") == "mode_select":
                    relay = data.get("relay")
                    mode = data.get("mode")
                    print(f"모드 선택 명령 저장: {mode}")
                    mode_control_doc = {
                        "relay": relay,
                        "mode": mode,
                        "timestamp": datetime.now(timezone.utc)
                    }
                    mode_collection.insert_one(mode_control_doc)
                    print(f"모드 선택 명령 저장: {mode_control_doc}")

                if data.get("type") == "set_target_temp":
                    target_temp = data.get("target_temp")
                    print(f"목표 온도 설정 명령 저장: {target_temp}")
                    target_temp_doc = {
                        "target_temp": target_temp,
                        "timestamp": datetime.now(timezone.utc)
                    }
                    target_temp_collection.insert_one(target_temp_doc)
                    print(f"목표 온도 설정 명령 저장: {target_temp_doc}")
            except Exception as e:
                print("명령 처리 오류:", e)
    except websockets.exceptions.ConnectionClosed:
        print("클라이언트 연결 종료됨 (receive_commands)")

async def handle_client(websocket):
    try:
        await asyncio.gather(
            send_sensor_data(websocket),
            receive_commands(websocket)
        )
    except websockets.exceptions.ConnectionClosed:
        print("클라이언트 연결 종료됨 (handle_client)")

async def main():
    async with websockets.serve(handle_client, "", 8765):
        print("WebSocket 서버 시작됨")
        await asyncio.Future()

asyncio.run(main())
