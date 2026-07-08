# Sigenergy Home Assistant Integration

Custom Home Assistant integration for Sigenergy systems with system/device discovery, monitoring, and charger control.

## HACS Installation

1. Open HACS in Home Assistant.
2. Go to Integrations.
3. Add custom repository:
   - Repository: https://github.com/Stuart0411/Sigenergy-API
   - Category: Integration
4. Search for Sigenergy and install.
5. Restart Home Assistant.

## Manual Installation

1. Copy custom_components/sigenergy into your Home Assistant config directory under custom_components.
2. Restart Home Assistant.

## Configuration

1. Home Assistant: Settings -> Devices & Services -> Add Integration.
2. Search for Sigenergy.
3. Enter credentials:
   - username
   - password
   - account_id (optional)
   - api_key (optional)
   - client_id (optional)
   - client_secret (optional)
4. Optional frequency settings:
   - energy_flow_interval: polling interval for Doc 36 endpoint, minimum 300 seconds
   - summary_interval: polling interval for Doc 35 endpoint, minimum 300 seconds

## Data Sources

### MQTT Subscription APIs

- openapi/subscription/period
- openapi/subscription/change

### REST APIs

- GET openapi/systems/{systemId}/energyFlow (Doc 36)
- GET openapi/systems/{systemId}/summary (Doc 35)

## Entities

### Sensors

- system_power
- system_soc
- pv_power
- grid_power
- ev_power
- load_power
- battery_power
- daily_power_generation
- monthly_power_generation
- annual_power_generation
- lifetime_power_generation
- lifetime_co2_reduction
- lifetime_coal_saved
- lifetime_trees_planted

### Controls

- switch: charger_status
- number: charger_max_power
- binary_sensor: system_online

## Notes

- The Sigenergy endpoints in docs 35 and 36 are rate limited to once every 5 minutes per station.
- This integration enforces a minimum of 300 seconds for those polling intervals.

## API Documentation

- https://developer.sigencloud.com/user/api/document/17
- https://developer.sigencloud.com/user/api/document/35
- https://developer.sigencloud.com/user/api/document/36
