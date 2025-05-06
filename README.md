# Raspberry Pi Pico W Thermostat with MQTT Control

This project implements a smart thermostat using a Raspberry Pi Pico W, a DHT11 temperature and humidity sensor, and a relay. It offers both manual and automatic control modes, configurable via MQTT over a secure connection (MQTTs). The system is programmed in MicroPython, leveraging the `asyncio` and `mqtt_as` libraries for efficient and event-driven communication.

## Features

* **Dual Control Modes:**
    * **Automatic Mode:** The relay is activated when the measured temperature exceeds the configured setpoint.
    * **Manual Mode:** The relay state is directly controlled via MQTT commands.
* **MQTT Communication (MQTTs):** Securely communicates with an MQTT broker.
* **Periodic Data Publishing:** Publishes temperature, humidity, setpoint, period, mode, and relay status as a JSON payload to the topic `DEVICE_ID` (replace `DEVICE_ID` with your unique device identifier).
* **MQTT Subscription:** Subscribes to the following topics under `DEVICE_ID`:
    * `/setpoint`: To receive new temperature setpoint values.
    * `/periodo`: To receive updates to the data publishing period.
    * `/destello`: To trigger a visual indication (e.g., blinking an LED).
    * `/modo`: To switch between "auto" and "manual" control modes.
    * `/rele`: To directly control the relay state in manual mode ("on" or "off").
* **Non-Volatile Storage:** Utilizes the `btree` module to persistently store the setpoint, period, mode, and relay state across reboots.
* **On-Demand Blink:** Upon receiving a "destello" command via MQTT, the Pico W will briefly blink an indicator (you'll need to define the blinking behavior in the code).
* **Dynamic Configuration:** When new non-volatile parameters are received via MQTT, the system updates its stored values and immediately adjusts its behavior if necessary.
* **Event-Driven Architecture:** Employs an event-based approach using `asyncio` and `mqtt_as`, avoiding the complexities of traditional callback functions.

## Hardware Components

* Raspberry Pi Pico W
* DHT11 Temperature and Humidity Sensor
* Relay module (compatible with Raspberry Pi Pico W voltage levels)
* (Optional) LED for visual feedback

## Software

* MicroPython firmware installed on the Raspberry Pi Pico W.
* Required MicroPython libraries:
    * `umqtt.simple` (or `mqtt_as`)
    * `dht` (or a similar library for DHT11)
    * `machine`
    * `asyncio`
    * `btree`
    * `json`
    * `time`
* MQTT broker with TLS/SSL enabled for secure communication.

## Setup and Usage

1.  **Hardware Connections:** Connect the DHT11 sensor and the relay module to the appropriate GPIO pins on the Raspberry Pi Pico W. Refer to the code for the specific pin assignments.
2.  **Install MicroPython Libraries:** Ensure the necessary libraries (`umqtt.simple` or `mqtt_as`, `dht`, `btree`) are installed on your Raspberry Pi Pico W. You might need to use `upip` for this.
3.  **Configure MQTT Broker:** Set up an MQTT broker that supports TLS/SSL. Note down the broker address, port, and any required credentials.
4.  **Configure `config.py` (or similar):** Create a configuration file (e.g., `config.py`) to store your Wi-Fi credentials, MQTT broker details, and the `DEVICE_ID`.
5.  **Upload Code:** Upload the MicroPython code (`main.py` and any other necessary files) to your Raspberry Pi Pico W.
6.  **Run the Script:** The `main.py` script will automatically connect to your Wi-Fi network and the MQTT broker upon startup.
7.  **Control via MQTT:** Use an MQTT client to subscribe to the relevant topics and publish commands to control the thermostat:
    * Publish to `DEVICE_ID/setpoint` with a numeric value (e.g., `25`) to set the target temperature.
    * Publish to `DEVICE_ID/periodo` with an integer value (in seconds) to change the data publishing interval.
    * Publish `"blink"` to `DEVICE_ID/destello` to trigger the blink.
    * Publish `"auto"` or `"manual"` to `DEVICE_ID/modo` to switch control modes.
    * In manual mode, publish `"on"` or `"off"` to `DEVICE_ID/relé` to control the relay.

## Code Structure

The main script (`main.py`) will likely contain the following sections:

* **Import Statements:** Imports necessary libraries.
* **Configuration:** Reads Wi-Fi and MQTT settings from a configuration file.
* **Hardware Initialization:** Initializes the DHT11 sensor and the relay pin.
* **Non-Volatile Storage:** Initializes and loads persistent data using the `btree` module.
* **MQTT Connection and Event Handlers:** Establishes the MQTT connection and defines asynchronous event handlers for subscribed topics.
* **Data Publishing Task:** An asynchronous task that periodically reads sensor data and publishes it to the MQTT broker.
* **Thermostat Logic:** Implements the automatic and manual control logic for the relay.
* **Blink Functionality:** Implements the visual blink when the "destello" command is received.
* **Main Asynchronous Loop:** Starts the asynchronous tasks.

## Git Repository

The complete code for this project can be found in the following Git repository:

\[Your Git Repository URL Here]

Feel free to explore the code and adapt it to your specific needs.