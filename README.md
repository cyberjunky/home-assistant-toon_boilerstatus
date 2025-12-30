[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
![Project Maintenance][maintenance-shield]

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

# Omnik Inverter Custom Integration

A Home Assistant custom integration that monitors older Omnik Solar inverters via the network using special TCP packets. Get real-time insights into production, yield, and more.

## Supported Features

Monitor your Omnik Solar inverter with these sensors:

- **Status** - Online/Offline status
- **Actual Power** - Current power output (W)
- **Energy Today** - Energy generated today (kWh)
- **Energy Total** - Lifetime energy generated (kWh)
- **Hours Total** - Total operating hours
- **Inverter Serial Number** - Device serial number
- **Temperature** - Inverter temperature (°C)
- **DC Input Voltage** - PV panel voltage (V)
- **DC Input Current** - PV panel current (A)
- **AC Output Voltage** - Grid voltage (V)
- **AC Output Current** - Grid current (A)
- **AC Output Frequency** - Grid frequency (Hz)
- **AC Output Power** - Grid power output (W)

All sensors are created by default and grouped under a single device for easy management.

## Requirements

- **Omnik Solar Inverter** with network connectivity
- **Inverter IP address** accessible from Home Assistant
- **Inverter serial number** (found on the device label)
- **TCP port** (usually 8899)

## Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=cyberjunky&repository=home-assistant-omnik_inverter&category=integration)

Alternatively:

1. Install [HACS](https://hacs.xyz) if not already installed
2. Search for "Omnik Inverter" in HACS
3. Click **Download**
4. Restart Home Assistant
5. Add via Settings → Devices & Services

### Manual Installation

1. Copy the `custom_components/omnik_inverter` folder to your `<config>/custom_components/` directory
2. Restart Home Assistant
3. Add via Settings → Devices & Services

## Configuration

### Adding the Integration

1. Navigate to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **"Omnik Inverter"**
4. Enter your configuration:
   - **Host**: Your inverter's IP address (e.g., `192.168.2.129`)
   - **Port**: Default is `8899`
   - **Serial Number**: Your inverter's serial number (e.g., `602696253`)
   - **Name**: Friendly name prefix (default: "Omnik")
   - **Update Interval**: Seconds between updates (default: `60`)

The integration validates your connection and creates all sensors automatically. Disable sensors you don't need via **Settings** → **Devices & Services** → **Omnik Inverter** → click a sensor → cogwheel icon → "Enable entity" toggle.

### Modifying Settings

Change integration settings without restarting Home Assistant:

1. Go to **Settings** → **Devices & Services**
2. Find **Omnik Inverter**
3. Click **Configure** icon
4. Modify the scan interval
5. Click **Submit**

Changes apply immediately. To enable/disable individual sensors, click on the sensor entity and toggle "Enable entity".

## Advanced Usage

### Automation Example

Monitor inverter status changes:

```yaml
automation:
  - alias: "Alert Inverter Offline"
    trigger:
      - platform: state
        entity_id: sensor.omnik_status
        to: "Offline"
        for:
          minutes: 5
    action:
      - service: notify.mobile_app
        data:
          message: "Warning: Omnik Inverter is offline!"
```

Monitor daily energy production:

```yaml
automation:
  - alias: "Daily Solar Report"
    trigger:
      - platform: time
        at: "21:00:00"
    action:
      - service: notify.mobile_app
        data:
          message: >
            Today's solar production: {{ states('sensor.omnik_energy_today') }} kWh
            Total production: {{ states('sensor.omnik_energy_total') }} kWh
```

## Troubleshooting

### Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.omnik_inverter: debug
```

Alternatively, enable debug logging via the UI in **Settings** → **Devices & Services** → **Omnik Inverter** → **Enable debug logging**:

![Enable Debug Logging](screenshots/enabledebug.png)

Then perform any steps to reproduce the issue and disable debug logging again. It will download the relevant log file automatically.

### Common Issues

**Integration won't connect:**

- Verify your inverter's IP address is correct
- Ensure the inverter is powered on and connected to the network
- Check that port 8899 is accessible (try `nc -zv YOUR_IP 8899` from command line)
- Verify the serial number matches your inverter

**Sensors show "Unavailable":**

- The inverter may be offline (at night or when there's no sunlight)
- Check the Status sensor - "Offline" is normal when the inverter is not producing power
- Verify network connectivity to the inverter

**Old YAML config not migrating:**

- Check Home Assistant logs for import errors
- Verify the YAML syntax is correct
- Manually add via UI if automatic import fails

## Development

Quick-start (from project root):

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements_lint.txt
./scripts/lint    # runs pre-commit + vulture
# or: ruff check .
# to auto-fix: ruff check . --fix
```

## 💖 Support This Project

If you find this integration useful, please consider supporting its continued development:

### 🌟 Ways to Support

- **⭐ Star this repository** - Help others discover the project
- **💰 Financial Support** - Contribute to development and hosting costs
- **🐛 Report Issues** - Help improve stability and compatibility
- **📖 Spread the Word** - Share with other solar enthusiasts

### 💳 Financial Support Options

[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg?style=for-the-badge&logo=paypal)](https://www.paypal.me/cyberjunkynl/)
[![Sponsor on GitHub](https://img.shields.io/badge/Sponsor-GitHub-red.svg?style=for-the-badge&logo=github)](https://github.com/sponsors/cyberjunky)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

[releases-shield]: https://img.shields.io/github/release/cyberjunky/home-assistant-omnik_inverter.svg?style=for-the-badge
[releases]: https://github.com/cyberjunky/home-assistant-omnik_inverter/releases
[commits-shield]: https://img.shields.io/github/commit-activity/y/cyberjunky/home-assistant-omnik_inverter.svg?style=for-the-badge
[commits]: https://github.com/cyberjunky/home-assistant-omnik_inverter/commits/main
[license-shield]: https://img.shields.io/github/license/cyberjunky/home-assistant-omnik_inverter.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-cyberjunky-blue.svg?style=for-the-badge
