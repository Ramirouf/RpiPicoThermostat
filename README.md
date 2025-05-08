# Raspberry Pi Pico W Thermostat (MQTT)

**Author:** Ramiro Uffelmann

## Project Overview

A network‑connected thermostat built on a Raspberry Pi Pico 2 W using MicroPython and `mqtt_as`. It reads temperature and humidity from a DHT11 sensor, controls a relay in automatic or manual mode, and communicates securely over MQTT‑TLS. All configuration parameters persist across power cycles.

## Features

* **Automatic mode**: Relay toggles when temperature exceeds the setpoint.
* **Manual mode**: Relay toggled via MQTT command.
* **Periodic telemetry**: Publishes JSON (temperatura, humedad, setpoint, periodo, modo) at a configurable interval.
* **Remote configuration**: Subscribe to topics:

  * `<DEVICE_ID>/setpoint`
  * `<DEVICE_ID>/periodo`
  * `<DEVICE_ID>/modo`
  * `<DEVICE_ID>/rele` (manual relay control)
  * `<DEVICE_ID>/destello` (LED blink)
* **Non‑volatile storage**: setpoint, period, mode, relay state stored in `params.json` on flash.
* **Secure MQTT**: TLS using a provided certificate.

## Technologies

* **MicroPython** on Raspberry Pi Pico 2 W
* **asyncio** event loop
* **mqtt\_as** library (by: Peter Hinch)
* **DHT11** temperature/humidity sensor
* **Relay module** (5 V coil)
* **uJSON** for JSON handling

## Repository Structure

```
/main.py           # Application entry point
/settings.py       # Wi‑Fi and broker credentials
/README.md         # This documentation
```

## Hardware Wiring

| Component    | Pico 2 W Pin | Comments              |
| ------------ | ------------ | --------------------- |
| DHT11 Data   | GP16         | Use pull‑up if needed |
| Relay IN     | GP15         | Active‑high drive     |
| On‑board LED | `LED`        | Status / blink        |
| 3.3 V, GND   | 3V3, GND     | Power rails           |

> **Note:** Ensure your relay module is 5 V‑compatible.

## Setup & Deployment

1. **Prepare files**

   * Copy `main.py`, `settings.py`, `cert.pem` into the Pico's flash (main.py and settings.py can be uploaded using the MicroPico extension in Visual Studio Code, and the cert.pem file is usually already present on the board).
2. **Configure credentials** in `settings.py`:

   ```python
   SSID = "your_wifi_ssid"
   password = "your_wifi_password"
   BROKER = "mqtt.example.com"
   ```
3. **Upload CA certificate** as `/flash/cert.pem` (if not present on your board).
4. **Run**: Reset Pico; `main.py` starts automatically.
5. **Monitor**: Use `rshell` or serial REPL to view debug logs.

## MQTT Topics

Replace `<DEVICE_ID>` with the hex‑ID printed on startup.

* **Telemetry publish**: `<DEVICE_ID>`
* **Setpoint**: `<DEVICE_ID>/setpoint` (float)
* **Period**: `<DEVICE_ID>/periodo` (int seconds)
* **Mode**: `<DEVICE_ID>/modo` (0=auto, 1=manual)
* **Relay**: `<DEVICE_ID>/rele` (0=off, 1=on)
* **Blink LED**: `<DEVICE_ID>/destello`

## Customization

* Default parameters in `default_params` of `main.py`.
* Change sensor pin or relay pin in code as needed.
* To adapt non‑volatile storage, modify `PARAMS_FILE` or integrate a different storage module.

## Troubleshooting

* **No Wi‑Fi**: Check SSID/password, verify `cert.pem` matches broker CA.
* **Sensor errors**: Ensure correct wiring and adequate pull‑up resistor on DHT data line.
* **Relay chatter**: Confirm relay coil voltage compatibility.

## License

MIT License
