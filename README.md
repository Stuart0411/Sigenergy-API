# Sigenergy Home Assistant Integration

A custom Home Assistant integration for Sigenergy energy management systems. This integration provides auto-discovery of systems and devices, real-time monitoring of power flows, battery state of charge, and control capabilities for charging devices.

## Features

- **Auto-Discovery**: Automatically discovers all Sigenergy systems and devices associated with your account
- **Real-time Monitoring**: 
  - System total power
  - Battery state of charge (SOC)
  - Battery power input/output
  - Grid power import/export
  - PV generation power
  - Load power consumption
- **Real-time MQTT Updates**: 
  - Periodic telemetry data (default 5-minute intervals) via MQTT push
  - Immediate system data changes (battery capacity, max charge/discharge power)
  - Alarm notifications with severity levels
- **Device Control**:
  - **REST API Energy Monitoring**:
    - Energy flow data (PV, grid, EV, load, heat pump, battery power)
    - Power generation statistics (daily, monthly, annual, lifetime)
    - Environmental impact metrics (CO₂, coal, trees equivalent)
  - **Device Control**:
  - Start/stop charging
  - Set maximum charging power
  - Configure charging profiles
- **Multi-System Support**: Monitor and control multiple Sigenergy systems from a single Home Assistant instance
- **OAuth2 Authentication**: Support for secure token-based authentication with automatic token refresh

## Installation

### Prerequisites

- Home Assistant 2024.1.0 or later
- Sigenergy API credentials (username and password or API key)

### Manual Installation

1. Copy the `custom_components/sigenergy` directory to your Home Assistant `custom_components` folder:
   ```
   ~/.homeassistant/custom_components/sigenergy/
   ```

2. Restart Home Assistant

3. Go to **Settings** → **Devices & Services** → **Create Automation** and search for "Sigenergy"

### HACS Installation

1. Add this repository to HACS (if published)
2. Search for "Sigenergy" in HACS
3. Click Install
4. Restart Home Assistant

## Configuration

### Setup via UI

1. Go to **Settings** → **Devices & Services** → **Integrations**
2. Click **Create Integration** and search for "Sigenergy"
3. Enter your credentials:
   - **Username**: Your Sigenergy account username (required)
   - **Password**: Your Sigenergy account password (required)
   - **Account ID** (optional): Specific account ID if you have multiple accounts
   - **API Key** (optional): API key for token-based authentication
   - **Client ID** (optional): OAuth2 client ID for service-to-service authentication
   - **Client Secret** (optional): OAuth2 client secret for token-based auth

4. Click **Submit**

The integration will automatically:
- Authenticate with Sigenergy API using OAuth2 or basic auth
- Discover all systems associated with your account
- Discover all devices in each system
- Create appropriate entities for monitoring and control
- Subscribe to real-time MQTT data streams (telemetry, system data, alarms)

## Supported Platforms

- **Sensor**: Power measurements (W), state of charge (%), energy (Wh)
- **Switch**: Charger on/off control
- **Binary Sensor**: System online status, device availability
- **Number**: Charging power limits and control


## Real-Time Data Sources

The integration combines multiple data sources for comprehensive monitoring:

### MQTT Real-Time Subscriptions (Push)
- Telemetry data (periodic, default 5-minute intervals)
- System data changes (immediate on change)
- Alarm notifications (immediate on alarm)

### REST API Endpoints (Pull)
- **Energy Flow** (`GET /openapi/systems/{system_id}/energyFlow`) - Real-time power flows
  - PV power, Grid power, EV power, Load power, Heat pump power, Battery power/SOC
  - Rate limit: Once per 5 minutes per system
  - Default poll interval: 60 seconds

- **System Summary** (`GET /openapi/systems/{system_id}/summary`) - Generation statistics
  - Daily, monthly, annual, lifetime power generation
  - Environmental impact: CO₂ reduction, coal saved, trees equivalent
  - Rate limit: Once per 5 minutes per system
  - Default poll interval: 300 seconds
  - **Energy Flow Interval** (optional): Polling interval for energy flow data in seconds (default: 60)
  - **Summary Interval** (optional): Polling interval for summary data in seconds (default: 300)
- Poll REST endpoints for energy flow and summary data at configured intervals
## API Reference

This integration uses the Sigenergy API v1. For complete API documentation, see:
https://developer.sigencloud.com/user/api/document/17

### Authentication

The integration supports two authentication methods:

1. **Username/Password**: Standard credential-based authentication
2. **API Key**: Token-based authentication for programmatic access

### Endpoints Used

- `GET /systems` - List all systems
- `GET /systems/{system_id}` - Get system details
- `GET /systems/{system_id}/devices` - List devices in system
- `GET /systems/{system_id}/devices/{device_id}/data` - Get device real-time data
- `POST /systems/{system_id}/devices/{device_id}/command` - Send commands to devices
- `GET /openapi/systems/{system_id}/energyFlow` - Real-time energy flow (Doc 36)
- `GET /openapi/systems/{system_id}/summary` - Power generation summary (Doc 35)

### MQTT Topics for Real-Time Data

- `openapi/subscription/period` - Periodic telemetry subscription (default 5-minute interval)
- `openapi/subscription/change` - System data changes subscription (real-time on change)
- `openapi/subscription/alarm` - Alarm notifications subscription (immediate on alarm)

