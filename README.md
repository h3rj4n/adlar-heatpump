# Adlar Heatpump (Aurora II) — Home Assistant Integration

A HACS-compatible custom integration for the **Adlar Castra Aurora II** heat pump, communicating over **Modbus TCP** via an RS485-to-WiFi gateway.

No YAML required. All setup is done through the Home Assistant UI.

---

## Hardware setup

This integration was developed and tested with the following hardware:

- **JPX-3002** RS485 splitter (2 master / 1 slave):
  - **Slave port** → Modbus RS485 cable from the heat pump
  - **Master 1** → JAN module (original controller)
  - **Master 2** → Elfin EW11A (RS485 to WiFi/TCP bridge)
- The **Elfin EW11A** configured as TCP Server on port **502**
- Modbus slave ID of the heat pump: **1** (default)

Any RS485-to-Modbus-TCP bridge should work (Waveshare, USR-W610, etc.).

---

## Elfin EW11 configuration

**Serial Port Settings:**
- Baud Rate: `9600`
- Data Bit: `8`
- Stop Bit: `1`
- Parity: `None`
- Buffer Size: `1024`
- Gap Time: `100`

**Communication Settings:**
- Protocol: `TCP Server`
- Local Port: `502`

---

## Installation

### Via HACS (recommended)

1. Open **HACS → Integrations**
2. Click the three-dot menu → **Custom repositories**
3. Add this repository URL, category: **Integration**
4. Search for **Adlar Heatpump** and install
5. Restart Home Assistant

### Manual

Copy the `custom_components/adlar_heatpump/` folder into your HA `config/custom_components/` directory, then restart.

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Adlar Heatpump**
3. Enter:
   - **IP address** of your RS485-TCP gateway
   - **Port** (default `502`)
   - **Slave ID** (default `1`)
   - **Scan interval** in seconds (default `60`)

---

## Entities created

### Sensors (read-only)
| Name | Unit | Notes |
|---|---|---|
| Compressor Target Frequency | Hz | |
| Compressor Running Frequency | Hz | |
| Fan Running Speed | Hz | |
| EEV Open Step | P | |
| EVI Valve Open Step | P | |
| AC Input Current | A | Unit level, ×0.01 |
| Compressor Phase Current | A | Compressor level, ×0.1 |
| High Pressure Saturation Temp | °C | |
| Low Pressure Saturation Temp | °C | |
| Ambient Temp T1 | °C | |
| Outer Coil Temp T2 | °C | |
| Inner Coil Temp T3 | °C | |
| Suction Temp T4 | °C | |
| Exhaust Temp T5 | °C | |
| Water Inlet Temp T6 | °C | |
| Water Outlet Temp T7 | °C | |
| Economizer Inlet Temp T8 | °C | |
| Economizer Outlet Temp T9 | °C | |
| Plate HX Exhaust Temp | °C | |
| Water Pump Speed PWM | % | |
| Water Flow | L/min | |
| Unit Input Current | A | ×0.01 |
| Unit Input Power | kW | ×0.01 |
| Unit Power Consumption | kWh | 32-bit cumulative counter |
| DC Bus Inverter Voltage | V | ×0.1 |
| Thermal Power | kW | Calculated: flow × ΔT × 4.186 / 60 |
| COP | — | Calculated: thermal power / electrical power |
| Calculated Power | W | Calculated: voltage × current |

### Diagnose / Binary Sensors (running status)
| Name | Notes |
|---|---|
| Running Status: Refrigerant Recovery | |
| Running Status: Primary Anti-freeze | |
| Running Status: Secondary Anti-freeze | |
| Running Status: Fault Alarm | |
| Running Status: System Oil Return | |
| Running Status: System Frosting | |
| Running Status: Shutdown after Reaching Temp | |
| Running Status: Shutdown after Unit Failure | |
| Running Status: Unit Operation | |
| Running Status: Unit Waiting for Operation | |

### Controls
| Entity | Type | Options / Range |
|---|---|---|
| Adlar Heatpump | Climate | Heat / Cool / Heat+Cool / Off |
| Heatpump ON/OFF | Switch | on / off |
| Temp Set Cooling | Number | 7–25 °C |
| Temp Set Heating | Number | 15–60 °C |
| Temp Set Floor Heating | Number | 20–60 °C |
| Mode | Select | Cooling / Heating / Hot Water / Floor Heating / combinations |
| Running Mode | Select | Standard Mode / Boost / Silent |
| Cooling Setting Curve | Select | Off, H1–H8, L1–L8 |
| Heating Setting Curve | Select | Off, H1–H8, L1–L8 |
| Underfloor Heating Setting Curve | Select | Off, H1–H8, L1–L8 |

### Config
| Entity | Type | Options / Range |
|---|---|---|
| P26: Hysteresis Water Temp (Cool/Heat) | Number | 0–10 °C |
| P88: Silent mode - compressor maximum frequency | Number | 20–70 Hz |
| P89: Silent mode - fan motor maximum frequency | Number | 20–60 Hz |
| P99: Water pump speed regulation temperature differential | Number | 2–10 °C |
| P100: PWM pump minimum speed | Number | 20–80 % |
| P163: Water pump speed regulation - Minimum speed | Number | 0–70 L/min |
| P260: Maximum water pump speed | Number | 50–99 % |
| P261: Water pump speed - at constant temperature | Number | 20–99 % |

---

## Technical notes

### Registers not available on R32 model
The following registers always return 0 on the R32 (Aurora II) model and are excluded:
- `0x0044` AC Input Voltage
- `0x0047` Compressor IPM Temperature

### Scan interval
The default scan interval is 60 seconds. The scan interval can be adjusted in the configuration but must be at least 5 seconds.

## TODO

[x] Increase scan interval by grouping registers into single requests (35+ requests per poll cycle --> 8 requests per poll cycle)
[x] Update sensor data faster after value being changed in UI.
[ ] Different scan intervals for different register types (e.g. faster for control registers, slower for status registers).

---

## Disclaimer

This integration is community-developed and not affiliated with Adlår. Use at your own risk. Incorrect writes to control registers could affect heat pump operation. Always verify setpoints before applying changes.
