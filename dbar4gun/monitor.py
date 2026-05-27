import pyudev


def is_wiimote(device):
    """
    Robust Wiimote detection using kernel driver + sysfs chain.
    """
    try:
        dev = device

        while dev is not None:
            # Best signal: kernel driver binding
            if getattr(dev, "driver", None) == "wiimote":
                return True

            # Sometimes driver is on parent chain only
            if getattr(dev, "subsystem", None) == "hid" and getattr(dev, "driver", None) == "wiimote":
                return True

            dev = dev.parent

    except Exception:
        pass

    return False


class Monitor(object):
    def __init__(self, queue):
        self.queue = queue

        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context, source="udev")

    def _handle_device(self, action, device):
        hidraw_path = device.get("DEVNAME")
        if not hidraw_path:
            return

        self.queue.put([action, hidraw_path])

    def _first_scan(self):
        """
        Initial scan of already-connected devices.
        """
        for device in self.context.list_devices(subsystem="hidraw"):
            if not is_wiimote(device):
                continue

            self._handle_device("add", device)

    def run(self):
        self._first_scan()

        self.monitor.filter_by(subsystem="hidraw")

        for action, device in self.monitor:
            # only care about add/remove
            if action not in ("add", "remove"):
                continue

            if not is_wiimote(device):
                continue

            self._handle_device(action, device)
