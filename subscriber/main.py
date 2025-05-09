import paho.mqtt.client as mqtt
from pymongo import MongoClient
from datetime import datetime
import json
import threading


# MongoDB 연결
mongo = MongoClient("mongodb://mongo:27017/")
db = mongo["esp32_db"]
db_server = mongo["server_db"]
accel_collection = db["accel_data"]
env_collection = db["env_data"]
relay_collection = db["relay_data"]
target_temp_collection = db_server["target_temp_data"]
relay_control_collection = db_server["relay_control_data"]
mode_control_collection = db_server["mode_control_data"]

# MQTT 브로커 설정
MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883
TOPICS = [("esp32/accel", 0), ("esp32/env", 0), ("esp32/relay", 0)]

def convert_datetime(obj):
    if isinstance(obj, dict):
        return {k: convert_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime(i) for i in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj

# MQTT 콜백 - 연결 성공
def on_connect(client, userdata, flags, rc):
    print("MQTT 연결됨:", rc)
    client.subscribe(TOPICS)
    print("토픽 구독 완료:", TOPICS)

# MQTT 콜백 - 메시지 수신 (ESP32 → DB)
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        # print(f"[{msg.topic}] 수신:", payload)
        
        if msg.topic == "esp32/accel":
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
            
        elif msg.topic == "esp32/relay":
            payload["timestamp"] = datetime.utcnow().isoformat()
            relay_collection.insert_one(payload)
            print("→ relay_data 컬렉션에 저장 완료")

    except Exception as e:
        print("에러:", e)

# db_server 컬렉션 감시 → MQTT publish
def publish_to_mqtt(topic, doc):
    doc = dict(doc)
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    doc = convert_datetime(doc)
    payload = json.dumps(doc)
    client.publish(topic, payload)
    print(f"MQTT로 전송: {topic} {payload}")

def watch_collection(collection, topic):
    print(f"Change Stream 감시 시작: {collection.name} → {topic}")
    with collection.watch([{"$match": {"operationType": "insert"}}]) as stream:
        for change in stream:
            new_doc = change["fullDocument"]
            publish_to_mqtt(topic, new_doc)

if __name__ == "__main__":
    # MQTT 클라이언트(ESP32 → DB)
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    # db_server 컬렉션 감시(서버 → ESP32)
    threading.Thread(target=watch_collection, args=(target_temp_collection, "esp32/target_temp"), daemon=True).start()
    threading.Thread(target=watch_collection, args=(relay_control_collection, "esp32/manual_relay"), daemon=True).start()
    threading.Thread(target=watch_collection, args=(mode_control_collection, "esp32/mode"), daemon=True).start()

    print("MQTT 브릿지 + DB 감시 동작 중...")
    client.loop_forever()
