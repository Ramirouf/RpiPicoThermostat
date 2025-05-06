from mqtt_as import MQTTClient, config
import machine, dht
from machine import Pin
import asyncio
from settings import SSID, password, BROKER
import ujson

config["ssid"] = SSID
config["wifi_pw"] = password
config["server"] = BROKER

# Hardware
device_id = "".join("{:02X}".format(b) for b in machine.unique_id())
dht_sensor = dht.DHT11(Pin(16))
measure = {}


async def measure_sensor():
    while True:
        dht_sensor.measure()
        measure["temperature"] = dht_sensor.temperature()
        measure["humidity"] = dht_sensor.humidity()
        await asyncio.sleep(2)  # Replace with actual period from params


# Coroutine for publishing JSON
async def publish():
    while True:
        payload = {
            "temperature": measure["temperature"],
            "humidity": measure["humidity"],
        }
        payload_str = ujson.dumps(payload)
        print("Publishing: ", payload_str)
        await client.publish(device_id, payload_str)
        await asyncio.sleep(5)


async def main(client):
    print("Device ID: ", device_id)
    await client.connect(quick=True)
    asyncio.create_task(measure_sensor())
    asyncio.create_task(publish())
    while True:
        await asyncio.sleep(1)


config["queue_len"] = 1  # Use event interface with default queue size
MQTTClient.DEBUG = True  # type: ignore
client = MQTTClient(config)
try:
    asyncio.run(main(client))
except KeyboardInterrupt:
    print("Received Ctrl+C, shutting down...")
finally:
    client.close()  # Prevent LmacRxBlk:1 errors
