import paho.mqtt.client as mqtt
import json
import random
import time
import math
from datetime import datetime

# CONFIGURACIÓN DEL BROKER MQTT
BROKER_HOST = "localhost"      # o IP del servidor Docker
BROKER_PORT = 1883
TOPIC = "tank/esp32_01/ultrasonic/measurements"

# SIMULACIÓN DE DATOS
DEVICE_ID = "esp32_01"

# el ángulo gira de 0 a 180 grados y vuelve
angle = 0
direction = 1  # 1 = sube, -1 = baja

# debug
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado al broker MQTT")
    else:
        print("❌ Error de conexión. Código:", rc)

def on_publish(client, userdata, mid):
    print("📤 Mensaje publicado correctamente.")

# CLIENTE MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_publish = on_publish

print("🔌 Conectando al broker MQTT...")
client.connect(BROKER_HOST, BROKER_PORT, 60)
client.loop_start()

# LOOP DE ENVÍO PERIÓDICO
try:
    while True:
        # generar distancia simulada (ondas entre 10 y 90 cm)
        distance = 50 + 40 * math.sin(math.radians(angle))
        raw_us = int(distance * 58)  # valor de pulso aproximado

        payload = {
            "deviceId": DEVICE_ID,
            "distance_cm": round(distance, 2),
            "angle_deg": angle,
            "raw_us": raw_us,
            "correlationId": f"sim-{int(time.time())}"
        }

        # convertir a JSON y publicar
        msg = json.dumps(payload)
        client.publish(TOPIC, msg)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] → {msg}")

        # avanzar ángulo (efecto "barrido" del servo)
        angle += direction * 10
        if angle >= 180:
            direction = -1
            angle = 180
        elif angle <= 0:
            direction = 1
            angle = 0

        time.sleep(1)  # cada 1 segundo

except KeyboardInterrupt:
    print("\n🛑 Simulación detenida por el usuario.")
finally:
    client.loop_stop()
    client.disconnect()
    print("🔒 Desconectado del broker MQTT.")
