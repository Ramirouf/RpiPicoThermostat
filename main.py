from machine import Pin
import machine, dht
from mqtt_as import MQTTClient, config
import asyncio
from settings import SSID, password, BROKER
import ujson

config["ssid"] = SSID
config["wifi_pw"] = password
config["server"] = BROKER
config["ssl_params"] = {"server_hostname": BROKER, "certfile": "/flash/cert.pem"}


PARAMS_FILE = "params.json"
default_params = {
    "setpoint": 25.0,  # Temperature setpoint in Celsius
    "period": 1,  # Publishing period in seconds
    "mode": "auto",  # "auto" or "manual"
    "relay": 0,  # Relay state (0=off, 1=on)
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


# ----- Hardware Setup -----
# Define sensor and relay pins
dht_sensor = dht.DHT11(Pin(16))
relay = Pin(15, Pin.OUT)
# Optionally, use an LED for blink feedback
blink_led = Pin("LED", Pin.OUT)
# Get unique ID for topics
device_id = "".join("{:02X}".format(b) for b in machine.unique_id())

# Global parameters (loaded from non-volatile storage)
params = load_params()
print("Parameters loaded!")


async def messages(client):  # Respond to incoming messages
    global params
    async for topic, msg, retained in client.queue:
        topic = topic.decode()
        payload = msg.decode()
        print("Received on", topic, ":", payload, "retained: ", retained)
        # Determine action based on the topic
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
            payload = payload.strip()
            if payload in ["auto", "manual"]:
                params["mode"] = payload
                save_params(params)
                print("Mode updated:", params["mode"])
            else:
                print("Invalid mode value")
        elif topic == f"{device_id}/relé":
            # In manual mode, update relay state immediately.
            try:
                relay_val = int(payload)
                if params["mode"] == "manual":
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
            asyncio.create_task(blink())
        else:
            print("Unknown topic")


async def up(client):  # Respond to connectivity being (re)established
    while True:
        await client.up.wait()  # Wait on an Event
        client.up.clear()
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
            print("Subscribed to", topic)


async def blink():
    # Blink the LED for a few seconds.
    blink_led.value(1)
    await asyncio.sleep(0.2)
    blink_led.value(0)
    await asyncio.sleep(0.2)


async def sensor_task(client):
    # Read sensor data, control the relay (auto mode) and publish data as JSON.
    global params
    # n = 0
    while True:
        await asyncio.sleep(params.get("period", 1))
        try:
            dht_sensor.measure()
            temp = dht_sensor.temperature()
            hum = dht_sensor.humidity()
            print("temp: ", temp, "hum: ", hum)
        except Exception as e:
            print("Sensor error:", e)
            temp = None
            hum = None

        # In auto mode, control the relay based on setpoint.
        if params["mode"] == "auto" and temp is not None:
            if temp > params["setpoint"]:
                relay.value(1)
                params["relay"] = 1
            else:
                relay.value(0)
                params["relay"] = 0
            save_params(params)

        # Build JSON payload
        payload = {
            "temperature": temp,
            "humidity": hum,
            "setpoint": params["setpoint"],
            "period": params["period"],
            "mode": params["mode"],
            "relay": params["relay"],
        }
        payload_str = ujson.dumps(payload)
        print("Publishing:", payload_str)
        try:
            await client.publish(device_id, payload_str, qos=1)
        except Exception as e:
            print("Publish error:", e)
        # n += 1


async def main(client):
    print("Device ID: ", device_id)
    await client.connect(quick=True)
    asyncio.create_task(up(client))
    asyncio.create_task(messages(client))
    asyncio.create_task(sensor_task(client))


config["queue_len"] = 1  # Use event interface with default queue size
MQTTClient.DEBUG = True
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    client.close()  # Prevent LmacRxBlk:1 errors
