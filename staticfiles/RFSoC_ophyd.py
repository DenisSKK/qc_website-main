import os
import io
import json
import threading
import time
from typing import List
import abc
import typing
import logging
from ophyd.log import config_ophyd_logging
# config_ophyd_logging(file='/tmp/ophyd.log', level='DEBUG')
from prettytable import PrettyTable
from log_ophyd import log_ophyd

import numpy as np
# from bec_utils import BECMessage, MessageEndpoints, bec_logger
from ophyd import Component as Cpt
from ophyd import Device, PositionerBase, Signal
from ophyd.status import wait as status_wait
from ophyd.utils import LimitError, ReadOnlyError

from ophyd.ophydobj import OphydObject

# import asyncio
from IPython.display import clear_output
from ssh import SSH
from create_json import import_json_file, save_list_to_json_file

def startupCheck(PATH):
    """
    The function `startupCheck` checks if a file exists and is readable, and returns True if it does.
    @param PATH - The `PATH` parameter is a string that represents the file path of the file you want to
    check.
    @returns a boolean value. If the file exists and is readable, it returns True. Otherwise, it returns
    False.
    """
    if os.path.isfile(PATH) and os.access(PATH, os.R_OK):
        # checks if file exists
        print ("File exists and is readable")
        return True
    else:
        print ("Either file is missing or need to install from the RFSoC")



logger = log_ophyd("rfsoc_log.txt",__name__)

DEFAULT_EPICSSIGNAL_VALUE = object()
class RFSoCCommunicationError(Exception):
    pass


class RFSoCError(Exception):
    pass

_type_map = {
    "number": (float, np.floating),
    "array": (np.ndarray, list, tuple),
    "string": (str,),
    "integer": (int, np.integer),
}

def data_shape(val):
    """Determine data-shape (dimensions)

    Returns
    -------
    list
        Empty list if val is number or string, otherwise
        ``list(np.ndarray.shape)``
    """
    if data_type(val) != "array":
        return []

    try:
        return list(val.shape)
    except AttributeError:
        return [len(val)]


def data_type(val):
    """Determine the JSON-friendly type name given a value

    Returns
    -------
    str
        One of {'number', 'integer', 'array', 'string'}

    Raises
    ------
    ValueError if the type is not recognized
    """
    bad_iterables = (str, bytes, dict)
    if isinstance(val, typing.Iterable) and not isinstance(val, bad_iterables):
        return "array"

    for json_type, py_types in _type_map.items():
        if isinstance(val, py_types):
            return json_type

    raise ValueError(
        f"Cannot determine the appropriate bluesky-friendly data type for "
        f"value {val} of Python type {type(val)}. "
        f"Supported types include: int, float, str, and iterables such as "
        f"list, tuple, np.ndarray, and so on."
    )

class RFSoCController(OphydObject): #On off laser similar to controller
    _controller_instances = {}
    _get_lists = ["laser1:ctl:wavelength-act", "laser1:scan:end","laser1:scan:frequency","laser1:scan:offset"]
    USER_ACCESS = [
        "set_laser","get_laser","off"
    ]
    SUB_CONNECTION_CHANGE = "connection_change"

    def __init__(
        self,
        *,
        host,
        username,
        password,
        name=None,
        port=22,
        attr_name="",
        parent=None,
        labels=None,
        kind=None,
    ):
        if not hasattr(self, "_initialized"):
            super().__init__(
                name=name, attr_name=attr_name, parent=parent, labels=labels, kind=kind
            )

            self._lock = threading.RLock()
            self.host = host
            self.port = port
            self._initialized = True
            self.username = username
            self.password = password
            self._initialize()

    def _initialize(self):
        # self._connected = False
        print(f"connecting to {self.host}")
        logger.info("The connection has already been established.")
        self.RFSoC = SSH(self.host,self.username, self.password)
        self.RFSoC.connect()
        self._connected = True
        self.name = "RFSoC"
        self.is_open = True
        self.config =None

    def check_config(self, source_file=None):
        """
        The function checks if a configuration file exists, and if not, it downloads it from a specified
        source file.
        @param source_file - The `source_file` parameter is the path to the JSON file that you want to
        download and import as the configuration file. If `source_file` is not provided or is set to
        `None`, the code will download the configuration file from the specified location
        (`/home/xilinx/jupyter_notebooks
        """
        if startupCheck("config.json"):
            self.config = import_json_file("config.json")
        else:
            if source_file==None:
                self.RFSoC.download_file(r"/home/xilinx/jupyter_notebooks/qick/qick_demos/config.json",r"config.json")
            else:
                self.RFSoC.download_file(rf"{source_file}",r"config.json")

            self.config = import_json_file("config.json")

    @property
    def connected(self):
        return self._connected

    def off(self):
        """
        The function closes the connection to the laser.
        """
        """Close the connection to the laser"""
        logger.info("The connection is already closed.")
        self.RFSoC.disconnect()
        self.connected = False

    def run_rfsoc(self):
        logger.info(f"run the RFSoC")
        self.RFSoC.transfer_file(r"config.json",r"/home/xilinx/jupyter_notebooks/qick/qick_demos/config.json")
        self.RFSoC.run_code("RFSoC")

    def show_config(self):
        if self.config!=None:
            print(json.dumps(self.config, indent = 3))

    def get_rfsoc_data(self):
        signals = {
            # "wide scan amplitude":{"value": self.dlc.laser1.wide_scan.amplitude.get()},
        }
        return signals

    def update_config(self, key, value):
        logger.debug(f"update the config")
        self.config[key] = value



    def describe(self) -> None:
        t = PrettyTable()
        t.title = f"{self.__class__.__name__} on {self.sock.host}:{self.sock.port}"
        t.field_names = [
            # "wide scan amplitude",
        ]
        t.add_row(
                    [
                        # self.widescan_amplitude(),
                    ]
                )
        print(t)

