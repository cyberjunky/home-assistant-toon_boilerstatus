[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)  [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/cyberjunkynl/)

# Toon Boiler Status Sensor Component
This is a Custom Component for Home-Assistant (https://home-assistant.io) that reads and displays the boiler status values from a rooted Toon thermostat.

NOTE: This component only works with rooted Toon devices.
Toon thermostats are available in The Netherlands and Belgium.

More information about rooting your Toon can be found here:
[Eneco Toon as Domotica controller](http://www.domoticaforum.eu/viewforum.php?f=87)

You also need to install ToonStore and the BoilerStatus app, you can find information on how to install these on forum mentioned above.

## Installation

### HACS - Recommended
- Have [HACS](https://hacs.xyz) installed, this will allow you to easily manage and track updates.
- Search for 'Toon Boiler Status'.
- Click Install below the found integration.
- Configure using the configuration instructions below.
- Restart Home-Assistant.

### Manual
- Copy directory `custom_components/toon_boilerstatus` to your `<config dir>/custom_components` directory.
- Configure with config below.
- Restart Home-Assistant.

## Usage
To use this component in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry

sensor:
  - platform: toon_boilerstatus
    host: IP_ADDRESS
    port: 80
    scan_interval: 10
    resources:
      - boilersetpoint
      - boilerintemp
      - boilerouttemp
      - boilerpressure
      - boilermodulationlevel
      - roomtemp
      - roomtempsetpoint
```

Configuration variables:

- **host** (*Required*): The IP address on which the Toon can be reached.
- **port** (*Optional*): Port used by your Toon. (default = 80)
- **scan_interval** (*Optional*): Number of seconds between polls. (default = 10)
- **resources** (*Required*): This section tells the component which values to display and monitor.

By default the values are displayed as badges.

If you want them grouped instead of having the separate sensor badges, you can use these entries in your `groups.yaml`:

```yaml
# Example groups.yaml entry

Boiler Status:
  - sensor.toon_boiler_intemp
  - sensor.toon_boiler_outtemp
  - sensor.toon_boiler_setpoint
  - sensor.toon_boiler_pressure
  - sensor.toon_boiler_modulation
  - sensor.toon_room_temp
  - sensor.toon_room_temp_setpoint
```

## Screenshots

![alt text](https://github.com/cyberjunky/home-assistant-toon_boilerstatus/blob/master/screenshots/toon-boilerstatus.png?raw=true "Screenshot Toon Boiler Status")

## Donation
[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.me/cyberjunkynl/)
