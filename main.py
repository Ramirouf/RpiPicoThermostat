# Author: Ramiro Uffelmann
# Note: Given that "btree" is unavailable, a JSON file is used to store parameters.
# Nota: La consigna de la actividad solicita suscribirse a tópico "relé", pero el uso de tildes ocasiona desconexión de red de la placa, por lo que se optó por usar "rele".
from mqtt_as import MQTTClient, config
import machine, dht
from machine import Pin
import asyncio
from settings import SSID, password, BROKER
import ujson

config["ssid"] = SSID
config["wifi_pw"] = password
config["server"] = BROKER
# config["ssl_params"] = {"server_hostname": BROKER, "certfile": "/flash/cert.pem"}

# Parameters file -----
PARAMS_FILE = "params.json"
# Create parameters dictionary and define default values.
default_params = {
    "setpoint": 25.0,
    "period": 10,
    "mode": 0,  # mode=0: automatic; 1 for manual
    "relay": 0,
}


def load_params():
    try:
        with open(PARAMS_FILE, "r") as f:
            params = ujson.load(f)
    except Exception:
        params = default_params.copy()
        save_params(params)
    return params


def save_params(params):
    try:
        with open(PARAMS_FILE, "w") as f:
            ujson.dump(params, f)
    except Exception as e:
        print("Error saving parameters:", e)


params = load_params()
print("Parameters loaded!")

# Hardware
device_id = "".join("{:02X}".format(b) for b in machine.unique_id())
dht_sensor = dht.DHT11(Pin(16))
led = Pin("LED", Pin.OUT)
relay = Pin(15, Pin.OUT)
measure = {}


# Measures the sensor at a certain period and stores data in memory
async def measure_sensor():
    while True:
        dht_sensor.measure()
        measure["temperature"] = dht_sensor.temperature()
        measure["humidity"] = dht_sensor.humidity()
        await asyncio.sleep(1)


# Coroutine for publishing JSON
async def publish():
    while True:
        payload = {
            "temperatura": measure["temperature"],
            "humedad": measure["humidity"],
            "setpoint": params["setpoint"],
            "periodo": params["period"],
            "modo": params["mode"],
        }
        payload_str = ujson.dumps(payload)
        print("Publishing: ", payload_str)
        await client.publish(device_id, payload_str)
        await asyncio.sleep(params["period"])


# Handle reconnections and subscriptions
async def up(client):  # Handle reconnection
    while True:
        await client.up.wait()
        client.up.clear()
        # Subscription with QoS=1 so the client responds an ACK to the broker when a QoS=1 message is received
        topics = [
            (f"{device_id}/setpoint", 1),
            (f"{device_id}/periodo", 1),
            (f"{device_id}/modo", 1),
            (f"{device_id}/rele", 1),
            (f"{device_id}/destello", 1),
        ]
        for topic, qos in topics:
            await client.subscribe(topic, qos)
            await asyncio.sleep(0.5)
            print("Subscribed to: ", topic, " with QoS: ", qos)


async def messages(client):  # Respond to incoming messages
    async for topic, msg, retained in client.queue:
        topic = topic.decode()
        payload = msg.decode()
        if topic == f"{device_id}/setpoint":
            try:
                params["setpoint"] = float(payload)
                save_params(params)
                print("Setpoint updated:", params["setpoint"])
            except ValueError:
                print("Invalid setpoint value")
        elif topic == f"{device_id}/periodo":
            try:
                params["period"] = int(payload)
                save_params(params)
                print("Period updated:", params["period"])
            except ValueError:
                print("Invalid period value")
        elif topic == f"{device_id}/modo":
            try:
                if int(payload) in [0, 1]:
                    params["mode"] = int(payload)
                    save_params(params)
                    print("Mode updated:", params["mode"])
                else:
                    print("Invalid mode value")
            except ValueError:
                print("Invalid mode value. Should be 0 for automatic and 1 for manual")
        elif topic == f"{device_id}/rele":
            # In manual mode, update relay state immediately.
            try:
                relay_val = int(payload)
                print(params["mode"])
                if params["mode"] == 1:  # Check if it's in manual
                    relay.value(relay_val)
                    params["relay"] = relay_val
                    save_params(params)
                    print("Relay updated (manual):", relay_val)
                else:
                    print("Ignored relay command in auto mode")
            except ValueError:
                print("Invalid relay value")
        elif topic == f"{device_id}/destello":
            # Blink LED on receiving "destello" command
            print("Blink command received")
            await blink()
        else:
            print("Unknown topic")


async def blink():
    # Blink the LED for a few seconds.
    led.value(1)
    await asyncio.sleep(0.2)
    led.value(0)
    await asyncio.sleep(0.2)
    led.value(1)
    await asyncio.sleep(0.2)
    led.value(0)
    await asyncio.sleep(0.2)


# Handle automatic relay control
async def relay_control():
    while True:
        if params["mode"] == 0:  # Automatic mode
            print("measure: ", measure)
            if measure["temperature"] > params["setpoint"]:
                relay.value(1)  # Turn on relay
            else:
                relay.value(0)  # Turn off relay
        await asyncio.sleep(1)


async def main(client):
    print("Device ID: ", device_id)
    await client.connect(quick=True)
    asyncio.create_task(measure_sensor())
    asyncio.create_task(publish())
    asyncio.create_task(up(client))
    asyncio.create_task(messages(client))
    asyncio.create_task(relay_control())
    while True:
        await asyncio.sleep(1)


config["queue_len"] = 1  # Use event interface with default queue size
MQTTClient.DEBUG = True  # type: ignore
client = MQTTClient(config)
try:
    asyncio.run(main(client))
except KeyboardInterrupt:
    print("Received Ctrl+C, shutting down...")
    # Turn off relay
    relay.value(0)
finally:
    client.close()  # Prevent LmacRxBlk:1 errors
