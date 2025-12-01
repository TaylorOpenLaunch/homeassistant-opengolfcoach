# NOVA by Open Launch - Home Assistant Integration

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=OpenLaunchLabs&repository=homeassistant-nova&category=integration)

A Home Assistant HACS integration for NOVA golf launch monitors by Open Launch. Connects to your device via WebSocket and exposes shot data as sensor entities. Supports automatic discovery via SSDP.

## Features

- **Automatic Discovery**: Devices are automatically discovered via SSDP (UPnP)
- **WebSocket Connection**: Real-time data streaming from your launch monitor
- **Shot Data Sensors**: Ball speed, launch angles, spin rate, and more
- **Status Sensors**: Device uptime, firmware version, shot count
- **Auto-Reconnect**: Automatically reconnects if connection is lost
- **HACS Compatible**: Easy installation via Home Assistant Community Store

## Sensors

### Shot Data (updated on each shot)
| Sensor | Unit | Description |
|--------|------|-------------|
| Ball Speed | m/s | Ball velocity at launch (1 decimal) |
| Vertical Launch Angle | ° | Launch angle (up/down, 1 decimal) |
| Horizontal Launch Angle | ° | Launch angle (left/right, 1 decimal) |
| Total Spin | rpm | Ball spin rate (whole number) |
| Spin Axis | ° | Spin axis tilt (whole number) |
| Shot Number | - | Current shot count |
| Last Shot | - | Time since last shot |

### Status Data (updated periodically)
| Sensor | Unit | Description |
|--------|------|-------------|
| Uptime | s | Device uptime (whole seconds) |

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots in the top right corner
3. Select "Custom repositories"
4. Add this repository URL and select "Integration" as the category
5. Click "Add"
6. Find "NOVA by Open Launch" in HACS and click "Download"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/nova_by_openlaunch` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

### Automatic Discovery (Recommended)

1. Ensure your NOVA device is powered on and connected to your network
2. Home Assistant will automatically discover the device via SSDP
3. Go to Settings → Devices & Services
4. You should see a notification about the discovered device
5. Click "Configure" and confirm the device name

### Manual Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "NOVA by Open Launch"
4. Enter your device details:
   - **Name**: A friendly name for your device
   - **Host**: IP address of your launch monitor
   - **Port**: WebSocket port (default: 2920)

## Protocol

This integration uses a custom WebSocket + SSDP protocol.

### SSDP Discovery

The device responds to SSDP M-SEARCH requests with:
- **ST**: `urn:openlaunch:service:websocket:1`
- **LOCATION**: WebSocket server URL (e.g., `http://192.168.1.100:2920/`)
- **X-FRIENDLY-NAME**: Device display name
- **X-MANUFACTURER**: "Open Launch"
- **X-MODEL**: "NOVA"

### WebSocket Messages

**Shot Message** (sent when a shot is taken):
```json
{
  "type": "shot",
  "shot_number": 1,
  "timestamp_ns": 1764477382748215552,
  "ball_speed_meters_per_second": 34.37,
  "vertical_launch_angle_degrees": 7.5,
  "horizontal_launch_angle_degrees": -11.8,
  "total_spin_rpm": 1684.2,
  "spin_axis_degrees": -3.7
}
```

**Status Message** (sent periodically):
```json
{
  "type": "status",
  "uptime_seconds": 3512,
  "firmware_version": "0.1.0",
  "shot_count": 5
}
```

## Troubleshooting

### Device not discovered
- Ensure the device and Home Assistant are on the same network/subnet
- Check that multicast traffic (SSDP) is not blocked by your router
- Try manual configuration with the device's IP address

### Connection issues
- Verify the device is powered on and connected to the network
- Check Home Assistant logs for connection errors
- The integration will automatically retry every 10 seconds

### Sensors show "unavailable"
- This indicates the WebSocket connection is not active
- Check that the device is reachable
- Restart the integration from Settings → Devices & Services

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Credits

Developed for Open Launch NOVA launch monitors.
