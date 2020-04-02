from bluepy.btle import Scanner, DefaultDelegate


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print("Discovered device %s" % (dev.addr))
        elif isNewData:
            print("Received new data from %s" % (dev.addr))


def main():
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(10.0)
    for dev in devices:
        print("Iface %s Device %s (%s), RSSI=%d dB, connectable=%s" % (
            dev.iface, dev.addr, dev.addrType, dev.rssi, dev.connectable))
        for (adtype, desc, value) in dev.getScanData():
            print("  type= 0X%02x (%s) = %s" % (adtype, desc, value))
        print("---------------------------")


if __name__ == "__main__":
    main()
