import argparse
import configparser
from datetime import datetime
from typing import List
import http.client

from bluepy.btle import Peripheral, DefaultDelegate, BTLEDisconnectError


class SensorValues:
    ts: datetime = None
    humidity: str = None
    temperature: str = None
    label: str = None

    def __init__(self, label: str, timestamp: datetime, temperature: str, humidity: str):
        self.label = label
        self.ts = timestamp
        self.temperature = temperature
        self.humidity = humidity

    def __str__(self):
        return "label=" + str(self.label) \
               + ", timestamp=" + str(self.ts) \
               + ", temperature=" + str(self.temperature) \
               + ", humidity=" + str(self.humidity)

    def to_nano(self) -> str:
        return '{:.0f}000'.format(self.ts.timestamp() * 1000000)


class ValueDelegate(DefaultDelegate):
    def __init__(self, label: str, results: List[SensorValues]):
        DefaultDelegate.__init__(self)
        self.label = label
        self.results = results

    def handleNotification(self, cHandle, data):
        if cHandle == 14:
            value = SensorValues(
                label=self.label,
                timestamp=datetime.now(),
                temperature=data[2:6].decode('utf8'),
                humidity=data[9:13].decode('utf8')
            )
            if self.results is not None:
                self.results.append(value)
            else:
                print("Failed to append result")


class BluetoothPoller:
    _DATA_MODE_LISTEN = bytes([0x01, 0x00])

    def __init__(self, address: str, label: str, results: List[SensorValues], iface: int):
        self.peripheral = Peripheral(deviceAddr=address, iface=iface)
        self.peripheral.withDelegate(ValueDelegate(label=label, results=results))

    def wait_for_notification(self, handle: int, timeout=1.0):
        self.peripheral.writeCharacteristic(handle, BluetoothPoller._DATA_MODE_LISTEN)
        return self.peripheral.waitForNotifications(timeout)

    def disconnect(self):
        self.peripheral.disconnect()


def read_config(path) -> dict:
    cfg = configparser.ConfigParser()
    config_map = {}

    cfg.read(path)
    for section in cfg.sections():
        meta = {}

        for key, value in cfg.items(section):
            meta[key] = value

        config_map[section] = meta

    return config_map


def parse_args():
    parser = argparse.ArgumentParser(description='Read bluetooth BT sensors')
    parser.add_argument('--config', nargs=1, help="Config file location", default='config.ini')
    parser.add_argument('--iface', nargs=1, help="Config file location", type=int, default=1)
    parser.add_argument('--timeout', nargs=1, help='connection timeout', type=int, default=1.0)
    return parser.parse_args()


def main():
    cmd_args = parse_args()
    config = read_config(cmd_args.config)
    results = []

    for deviceName in filter(lambda k: k.startswith('sensor:'), config.keys()):
        device_attrs = config.get(deviceName)

        try:
            device = BluetoothPoller(
                address=device_attrs['address'],
                label=deviceName[7:],
                results=results,
                iface=cmd_args.iface
            )

            if not device.wait_for_notification(0x0010, cmd_args.timeout):
                print("Failed to get result form %s" % deviceName)

            device.disconnect()

        except BTLEDisconnectError:
            print("Failed to connect to %s" % deviceName)

    measurements = []
    for result in results:
        measurements.append(
            "temperature,label={} value={} {}\n".format(result.label, result.temperature, result.to_nano()))
        measurements.append(
            "humidity,label={} value={} {}\n".format(result.label, result.humidity, result.to_nano()))

    influxdb = config.get('influxdb')
    if influxdb is None:
        print(measurements)
    else:
        comm = http.client.HTTPConnection(host=influxdb['host'], port=int(influxdb['port']))
        comm.request(
            method="POST",
            url='/write?db=' + influxdb['database'],
            body=''.join(measurements),
            headers={'Content-Type': 'application/octet-stream'}
        )

        response = comm.getresponse()
        if response.status >= 300:
            print(response.read())

        comm.close()


if __name__ == "__main__":
    main()