## Services

### `sigenergy.set_charging_profile`

Set the charging profile for a charger device.

**Parameters**:
- `system_id` (string): The system ID
- `device_id` (string): The charger device ID
- `max_power` (number): Maximum charging power in watts

### `sigenergy.start_charging`

Start charging on a specific device.

**Parameters**:
- `system_id` (string): The system ID
- `device_id` (string): The charger device ID

### `sigenergy.stop_charging`

Stop charging on a specific device.

**Parameters**:
- `system_id` (string): The system ID
- `device_id` (string): The charger device ID

## Example Automations

### Auto-stop charging when battery is full

```yaml
automation:
  - alias: "Stop charging when battery full"
    trigger:
      platform: numeric_state
      entity_id: sensor.system_soc
      above: 95
    action:
      service: sigenergy.stop_charging
      data:
        system_id: "system_123"
        device_id: "charger_456"
```

### Limit charging during peak hours

```yaml
automation:
  - alias: "Reduce charging during peak hours"
    trigger:
      platform: time
      at: "17:00:00"
    action:
      service: sigenergy.set_charging_profile
      data:
        system_id: "system_123"
        device_id: "charger_456"
        max_power: 5000
```

## Authentication Methods

### Method 1: Username & Password (Basic Auth)
- Simplest setup
- Uses resource owner password credentials grant
- Token automatically refreshed (12-hour expiry)

### Method 2: OAuth2 Client Credentials
- More secure for service-to-service integration
- Requires client_id and client_secret from Sigenergy
- Recommended for production deployments
- Automatic token management with 12-hour expiry

### Method 3: API Key
- Legacy authentication method
- Can be used as alternative to password-based auth
- Useful for quick testing

**Recommended**: Use OAuth2 client credentials for production systems. Contact Sigenergy to generate client credentials.

## Real-Time Data Updates

This integration supports **real-time MQTT data subscriptions** for immediate updates:

### Telemetry Data (Periodic)
- **Topic**: `openapi/subscription/period`
- **Default Interval**: 5 minutes
- **Data Includes**: Power readings, energy metrics, device status
- **Update Frequency**: Periodic push from Sigenergy servers
   # Integration setup
├── api.py                   # Sigenergy API client with OAuth2 & MQTT support
├── config_flow.py           # Configuration flow
├── const.py                 # Constants & MQTT topics
├── coordinator.py           # Data update coordinator with real-time callbacks
├── entity.py                # Base entity classes
├── sensor.py                # Sensor platform
├── switch.py                # Switch platform
├── binary_sensor.py         # Binary sensor platform
├── number.py                # Number platform
├── manifest.json            # Integration metadata
└── strings.json             # Localized strings
```

### Testing

To test the integration locally:

1. Copy the `custom_components/sigenergy` directory to your Home Assistant test instance
2. Restart Home Assistant
3. Go through the setup flow
4. Check logs and entity states for real-time updates

### Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guide
- All functions have docstrings
- Changes are tested before submission
- OAuth2 and MQTT functionality is preserved
- Wait for the first update cycle (default: 5 minutes)
- Check Home Assistant logs for errors
- Ensure you have devices in your Sigenergy system
- Verify your account has access to these devices
- Make sure MQTT subscriptions are configured (contact Sigenergy support)

### Real-time data not updating

- Verify MQTT subscriptions are enabled through Sigenergy support
- Check if Home Assistant webhook endpoint is accessible from Sigenergy servers
- Review logs for subscription errors
- Ensure firewall allows incoming MQTT connections

## Development

### Project Structure

```
custom_components/sigenergy/
├── __init__.py           # Integration setup
├── api.py                # Sigenergy API client
├── config_flow.py        # Configuration flow
├── const.py              # Constants
├── coordinator.py        # Data update coordinator
├── entity.py             # Base entity classes
├── sensor.py             # Sensor platform
├── switch.py             # Switch platform
├── binary_sensor.py      # Binary sensor platform
├── number.py             # Number platform
├── manifest.json         # Integration metadata
└── strings.json          # Localized strings
```

### Testing

To test the integration locally:

1. Copy the `custom_components/sigenergy` directory to your Home Assistant test instance
2. Restart Home Assistant
3. Go through the setup flow
4. Check logs and entity states

### Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 style guide
- Real-time MQTT subscriptions for telemetry, system data, and alarms
- Charger control (start/stop)
- Charging power adjustment
- Support for multiple systems
- OAuth2 and basic authentication support
- Automatic token refresh and management
## License

This integration is provided as-is for use with Home Assistant.

## Support

For issues or questions:
1. Check the [Sigenergy API documentation](https://developer.sigencloud.com/user/api/document/17)
2. Review Home Assistant logs for error messages
3. Report issues on the project repository

## Changelog

### Version 0.1.0

- Initial release
- Auto-discovery of systems and devices
- Real-time monitoring of power flows and battery state
- Charger control (start/stop)
- Charging power adjustment
- Support for multiple systems
Real-time MQTT subscriptions for telemetry, system data, and alarms
- Charger control (start/stop)
- Charging power adjustment
- Support for multiple systems
- OAuth2 and basic authentication support
- Automatic token refresh and management