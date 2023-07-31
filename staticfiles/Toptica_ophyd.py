import functools
import threading
import time
from typing import List
import abc
import typing
from prettytable import PrettyTable
from .log_ophyd import log_ophyd

import numpy as np
# from bec_utils import BECMessage, MessageEndpoints, bec_logger
from ophyd import Component as Cpt
from ophyd import Device, PositionerBase, Signal
from ophyd.status import wait as status_wait
from ophyd.utils import LimitError, ReadOnlyError

from ophyd.ophydobj import OphydObject

import asyncio
from IPython.display import clear_output
from toptica.lasersdk.dlcpro.v2_0_3 import DLCpro, NetworkConnection

logger = log_ophyd("laser_log.txt",__name__)

DEFAULT_EPICSSIGNAL_VALUE = object()
class LaserCommunicationError(Exception):
    pass


class LaserError(Exception):
    pass


# def retry_once(fcn):
#     """Decorator to rerun a function in case a Laser communication error was raised. This may happen if the buffer was not empty."""

#     @functools.wraps(fcn)
#     def wrapper(self, *args, **kwargs):
#         try:
#             val = fcn(self, *args, **kwargs)
#         except (LaserCommunicationError, LaserError):
#             val = fcn(self, *args, **kwargs)
#         return val

#     return wrapper

# def threadlocked(fcn):
#     """Ensure that the thread acquires and releases the lock."""

#     @functools.wraps(fcn)
#     def wrapper(self, *args, **kwargs):
#         lock = self._lock if hasattr(self, "_lock") else self.dlc._lock
#         with lock:
#             return fcn(self, *args, **kwargs)

#     return wrapper

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

