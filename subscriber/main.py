import paho.mqtt.client as mqtt
from pymongo import MongoClient
from datetime import datetime
import json
import threading
import time

# MongoDB 연결
mongo = MongoClient("mongodb://mongo:27017/")
db = mongo["esp32_db"]
accel_collection = db["accel_data"]
env_collection = db["env_data"]

# MQTT 브로커 설정
MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883
TOPICS = [("esp32/accel", 0), ("esp32/env", 0)]
                
# MQTT 콜백 - 연결 성공
def on_connect(client, userdata, flags, rc):
    print("MQTT 연결됨:", rc)
    client.subscribe(TOPICS)
    print("토픽 구독 완료:", TOPICS)

# MQTT 콜백 - 메시지 수신
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"[{msg.topic}] 수신:", payload)
        
        if msg.topic == "esp32/accel":
            # payload 전체에 accel_data 배열 포함됨
            accel_data = payload.get("accel_data", [])
            
            if isinstance(accel_data, list):
                doc = {
                    "device_id": payload.get("device_id", "esp32-01"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "accel_data": accel_data
                }
                accel_collection.insert_one(doc)
                print(f"→ accel_data 컬렉션에 저장 완료 ({len(accel_data)}개)")
            else:
                print("⚠ accel_data 필드가 리스트가 아닙니다.")

        elif msg.topic == "esp32/env":
            payload["timestamp"] = datetime.utcnow().isoformat()
            env_collection.insert_one(payload)
            print("→ env_data 컬렉션에 저장 완료")

    except Exception as e:
        print("에러:", e)


# MQTT 클라이언트 실행
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
