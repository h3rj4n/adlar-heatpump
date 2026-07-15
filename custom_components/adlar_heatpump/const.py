"""Constants for Adlar Heatpump integration."""

from dataclasses import dataclass

from homeassistant.components.number import NumberDeviceClass, NumberEntityDescription
from homeassistant.components.number.const import NumberMode
from homeassistant.const import EntityCategory


DOMAIN = "adlar_heatpump"
DEFAULT_PORT = 502
DEFAULT_SLAVE = 1
DEFAULT_SCAN_INTERVAL = 60

# ─────────────────────────────────────────────
# Register definitions — adressen gebaseerd op HHI Modbus repo v2.2
# Schaling gevalideerd met Tuya app (Conrad, juni 2026):
#   R32 model stuurt temperaturen als directe graden (130 = 13°C), scale=1
#   NIET ×0.1 zoals HHI aangeeft (die werkt met een andere firmware/model)
# Each entry: (address, name, unit, device_class, scale, signed)
# ─────────────────────────────────────────────

SENSOR_REGISTERS = [
    # address, name, unit, device_class, scale, signed

    # --- Compressor & Ventilator ---
    (0x0040, "Compressor Running Frequency", "Hz",    "frequency",        1,     True),
    (0x0041, "Fan Running Speed",            "Hz",    "frequency",        1,     True),
    (0x0042, "EEV Open Step",                "P",     None,               1,     True),
    (0x0043, "EVI Valve Open Step",          "P",     None,               1,     True),

    # --- Elektrisch (compressor niveau) ---
    (0x0045, "AC Input Current",             "A",     "current",          0.1,   True),
    (0x0046, "Compressor Phase Current",     "A",     "current",          0.1,   True),

    # --- Temperaturen: adressen HHI v2.2, schaling ×1 (R32 model) ---
    (0x0047, "Compressor IPM Temp",          "°C",    "temperature",      1,     True),
    (0x0048, "High Pressure Saturation Temp","°C",    "temperature",      1,     True),
    (0x0049, "Low Pressure Saturation Temp", "°C",    "temperature",      1,     True),
    (0x004A, "Ambient Temp T1",              "°C",    "temperature",      1,     True),
    (0x004B, "Outer Coil Temp T2",           "°C",    "temperature",      1,     True),
    (0x004C, "Inner Coil Temp T3",           "°C",    "temperature",      1,     True),
    (0x004D, "Suction Temp T4",              "°C",    "temperature",      1,     True),
    (0x004E, "Exhaust Temp T5",              "°C",    "temperature",      1,     True),
    (0x004F, "Water Inlet Temp T6",          "°C",    "temperature",      1,     True),
    (0x0050, "Water Outlet Temp T7",         "°C",    "temperature",      1,     True),
    (0x0051, "Economizer Inlet Temp T8",     "°C",    "temperature",      1,     True),
    (0x0052, "Economizer Outlet Temp T9",    "°C",    "temperature",      1,     True),
    # 0x0053 = Device Tooling No — geen temperatuur, weglaten
    (0x0054, "DHW Tank Temp",                "°C",    "temperature",      1,     True),
    (0x0055, "Plate HX Exhaust Temp",        "°C",    "temperature",      1,     True),
    # 0x0056 = Drive Manufacturer Code — geen sensor, weglaten

    # --- Pomp & Flow ---
    (0x0057, "Water Pump Speed PWM",         "%",     None,               1,     True),
    (0x0058, "Water Flow",                   "L/min", "volume_flow_rate", 1,     True),
    (0x0059, "DHW Return Water Temp",        "°C",    "temperature",      1,     True),

    # --- Unit niveau elektrisch ---
    (0x005A, "Unit Input Voltage",           "V",     "voltage",          1,     True),
    (0x005B, "Unit Input Current",           "A",     "current",          0.01,  True),
    (0x005C, "Unit Input Power",             "kW",    "power",            0.01,  True),

    # --- DC Bus ---
    (0x0085, "DC Bus Inverter Voltage",      "V",     "voltage",          0.1,   True),
]

# Running status register (bitmask sensors)
STATUS_REGISTER = 0x0000
STATUS_BITS = [
    (0x0001, "Running Status: Refrigerant Recovery"),
    (0x0002, "Running Status: Primary Anti-freeze"),
    (0x0004, "Running Status: Secondary Anti-freeze"),
    (0x0008, "Running Status: Fault Alarm"),
    (0x0010, "Running Status: System Oil Return"),
    (0x0100, "Running Status: System Frosting"),
    (0x1000, "Running Status: Shutdown after Reaching Temp"),
    (0x2000, "Running Status: Shutdown after Unit Failure"),
    (0x4000, "Running Status: Unit Operation"),
    (0x8000, "Running Status: Unit Waiting for Operation"),
]

# Energy register: enkel 16-bit register, waarde direct in kWh (geen schaling)
ENERGY_REGISTER = 0x005D

@dataclass(frozen=True, kw_only=True)
class AdlarNumberDescription(NumberEntityDescription):
    """Describes an Adlar Heatpump writable number (setpoint) register.

    `key` doubles as the coordinator data-dict key (kept identical to the
    legacy display name so other platforms, e.g. climate.py, can keep
    reading `coordinator.data["Temp Set Cooling"]` unchanged).
    """

    address: int


