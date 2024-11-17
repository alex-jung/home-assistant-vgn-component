# "VGN Departures" integration

![Static Badge](https://img.shields.io/badge/code_owner-alex--jung-green)
![GitHub Release](https://img.shields.io/github/v/release/alex-jung/home-assistant-vgn-component)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/alex-jung/home-assistant-vgn-component/total)
![GitHub License](https://img.shields.io/github/license/alex-jung/home-assistant-vgn-component)

This integration provides information about next departure(s) for different transport types like Bus, Train, Tram etc. in [Verkehrsverbund Großraum Nürnberg (VGN)](http://www.vgn.de)

## Installation

### HACS Installation (recommended)

> HACS integration is ongoing!

Until it's done you can install the integration by adding this repository as a custom repository in HACS, and install as normal.

### Manual Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `vgn_departures`.
1. Download _all_ the files from the `custom_components/vgn_departures/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant

## Configuration
### Start integration dialog
The configuration of integration is made via Home Assistant GUI
1. Open _Settings/Devices & services_
2. Click on "Add Integration" button
3. Search for "VGN Departures"
4. Click on integration to start configuration dialog

### Configure a new station
Integration will load all available stations from GTFS data source. 
Start enter your station name in field to reduce the list and then choose a station you are interesting in from the list:\
![image](https://github.com/user-attachments/assets/e65635ec-2bc6-4eba-b73d-7b476bea1049)

In the next step you can select directions splitted by transport types and trip names:
![image](https://github.com/user-attachments/assets/96f402dd-a5c6-44d2-ad61-677adf38f7fe)

As result new sensor(s) will be created:
![image](https://github.com/user-attachments/assets/39ca6db8-8660-410d-9e2b-e4a92e055609)

### Reconfigure an entry
The directions you choosen in the [previous step](#Configure-a-new-station) can be reconfigured via GUI:
![image](https://github.com/user-attachments/assets/03864ffd-2420-4ca0-97e8-03d64f0189ae)

Here you can remove obsolete directions or add new by selection them in dialog.

## Usage in dashboard

### Example 1

### Example 2
