import paho.mqtt.client as mqtt
import json
import time
import math
from datetime import datetime
import os

# CONFIGURACIÓN DEL BROKER MQTT (nombre del servicio en Docker o localhost)
BROKER_HOST = os.getenv("BROKER_HOST", "localhost")
BROKER_PORT = int(os.getenv("BROKER_PORT", "1883"))
TOPIC = "tank/esp32_01/ultrasonic/measurements"

# DATOS DEL DISPOSITIVO
DEVICE_ID = "esp32_01"

# Variables de simulación
angle = 0
direction = 1  # 1 = sube, -1 = baja

# --- CALLBACKS DE DEPURACIÓN ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Conectado al broker MQTT ({BROKER_HOST}:{BROKER_PORT})")
    else:
        print("❌ Error de conexión. Código:", rc)

def on_publish(client, userdata, mid):
    print("📤 Mensaje publicado correctamente.")

# --- CONFIGURACIÓN DEL CLIENTE ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_publish = on_publish

print(f"🔌 Conectando al broker MQTT en {BROKER_HOST}:{BROKER_PORT}...")
client.connect(BROKER_HOST, BROKER_PORT, 60)
client.loop_start()

# --- BUCLE PRINCIPAL ---
try:
    while True:
        # Simula distancia entre 10 y 90 cm (onda sinusoidal)
        distance = 50 + 40 * math.sin(math.radians(angle))
        raw_us = int(distance * 58)  # microsegundos aproximados

        payload = {
            "device_id": DEVICE_ID,
            "distance_cm": round(distance, 2),
            "angle_deg": round(angle, 2),
            "raw_us": raw_us,
            "correlation_id": f"sim-{int(time.time())}"
        }

        msg = json.dumps(payload)
        client.publish(TOPIC, msg)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] → {msg}")

        # Movimiento de ángulo
        angle += direction * 10
        if angle >= 180:
            direction = -1
            angle = 180
        elif angle <= 0:
            direction = 1
            angle = 0

        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 Simulación detenida por el usuario.")
finally:
    client.loop_stop()
    client.disconnect()
    print("🔒 Desconectado del broker MQTT.")
