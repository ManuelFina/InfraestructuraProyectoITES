FROM python:3.11-slim

# Crear directorio de trabajo
WORKDIR /app

# Copiar el script al contenedor
COPY simulator.py .

# Instalar dependencias
RUN pip install paho-mqtt

# Cambiar el host al servicio de mosquitto dentro del compose
ENV BROKER_HOST=mosquitto
ENV BROKER_PORT=1883

# Ejecutar el simulador
CMD ["python", "simulator.py"]
