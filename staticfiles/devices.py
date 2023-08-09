import ruamel.yaml
from SX199_ophyd import SX199Device
from ITC_ophyd import MercuryITCDevice
from caylar_magnet_ophyd import CaylarMagnet
from Toptica_ophyd import LaserToptica
from RFSoC_controller import RFSoC_controller
from SR830_ophyd import SR830Device

CONFIG_TO_CLASS_NAME = {
    "sx199": SX199Device,
    "itc": MercuryITCDevice,
    "caylar": CaylarMagnet,
    "toptica": LaserToptica,
    "rfsoc": RFSoC_controller,
    "sr830": SR830Device,
}


class DeviceManager:
    def __init__(self, config_file="config.yaml"):
        self.config_file = config_file
        self.devices = {}
        self.load_devices()

    def load_devices(self):
        yaml = ruamel.yaml.YAML()
        with open(self.config_file, "r") as f:
            config_data = yaml.load(f)

        for device_name, device_info in config_data["instruments"].items():
            device_class = CONFIG_TO_CLASS_NAME.get(device_name)
            if device_class:
                device = device_class()
                connected = device.is_connected()
                if connected:
                    self.devices[device_name] = device

    def get_device(self, device_name):
        return self.devices.get(device_name)

    def list_connected_devices(self):
        return [device_name for device_name, device in self.devices.items()]

    def list_off_devices(self):
        yaml = ruamel.yaml.YAML()
        with open(self.config_file, "r") as f:
            config_data = yaml.load(f)

        all_device_names = config_data["instruments"].keys()
        off_devices = [device_name for device_name in all_device_names if device_name not in self.devices]

        return off_devices

    def reconnect_device(self, device_name):
        device_class = CONFIG_TO_CLASS_NAME.get(device_name)
        if device_class:
            device = device_class()
            connected = device.is_connected()
            if connected:
                self.devices[device_name] = device
                return f"Device {device_name} reconnected successfully."
            else:
                return f"Device {device_name} could not be reconnected."
        else:
            return f"Device class for {device_name} not found."


if __name__ == "__main__":
    device_manager = DeviceManager()