class RFSoCSignalBase(abc.ABC,Signal): #Similar to socketsignal
    SUB_SETPOINT = "setpoint"
    def __init__(self, signal_name, **kwargs):
        self.signal_name = signal_name
        super().__init__(**kwargs)
        self.dlc = self.parent.lasercontroller

    @abc.abstractmethod
    def _get(self):
        ...

    @abc.abstractmethod
    def _set(self, val):
        ...

    def get(self):
        self._readback = self._get()
        return self._readback

    def put(self, value):
        """Set the motor instance for a specified controller axis."""
        self._set(value)
        timestamp = time.time()
        old_value = self.get()
        VALUE = value
        super().put(value, timestamp=timestamp,force=True)
        self._run_subs(sub_type=self.SUB_SETPOINT, old_value=old_value,
                       value=VALUE, timestamp=self.timestamp)
    def describe(self):
        if self._readback is DEFAULT_EPICSSIGNAL_VALUE:
            val = self.get()
        else:
            val = self._readback
        return {
            self.name: {
                "source":self.dlc.name,
                "dtype": data_type(val),
                "shape":data_shape(val)
            }
        }

class RFSoCSignalRO(RFSoCSignalBase):
    def __init__(self, signal_name, **kwargs):
        super().__init__(signal_name, **kwargs)
        self._metadata["write_access"] = False

    # @threadlocked
    def _set(self):
        raise ReadOnlyError("Read-only signals cannot be set")

class RFSoCMainScanEnd(RFSoCSignalBase):
    # @threadlocked
    def _get(self):
        return self.dlc.scan_end()

    # @threadlocked
    def _set(self, val):
        logger.info("Main Scan end is set to "+str(val))
        self.dlc.scan_end_setter(val)



class RFSoCD(Device):
    # scan_end = Cpt(RFSoCMainScanEnd, signal_name="scan_end")
    def __init__(self, prefix,name, host, port=None, kind=None,configuration_attrs=None, parent=None,**kwargs):
        self.lasercontroller = RFSoCController(host=host,port=port)
        super().__init__(
            prefix=prefix,
            name=name,
            kind=kind,
            # read_attrs=read_attrs,
            configuration_attrs=configuration_attrs,
            parent=parent,
            **kwargs,
        )
        self.name = name

    def limit_wavelength(self):
        return self.low_limit_wavelength.get()
    def update_scan_end(self,val):
        self.scan_end.put(val)
    def update_scan_start(self,val):
        self.scan_start.put(val)
    def update_scan_offset(self,val):
        self.scan_offset.put(val)
    def update_scan_offset(self,val):
        self.scan_frequency.put(val)
    def update_ctl_wavelength_act(self,val):
        self.ctl_wavelength_act.put(val)
    def report_scan_end(self):
        return self.scan_end.get()
    def report_scan_start(self):
        return self.scan_start.get()
    def report_scan_offset(self):
        return self.scan_offset.get()
    def report_scan_frequency(self):
        return self.scan_frequency.get()
    def report_ctl_wavelength_act(self):
        return self.ctl_wavelength_act.get()

    def stage(self) -> List[object]:
        return super().stage()

    def unstage(self) -> List[object]:
        return super().unstage()

    def stop(self, *, success=False):
        self.controller.stop_all_axes()
        return super().stop(success=success)


if __name__ == "__main__":
    RSFOCD = RFSoCD(prefix="...",name="RSFOCD", host="129.129.131.153", password="xilinx", username="xilinx")
    RSFOCD.stage()
    print(RSFOCD.read())

    # print(RSFOCD.get())
    # print(RSFOCD.describe())

    RSFOCD.unstage()
