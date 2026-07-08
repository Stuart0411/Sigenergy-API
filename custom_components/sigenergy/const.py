"""Constants for the Sigenergy integration."""

DOMAIN = "sigenergy"

# API Configuration
SIGENERGY_API_BASE = "https://openapi-eu.sigencloud.com"
SIGENERGY_MQTT_BROKER = "mqtt.sigencloud.com"
SIGENERGY_MQTT_PORT = 1883
SIGENERGY_API_TIMEOUT = 30
SIGENERGY_TOKEN_EXPIRY = 43200  # 12 hours in seconds

# Regions
REGION_EU = "eu"
REGION_AP = "ap"
REGION_MEA = "mea"
REGION_CN = "cn"
REGION_ANZ = "anz"
REGION_LA = "la"
REGION_NA = "na"
REGION_JP = "jp"

REGION_URLS = {
	REGION_EU: "https://openapi-eu.sigencloud.com",
	REGION_AP: "https://openapi-apac.sigencloud.com",
	REGION_MEA: "https://openapi-eu.sigencloud.com",
	REGION_CN: "https://openapi-cn.sigencloud.com",
	REGION_ANZ: "https://openapi-aus.sigencloud.com",
	REGION_LA: "https://openapi-us.sigencloud.com",
	REGION_NA: "https://openapi-us.sigencloud.com",
	REGION_JP: "https://openapi-jp.sigencloud.com",
}

# Configuration keys
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_ACCOUNT_ID = "account_id"
CONF_API_KEY = "api_key"
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_REGION = "region"
CONF_USE_MQTT = "use_mqtt_realtime"
CONF_ENERGY_FLOW_INTERVAL = "energy_flow_interval"
CONF_SUMMARY_INTERVAL = "summary_interval"

# Platforms
PLATFORMS = ["sensor", "switch", "binary_sensor", "number"]

# Coordinator update interval (seconds)
SCAN_INTERVAL = 300  # Default MQTT/telemetry interval
ENERGY_FLOW_INTERVAL = 60  # Default energy flow endpoint interval (5-min API limit per device)
SUMMARY_INTERVAL = 300  # Default summary endpoint interval (5-min API limit per system)

# Device attributes
ATTR_SYSTEM_ID = "system_id"
ATTR_DEVICE_ID = "device_id"
ATTR_DEVICE_TYPE = "device_type"

# Service names
SERVICE_SET_CHARGING_PROFILE = "set_charging_profile"
SERVICE_START_CHARGING = "start_charging"
SERVICE_STOP_CHARGING = "stop_charging"

# Entity identifiers
ENTITY_SYSTEM_POWER = "system_power"
ENTITY_SYSTEM_SOC = "system_soc"
ENTITY_CHARGER_STATUS = "charger_status"
ENTITY_BATTERY_POWER = "battery_power"
ENTITY_GRID_POWER = "grid_power"
ENTITY_PV_POWER = "pv_power"
ENTITY_LOAD_POWER = "load_power"

# Device types
DEVICE_TYPE_SYSTEM = "system"
DEVICE_TYPE_CHARGER = "charger"
DEVICE_TYPE_BATTERY = "battery"
DEVICE_TYPE_INVERTER = "inverter"

# MQTT Topics for real-time data
MQTT_TOPIC_TELEMETRY = "openapi/subscription/period"
MQTT_TOPIC_SYSTEM_DATA = "openapi/subscription/change"
MQTT_TOPIC_ALARM = "openapi/subscription/alarm"

# REST API Endpoints
ENERGY_FLOW_ENDPOINT = "openapi/systems/{system_id}/energyFlow"  # Doc 36
SUMMARY_ENDPOINT = "openapi/systems/{system_id}/summary"  # Doc 35