# Writable number registers — setpoints (visible, no entity_category)
# plus P-code tuning parameters (entity_category=CONFIG).
NUMBER_DESCRIPTIONS: tuple[AdlarNumberDescription, ...] = (
    AdlarNumberDescription(
        key="Temp Set Cooling",
        translation_key="temp_set_cooling",
        address=0x0300,
        native_unit_of_measurement="°C",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=7,
        native_max_value=25,
        native_step=1,
        mode=NumberMode.BOX,
    ),
    AdlarNumberDescription(
        key="Temp Set Heating",
        translation_key="temp_set_heating",
        address=0x0301,
        native_unit_of_measurement="°C",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=15,
        native_max_value=60,
        native_step=1,
        mode=NumberMode.BOX,
    ),
    AdlarNumberDescription(
        key="Temp Set Floor Heating",
        translation_key="temp_set_floor_heating",
        address=0x0303,
        native_unit_of_measurement="°C",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=20,
        native_max_value=60,
        native_step=1,
        mode=NumberMode.BOX,
    ),
    AdlarNumberDescription(
        key="hysteresis_water_temp",
        translation_key="hysteresis_water_temp",
        address=0x011A,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement="°C",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=0,
        native_max_value=10,
        native_step=1,
        mode=NumberMode.SLIDER,
    ),
    AdlarNumberDescription(
        key="silent_mode_compressor_max_freq",
        translation_key="silent_mode_compressor_max_freq",
        address=0x0158,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement="Hz",
        device_class=NumberDeviceClass.FREQUENCY,
        native_min_value=20,
        native_max_value=70,
        native_step=1,
        mode=NumberMode.SLIDER,
    ),
    AdlarNumberDescription(
        key="silent_mode_fan_max_freq",
        translation_key="silent_mode_fan_max_freq",
        address=0x0159,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement="Hz",
        device_class=NumberDeviceClass.FREQUENCY,
        native_min_value=20,
        native_max_value=60,
        native_step=1,
        mode=NumberMode.SLIDER,
    ),
    AdlarNumberDescription(
        key="water_pump_speed_reg_temp_diff",
        translation_key="water_pump_speed_reg_temp_diff",
        address=0x0163,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement="°C",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=2,
        native_max_value=10,
        native_step=1,
        mode=NumberMode.SLIDER,
    ),
    AdlarNumberDescription(
        key="pwm_pump_min_speed",
        translation_key="pwm_pump_min_speed",
        address=0x0164,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement="%",
        native_min_value=20,
        native_max_value=80,
        native_step=1,
        mode=NumberMode.SLIDER,
    ),
    AdlarNumberDescription(
        key="water_pump_speed_reg_min_speed",
        translation_key="water_pump_speed_reg_min_speed",
        address=0x01A3,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement="L/min",
        device_class=NumberDeviceClass.VOLUME_FLOW_RATE,
        native_min_value=0,
        native_max_value=70,
        native_step=1,
        mode=NumberMode.SLIDER,
    ),
    AdlarNumberDescription(
        key="max_water_pump_speed",
        translation_key="max_water_pump_speed",
        address=0x0204,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement="%",
        native_min_value=50,
        native_max_value=99,
        native_step=1,
        mode=NumberMode.SLIDER,
    ),
    AdlarNumberDescription(
        key="water_pump_speed_constant_temp",
        translation_key="water_pump_speed_constant_temp",
        address=0x0205,
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement="%",
        native_min_value=20,
        native_max_value=99,
        native_step=1,
        mode=NumberMode.SLIDER,
    ),
)


# ON/OFF switch register
SWITCH_REGISTER = 0x0305

# Select registers (address, name, options_map)
CURVE_OPTIONS = {
    "Off": 0, "H1": 1, "H2": 2, "H3": 3, "H4": 4,
    "H5": 5, "H6": 6, "H7": 7, "H8": 8,
    "L1": 11, "L2": 12, "L3": 13, "L4": 14,
    "L5": 15, "L6": 16, "L7": 17, "L8": 18,
}

SELECT_REGISTERS = [
    (0x0304, "Mode", {
        "Cooling": 0, "Heating": 1, "Hot Water": 2,
        "Floor Heating": 3, "Hot Water + Cooling": 4,
        "Hot Water + Heating": 5, "Hot Water + Floor Heating": 7,
    }),
    (0x0307, "Running Mode", {
        "Standard Mode": 0, "Boost": 1, "Silent": 2,
    }),
    (0x0313, "Cooling Setting Curve",            CURVE_OPTIONS),
    (0x0314, "Heating Setting Curve",            CURVE_OPTIONS),
    (0x0316, "Underfloor Heating Setting Curve", CURVE_OPTIONS),
]

# ─────────────────────────────────────────────
# P119 Refrigerant Type register
# Adres: 0x0177, waarden: 1=R410A, 2=R32, 3=R290
# Bepaalt de temperatuurschaling:
#   R32  (waarde 2) → ×1  (raw waarde is directe °C)
#   R290 (waarde 3) → ×0.1 (raw waarde gedeeld door 10)
#   R410A (waarde 1) → ×1  (aanname, zelfde als R32)
# ─────────────────────────────────────────────
REFRIGERANT_REGISTER = 0x0177

REFRIGERANT_TYPES = {
    1: "R410A",
    2: "R32",
    3: "R290",
}

def get_temperature_scale(refrigerant_type: int) -> float:
    """Bepaal temperatuurschaling op basis van koelmiddeltype.
    R290 gebruikt ×0.1, alle andere ×1.
    """
    return 0.1 if refrigerant_type == 3 else 1.0
