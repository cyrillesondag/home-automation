## Home Automation Project

#### Install

pip install -r requirements.txt

#### Details

#### scan.py : 
Scan BT device

### service.py : 
Pool temperature and humidity values form Xiami's BT Sensor.

Values are saved in influxdb database.

#### Config.ini

[influxdb]

| Key      | Exemple          | Description          |
|---       |---               |---                   |
| host     | http://localhost | Influxdb server url  |
| port     | 8086             | Influxdb server port |
| database | my_dbname        | Target database name |

[sensor:*]

| Key      | Exemple           | Description         |
|---       |---                |---                  |
| address  | 40:65:a8:dd:37:a3 | Sensor MAC address  |
