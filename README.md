# DVI Heatpump exporter

A prometheus exporter for DVI Heatpumps.
It's been develped against the newer propan gas based pumps AW-290 4, 7, 12, 16, 20 so your API response might vary.
The response can also vary depending on how your pump is configured.

## API documentation
[Officel API dokumentation fra DVI](https://ws.dvienergi.com/API/howto.php "DVI")


## Usage
```bash
python3 ./dvi_exporter.py -u <email> -p <password> -d <fabnr/device>
```

## Extend for more metrics
Simply extend the output_mapping.json file to add your required metrics

### Thanks to
Thanks to Lasse Kofoed for mapping API to human readable metrics
[LasseKofoed](https://github.com/LasseKofoed/DVI_HA "DVI_HAy")


Please star this repo if you used the code - thanks!
