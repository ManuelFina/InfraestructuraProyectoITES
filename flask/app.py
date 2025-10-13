from flask import Flask, jsonify, render_template
from flask_cors import CORS
import mysql.connector
import paho.mqtt.client as mqtt
import os
import json
from datetime import datetime
import threading

app = Flask(__name__)
CORS(app)

# Configuración de Base de Datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', 'sensordb'),
    'user': os.getenv('DB_USER', 'sensoruser'),
    'password': os.getenv('DB_PASS', 'password')
}

# Configuración MQTT
MQTT_BROKER = os.getenv('MQTT_BROKER', 'mosquitto')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'sensor/ultrasonic')

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    """Inicializa la base de datos y crea la tabla si no existe"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                distance FLOAT NOT NULL,
                angle FLOAT DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_timestamp (timestamp)
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print("Base de datos inicializada correctamente")
    except Exception as e:
        print(f"Error inicializando la base de datos: {e}")

def on_connect(client, userdata, flags, rc):
    """Callback cuando se conecta al broker MQTT"""
    if rc == 0:
        print(f"Conectado al broker MQTT en {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        print(f"Suscrito al tópico: {MQTT_TOPIC}")
    else:
        print(f"Error de conexión MQTT. Código: {rc}")

def on_message(client, userdata, msg):
    """Callback cuando llega un mensaje MQTT"""
    try:
        payload = msg.payload.decode('utf-8')
        print(f"Mensaje recibido: {payload}")
        
        # Parsear el JSON del mensaje
        data = json.loads(payload)
        distance = float(data.get('distance', 0))
        angle = float(data.get('angle', 0))
        
        # Guardar en la base de datos
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO sensor_data (distance, angle) VALUES (%s, %s)',
            (distance, angle)
        )
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Datos guardados: distance={distance}, angle={angle}")
        
    except json.JSONDecodeError as e:
        print(f"Error al parsear JSON: {e}")
    except Exception as e:
        print(f"Error al procesar mensaje: {e}")

def start_mqtt_client():
    """Inicia el cliente MQTT en un thread separado"""
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_forever()
    except Exception as e:
        print(f"Error conectando al broker MQTT: {e}")

# API Endpoints
@app.route('/')
def index():
    """Renderiza el frontend del radar"""
    return render_template('radar.html')

@app.route('/api/sensor/latest')
def get_latest_data():
    """Obtiene los últimos N registros del sensor"""
    try:
        limit = 100  # Últimas 100 lecturas
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT distance, angle, timestamp 
            FROM sensor_data 
            ORDER BY timestamp DESC 
            LIMIT %s
        ''', (limit,))
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Convertir datetime a string para JSON
        for row in data:
            row['timestamp'] = row['timestamp'].isoformat()
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sensor/stats')
def get_stats():
    """Obtiene estadísticas de los datos del sensor"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT 
                COUNT(*) as total_readings,
                AVG(distance) as avg_distance,
                MIN(distance) as min_distance,
                MAX(distance) as max_distance,
                MAX(timestamp) as last_reading
            FROM sensor_data
        ''')
        stats = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if stats['last_reading']:
            stats['last_reading'] = stats['last_reading'].isoformat()
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sensor/clear', methods=['POST'])
def clear_data():
    """Limpia todos los datos del sensor (útil para testing)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sensor_data')
        conn.commit()
        deleted = cursor.rowcount
        cursor.close()
        conn.close()
        return jsonify({'message': f'{deleted} registros eliminados'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Inicializar la base de datos
    init_db()
    
    # Iniciar el cliente MQTT en un thread separado
    mqtt_thread = threading.Thread(target=start_mqtt_client, daemon=True)
    mqtt_thread.start()
    
    # Iniciar Flask
    app.run(host='0.0.0.0', port=5000, debug=False)