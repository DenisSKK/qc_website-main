import os

import ruamel.yaml

from staticfiles.ITC_ophyd import MercuryITCDevice
from staticfiles.RFSoC_controller import RFSoC_controller
from staticfiles.SX199_ophyd import SX199Device
from staticfiles.Toptica_ophyd import LaserToptica
from staticfiles.XMLGenerator import xml_config_to_dict
from staticfiles.caylar_magnet_ophyd import CaylarMagnet


def construct_object():
    rfsoc_host = xml_config_to_dict("staticfiles/xilinx_host.xml")
    caylar_host = xml_config_to_dict("staticfiles/caylar.xml")
    itc_host = xml_config_to_dict("staticfiles/mercuryITC.xml")
    toptica_host = xml_config_to_dict("staticfiles/toptica.xml")
    LTDLC = LaserToptica(prefix="...", name="LTDLC", config_host=toptica_host)
    RFSoC = RFSoC_controller(config_host=rfsoc_host)
    magneticIR = CaylarMagnet("H", name="magneticIR", config_host=caylar_host)
    ITCD = MercuryITCDevice(prefix="...", name="ITCD", host="itc-optistat.psi.ch", config_host=itc_host)
    SX = SX199Device(name='sx199')
    return RFSoC, LTDLC, magneticIR, ITCD, SX


def construct_sx():
    # Read host and port from sx199.xml
    sx_xml_dict = xml_config_to_dict("staticfiles/sx199.xml")
    sx_host = sx_xml_dict['host']
    sx_port = sx_xml_dict['port']

    # Create path for config.yaml and yaml object
    config_file = os.path.expanduser("~/.instrbuilder/config.yaml")
    yaml = ruamel.yaml.YAML()

    # Read the config.yaml file
    with open(config_file, "r") as f:
        config_data = yaml.load(f)

    # Update the sx199 instrument address with sx_host and sx_port
    config_data["instruments"]["sx199"]["address"]["pyvisa"] = f"TCPIP::{sx_host}::{sx_port}::SOCKET"

    # Write the updated config_data back to the config.yaml file
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Now, construct and return the SX199Device instance
    SX = SX199Device(name='sx199')
    return SX


def construct_toptica():
    toptica_host = xml_config_to_dict("staticfiles/toptica.xml")
    LTDLC = LaserToptica(prefix="...", name="LTDLC", config_host=toptica_host)
    # LTDLC.try_connect()
    return LTDLC


def construct_rfsoc():
    rfsoc_host = xml_config_to_dict("staticfiles/xilinx_host.xml")
    RFSoC = RFSoC_controller(config_host=rfsoc_host)
    # RFSoC.try_connect()
    return RFSoC


def construct_caylar():
    caylar_host = xml_config_to_dict("staticfiles/caylar.xml")
    magneticIR = CaylarMagnet("H", name="magneticIR", config_host=caylar_host)
    # magneticIR.try_connect()
    return magneticIR


def construct_itc():
    itc_host = xml_config_to_dict("staticfiles/mercuryITC.xml")
    ITCD = MercuryITCDevice(prefix="...", name="ITCD", host="itc-optistat.psi.ch", config_host=itc_host)
    # ITCD.try_connect()
    return ITCD