class LaserController(OphydObject): #On off laser similar to controller
    _controller_instances = {}
    _get_lists = ["laser1:ctl:wavelength-act", "laser1:scan:end","laser1:scan:frequency","laser1:scan:offset"]
    USER_ACCESS = [
        "set_laser","get_laser","off"
    ]
    SUB_CONNECTION_CHANGE = "connection_change"

    def __init__(
        self,
        *,
        name=None,
        host=None,
        port=None,
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
            self._initialize()

    def _initialize(self):
        # self._connected = False
        # self.try_connect()
        # self.name = "self.dlc.system_model.get()+self.dlc.system_type.get()+ self.dlc.serial_number.get()"
        # self._connected = True
        self._set_default_values()
        self.name = "DLCPro"

    def _set_default_values(self):
        # no. of axes controlled by each controller
        self._wavelength_act = 1550
        self._scan_end = 75
        self._scan_start = 50
        self._scan_freq = 10
        self._scan_offset = 70
        # self._wide_scan_amplitude = 120
        # self._wide_scan_offset = 1570

    def connected(self):
        return self._connected

    def try_connect(self):
        """
        The function `try_connect` attempts to establish a connection to a laser device and returns
        `True` if successful, `False` otherwise.
        @returns The function `try_connect` returns a boolean value. If the connection to the laser is
        successfully established, it returns `True`. Otherwise, if there is an exception or the
        connection cannot be established, it returns `False`.
        """
        print(f"connecting to {self.host}")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.dlc = DLCpro(NetworkConnection(self.host, timeout=30))
            self.dlc.open()
            loop.stop()

            self.is_open = True
            # self.name = "self.dlc.system_model.get()+self.dlc.system_type.get()+ self.dlc.serial_number.get()"
            self._connected = True
            print("Laser has been connected")
            logger.info("The connection has already been established.")
            return True
        except Exception as e:
            print(e)
            self.is_open = False
            self._connected = False
            print("Laser cannot be connected")
            return False

    def off(self):
        """
        The function closes the connection to the laser.
        """
        """Close the connection to the laser"""
        logger.info("The connection is already closed.")
        self.dlc.close()
        self.is_open = False

    def get_laser_data(self):
        """
        The function `get_laser_data` returns a dictionary of various laser data values.
        @returns a dictionary called "signals" which contains various laser data values.
        """
        signals = {
            # "wide scan amplitude":{"value": self.dlc.laser1.wide_scan.amplitude.get()},
            # "wide scan offset":{"value": self.dlc.laser1.wide_scan.offset.get()},
            # "wide scan remaining time":{"value": self.dlc.laser1.wide_scan.remaining_time.get()},
            "main scan end":{"value": self.dlc.laser1.scan.end.get()},
            "main scan start":{"value": self.dlc.laser1.scan.start.get()},
            "main scan frequency":{"value": self.dlc.laser1.scan.frequency.get()},
            "main scan offset":{"value": self.dlc.laser1.scan.offset.get()},
            "ctl wavelength":{"value":self.dlc.laser1.ctl.wavelength_act.get()},
            "voltage act":{"value":self.dlc.laser1.dl.pc.voltage_act.get()},
            "current act":{"value":self.dlc.laser1.dl.cc.current_act.get()},
            "emission":{"value":self.dlc.emission.get()},
            "system health":{"value":self.dlc.system_health.get()},
            "standby":{"value":self.dlc.standby.state.get()},
        }
        return signals
    def emission(self):
        """
        The function "emission" logs a debug message and returns the emission value from the "dlc"
        object.
        @returns The method `emission` is returning the value of `self.dlc.emission.get()`.
        """
        logger.debug(f"recv emission")
        return self.dlc.emission.get()
    def standby(self):
        """
        The function `standby` logs a debug message and returns the state of the standby mode.
        @returns The code is returning the value of `self.dlc.standby.state.get()`.
        """

        logger.debug(f"recv standby")
        return self.dlc.standby.state.get()
    def system_health(self):
        """
        The function retrieves the system health information from the dlc object.
        @returns The method `system_health` is returning the result of `self.dlc.system_health.get()`.
        """
        logger.debug(f"recv system health")
        return self.dlc.system_health.get()
    def current_act(self):
        """
        The function `current_act` retrieves the current activity of a laser.
        @returns The code is returning the value of `self.dlc.laser1.dl.cc.current_act.get()`.
        """
        logger.debug(f"recv current act")
        return self.dlc.laser1.dl.cc.current_act.get()
    def voltage_act(self):
        """
        The function "voltage_act" retrieves the current voltage value from a laser device.
        @returns The method `voltage_act` is returning the value of
        `self.dlc.laser1.dl.pc.voltage_act.get()`.
        """
        logger.debug(f"recv voltage act")
        return self.dlc.laser1.dl.pc.voltage_act.get()
    def current_act_setter(self,val):
        """
        The function sets the current value for a laser.
        @param val - The parameter "val" is the value that will be set for the current act.
        """

        logger.debug(f"recv current act")
        self.dlc.laser1.dl.cc.current_set.set(val)
    def voltage_act_setter(self,val):
        """
        The function sets the voltage of a laser.
        @param val - The parameter "val" is the value that will be set for the voltage act.
        """

        logger.debug(f"recv voltage act")
        self.dlc.laser1.dl.pc.voltage_set.set(val)
    def scan_end(self):
        """
        The function `scan_end` retrieves the value of the `end` attribute from the `scan` object of the
        `laser1` object in the `dlc` object and logs a debug message.
        @returns the value of `self.dlc.laser1.scan.end.get()`.
        """
        logger.debug(f"recv scan end")
        return self.dlc.laser1.scan.end.get()

    # @scan_end.setter
    def scan_end_setter(self,val):
        """
        The function sets the scan end value for a laser in a DLC object.
        @param val - The parameter "val" is the value that will be set for the scan end parameter.
        """
        logger.debug(f"set scan end")
        self.dlc.laser1.scan.end.set(val)
    def scan_start(self):
        """
        The function `scan_start` logs a debug message and returns the value of
        `self.dlc.laser1.scan.start.get()`.
        @returns the value of `self.dlc.laser1.scan.start.get()`.
        """
        logger.debug(f"recv scan start")
        return self.dlc.laser1.scan.start.get()

    # @scan_start.setter
    def scan_start_setter(self,val):
        """
        The function sets the scan start value for a laser.
        @param val - The parameter "val" is the value that will be set for the scan start.
        """
        logger.debug(f"set scan start")
        self.dlc.laser1.scan.start.set(val)
    def scan_frequency(self):
        """
        The function "scan_frequency" retrieves the scan frequency of laser1.
        @returns the scan frequency of laser1.
        """
        logger.debug(f"recv scan frequency")
        return self.dlc.laser1.scan.frequency.get()

    # @scan_frequency.setter
    def scan_frequency_setter(self,val):
        """
        The function sets the scan frequency for a laser.
        @param val - The parameter "val" is the value that will be set for the scan frequency.
        """
        logger.debug(f"set scan frequency")
        self.dlc.laser1.scan.frequency.set(val)

    def scan_offset(self):
        """
        The function `scan_offset` retrieves the scan offset value from the `dlc.laser1.scan.offset`
        attribute.
        @returns the value of `self.dlc.laser1.scan.offset.get()`.
        """
        logger.debug(f"recv scan offset")
        return self.dlc.laser1.scan.offset.get()

    # @scan_offset.setter
    def scan_offset_setter(self,val):
        """
        The function sets the scan offset value for a laser.
        @param val - The parameter "val" is the value that will be set for the scan offset.
        """
        logger.debug(f"set scan offset")
        self.dlc.laser1.scan.offset.set(val)

    def wavelength_act(self):
        """
        The function returns the current wavelength of a laser.
        @returns the value of `self.dlc.laser1.ctl.wavelength_act.get()`.
        """
        logger.debug(f"recv wavelength act")
        return self.dlc.laser1.ctl.wavelength_act.get()

    # @wavelength_act.setter
    def wavelength_act_setter(self,val):
        """
        The function sets the active wavelength for a laser control.
        @param val - The parameter "val" is the value that you want to set for the wavelength.
        """
        logger.debug(f"set wavelength act")
        self.dlc.laser1.ctl.wavelength_set.set(val)

    def describe(self) -> None:
        """
        The `describe` function prints a table with information about a specific object.
        """
        t = PrettyTable()
        t.title = f"{self.__class__.__name__} on {self.sock.host}:{self.sock.port}"
        t.field_names = [
            # "wide scan amplitude",
            # "wide scan offset",
            # "wide scan remaining time",
            "main scan end",
            "main scan start",
            "main scan frequency",
            "main scan offset",
            "wavelength act",
            "voltage act",
            "current act"
        ]
        t.add_row(
                    [
                        # self.widescan_amplitude(),
                        # self.widescan_offset(),
                        # self.widescan_remaining_time(),
                        self.scan_end(),
                        self.scan_start(),
                        self.scan_frequency(),
                        self.scan_offset(),
                        self.wavelength_act(),
                        self.voltage_act(),
                        self.current_act(),
                        self.emission(),
                        self.system_health(),
                    ]
                )
        print(t)
class LaserSignalBase(abc.ABC,Signal): #Similar to socketsignal
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

    # def get_laser(self, item):
    #     """Get motor instance for a specified controller axis."""
    #     return self._client.get(item)

class LaserSignalRO(LaserSignalBase):
    def __init__(self, signal_name, **kwargs):
        super().__init__(signal_name, **kwargs)
        self._metadata["write_access"] = False

    # @threadlocked
    def _set(self):
        raise ReadOnlyError("Read-only signals cannot be set")

class LaserEmission(LaserSignalRO):
    # @threadlocked
    def _get(self):
        return self.dlc.emission()
class LaserStandby(LaserSignalRO):
    # @threadlocked
    def _get(self):
        return self.dlc.standby()
class LaserSystemHealth(LaserSignalRO):
    # @threadlocked
    def _get(self):
        return self.dlc.system_health()
class LaserVoltageAct(LaserSignalBase):
    # @threadlocked
    def _get(self):
        return self.dlc.voltage_act()
    def _set(self, val):
        logger.info("Voltage is set to "+str(val))
        self.dlc.voltage_act_setter(val)
class LaserCurrentAct(LaserSignalBase):
    # @threadlocked
    def _get(self):
        return self.dlc.current_act()
    def _set(self, val):
        logger.info("Current is set to "+str(val))
        self.dlc.current_act_setter(val)
class LaserMainScanEnd(LaserSignalBase):
    # @threadlocked
    def _get(self):
        return self.dlc.scan_end()

    # @threadlocked
    def _set(self, val):
        logger.info("Main Scan end is set to "+str(val))
        self.dlc.scan_end_setter(val)

class LaserMainScanStart(LaserSignalBase):
    # @threadlocked
    def _get(self):
        return self.dlc.scan_start()

    # @threadlocked
    def _set(self, val):
        logger.info("Main Scan start is set to "+str(val))
        self.dlc.scan_start_setter(val)

class LaserMainScanFrequency(LaserSignalBase):
    # @threadlocked
    def _get(self):
        return self.dlc.scan_frequency()

    # @threadlocked
    def _set(self, val):
        logger.info("Main Scan frequency is set to "+str(val))
        self.dlc.scan_frequency_setter(val)

class LaserMainScanOffset(LaserSignalBase):
    # @threadlocked
    def _get(self):
        return self.dlc.scan_offset()
    # @threadlocked
    def _set(self, val):
        logger.info("Main Scan offset is set to "+str(val))
        self.dlc.scan_offset_setter(val)

class LaserMainCtlWavelengthAct(LaserSignalBase):
    # @retry_once
    # @threadlocked
    def _get(self):
        return self.dlc.wavelength_act()
    # @threadlocked
    def _set(self, val):
        logger.info("Main ctl wavelength is set to "+str(val))
        self.dlc.wavelength_act_setter(val)


class LaserToptica(Device):
    current_act = Cpt(LaserCurrentAct, signal_name="current_act", kind="hinted")
    voltage_act = Cpt(LaserVoltageAct, signal_name="voltage_act", kind="hinted")
    emission = Cpt(LaserEmission, signal_name="emission", kind="hinted")
    standby = Cpt(LaserStandby, signal_name="standby", kind="hinted")
    system_health = Cpt(LaserSystemHealth, signal_name="system_health", kind="hinted")
    scan_end = Cpt(LaserMainScanEnd, signal_name="scan_end")
    scan_start = Cpt(LaserMainScanStart, signal_name="scan_start")
    scan_offset = Cpt(LaserMainScanOffset, signal_name="scan_offset")
    scan_frequency =Cpt(LaserMainScanFrequency, signal_name="scan_frequency")
    ctl_wavelength_act = Cpt(LaserMainCtlWavelengthAct, signal_name="wavelength_act")
    low_limit_wavelength = Cpt(Signal, value=1510, kind="omitted")

    def __init__(self, prefix,name, host=None, port=None, kind=None,configuration_attrs=None, parent=None,config_host=None,**kwargs):
        if config_host==None:
            self.lasercontroller = LaserController(host=host,port=port)
        else:
            self.lasercontroller = LaserController(host=config_host["host"])

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
        self.tolerance = kwargs.pop("tolerance", 0.5)
        self.scan_end.kind = "hinted"
        self.scan_start.kind = "hinted"
        self.scan_offset.kind = "hinted"
        self.scan_frequency.kind = "hinted"
        self.ctl_wavelength_act.kind = "hinted"

    def try_connect(self):
        """
        The function "try_connect" attempts to establish a connection with a laser controller.
        @returns The try_connect() method of the lasercontroller object is being returned.
        """
        return self.lasercontroller.try_connect()

    def disconnect(self):
        """
        The function disconnect turns off the laser controller.
        @returns The method `disconnect` is returning the result of calling the `off` method on the
        `lasercontroller` object.
        """
        return self.lasercontroller.off()
    def update_all_xml(self, xml):
        """
        The function updates various parameters in an XML file and prints a message indicating success
        or failure.
        @param xml - The `xml` parameter is a string that represents the XML content that needs to be
        updated.
        """
        from .XMLGenerator import xml_config_to_dict
        try:
            self.config = xml_config_to_dict(xml)
            self.update_ctl_wavelength_act(self.config["wavelength_act"])
            self.update_scan_end(self.config["scan_end"])
            self.update_scan_start(self.config["scan_start"])
            self.update_current(self.config["current_act"])
            self.update_voltage(self.config["voltage_act"])
            self.update_scan_frequency(self.config["scan_freq"])
            print("Laser Updated")
        except:
            print("XML not Found")
    def limit_wavelength(self):
        """
        The function returns the value of the low limit wavelength.
        @returns The method is returning the value of the attribute `low_limit_wavelength`.
        """
        return self.low_limit_wavelength.get()
    def update_scan_end(self,val):
        """
        The function updates the value of the "scan_end" attribute with the given value.
        @param val - The parameter "val" is the value that you want to update the "scan_end" attribute
        with.
        """
        self.scan_end.put(val)
    def update_voltage(self,val):
        """
        The function updates the voltage value with the given input.
        @param val - The parameter "val" is the value of the voltage that you want to update.
        """
        self.voltage_act.put(val)
    def update_current(self,val):
        """
        The function updates the current activity with a new value.
        @param val - The parameter "val" is the value that you want to update the current_act with.
        """
        self.current_act.put(val)
    def update_scan_start(self,val):
        """
        The function updates the value of the "scan_start" attribute with the given input value.
        @param val - The parameter "val" is the value that you want to update the "scan_start" attribute
        with.
        """
        self.scan_start.put(val)
    def update_scan_offset(self,val):
        """
        The function updates the value of the scan_offset attribute with the given value.
        @param val - The parameter "val" is the value that you want to update the scan offset with.
        """
        self.scan_offset.put(val)
    def update_scan_frequency(self,val):
        """
        The function updates the scan offset value with the given input.
        @param val - The parameter "val" is the value that you want to update the scan offset with.
        """
        self.scan_frequency.put(val)
    def update_ctl_wavelength_act(self,val):
        """
        The function updates the value of the ctl_wavelength_act attribute with the given value.
        @param val - The parameter "val" is the value that you want to set for the "ctl_wavelength_act"
        attribute.
        """
        self.ctl_wavelength_act.put(val)
    def report_emission(self):
        """
        The function "report_emission" returns the value of the "emission" attribute.
        @returns The method `report_emission` is returning the value of `self.emission`.
        """
        return self.emission.get()

    def report_standby(self):
        """
        The function "report_standby" returns the value of the "standby" attribute.
        @returns The method is returning the value of the "standby" attribute.
        """
        return self.standby.get()
    def report_system_health(self):
        """
        The function "report_system_health" returns the system health.
        @returns The method is returning the value of `self.system_health.get()`.
        """
        return self.system_health.get()
    def report_current_act(self):
        """
        The function returns the value of the current_act attribute.
        @returns The method `report_current_act` is returning the value of the `current_act` attribute.
        """
        return self.current_act.get()
    def report_voltage_act(self):
        """
        The function returns the value of the voltage_act attribute.
        @returns The method `report_voltage_act` is returning the value of the `voltage_act` attribute.
        """
        return self.voltage_act.get()
    def report_scan_end(self):
        """
        The function "report_scan_end" returns the value of the "scan_end" attribute.
        @returns The value of the attribute `scan_end`.
        """
        return self.scan_end.get()
    def report_scan_start(self):
        """
        The function returns the value of the scan_start attribute.
        @returns The method is returning the value of the `scan_start` attribute.
        """
        return self.scan_start.get()
    def report_scan_offset(self):
        """
        The function "report_scan_offset" returns the value of the "scan_offset" attribute.
        @returns The method is returning the value of the scan_offset attribute.
        """
        return self.scan_offset.get()
    def report_scan_frequency(self):
        """
        The function returns the scan frequency value.
        @returns The method is returning the value of the scan_frequency attribute.
        """
        return self.scan_frequency.get()
    def report_ctl_wavelength_act(self):
        """
        The function returns the value of the ctl_wavelength_act attribute.
        @returns The method is returning the value of the attribute `ctl_wavelength_act`.
        """
        return self.ctl_wavelength_act.get()

    def stage(self) -> List[object]:
        return super().stage()

    def unstage(self) -> List[object]:
        return super().unstage()

    def stop(self, *, success=False):
        self.controller.stop_all_axes()
        return super().stop(success=success)


if __name__ == "__main__":
    LTDLC = LaserToptica(prefix="...",name="LTDLC", host="129.129.131.136")
    LTDLC.stage()
    print(LTDLC.read())

    # print(LTDLC.get())
    # print(LTDLC.describe())

    LTDLC.unstage()
