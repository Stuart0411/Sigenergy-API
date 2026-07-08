"""Sigenergy Home Assistant Integration

This is a custom integration for Home Assistant that provides:
- Auto-discovery of Sigenergy systems and devices
- Real-time monitoring of power flows and battery state
- Control of charging devices
- Support for multiple systems

For setup instructions, see README.md
For API documentation, visit: https://developer.sigencloud.com/user/api/document/17
"""

# Home Assistant Integration for Sigenergy

## Quick Start

1. **Install**: Copy `custom_components/sigenergy` to your Home Assistant `custom_components` folder
2. **Configure**: Go to Settings → Devices & Services → Create Integration → Search for "Sigenergy"
3. **Enter Credentials**: Provide your Sigenergy username/password
4. **Done**: Systems and devices will auto-discover

## What's Included

### Platforms
- **Sensors**: Power readings (W), battery SOC (%), energy (Wh)
- **Switches**: Charger on/off control
- **Binary Sensors**: System online status
- **Numbers**: Charging power limits

### Auto-Discovery
- Automatically finds all your Sigenergy systems
- Discovers devices within each system
- Creates entities for monitoring and control

### API Client
- Handles authentication (username/password or API key)
- Manages token refresh
- Provides methods for system queries and device control

### Data Coordinator
- Updates data every 5 minutes (configurable)
- Handles retries on failure
- Notifies all entities of data changes

## Key Files

| File | Purpose |
|------|---------|
| `__init__.py` | Integration setup and platform loading |
| `api.py` | Sigenergy API client with auth and requests |
| `config_flow.py` | User configuration and credential validation |
| `coordinator.py` | Periodic data fetching from API |
| `sensor.py` | Power and energy monitoring entities |
| `switch.py` | Charger on/off control |
| `binary_sensor.py` | System status entities |
| `number.py` | Charging power adjustment |
| `entity.py` | Base classes for all entities |
| `const.py` | Constants and configuration values |
| `manifest.json` | Integration metadata |
| `strings.json` | UI text and service definitions |

## Next Steps

1. **Customize API Endpoints**: Update endpoints in `api.py` based on actual Sigenergy API documentation
2. **Add Data Parsing**: Map Sigenergy API response fields to entity properties
3. **Implement Services**: Complete service handlers for charging control
4. **Add Diagnostics**: Implement diagnostic platform for debugging
5. **Write Tests**: Add tests for API client and entities
6. **Submit to HACS**: Publish integration to Home Assistant Community Store

## Documentation

- Full README: [README.md](./README.md)
- Sigenergy API: https://developer.sigencloud.com/user/api/document/17
- Home Assistant: https://www.home-assistant.io/
- Custom Components: https://developers.home-assistant.io/docs/creating_component_index
