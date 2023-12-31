import functools
import threading
import time
from typing import List
import abc
import typing
import logging
# config_ophyd_logging(file='/tmp/ophyd.log', level='DEBUG')
from prettytable import PrettyTable
from .log_ophyd import log_ophyd

import numpy as np
# from bec_utils import BECMessage, MessageEndpoints, bec_logger
from ophyd import Component as Cpt
from ophyd import Device, PositionerBase, Signal
from ophyd.status import wait as status_wait
from ophyd.utils import LimitError, ReadOnlyError

from ophyd.ophydobj import OphydObject

# import asyncio
from IPython.display import clear_output
from mercuryitc import MercuryITC

logger = log_ophyd("ITC_log.txt", __name__)

DEFAULT_EPICSSIGNAL_VALUE = object()
class ITCCommunicationError(Exception):
    pass


class ITCError(Exception):
    pass


# def retry_once(fcn):
#     """Decorator to rerun a function in case a ITC communication error was raised. This may happen if the buffer was not empty."""

#     @functools.wraps(fcn)
#     def wrapper(self, *args, **kwargs):
#         try:
#             val = fcn(self, *args, **kwargs)
#         except (ITCCommunicationError, ITCError):
#             val = fcn(self, *args, **kwargs)
#         return val

#     return wrapper

# def threadlocked(fcn):
#     """Ensure that the thread acquires and releases the lock."""

#     @functools.wraps(fcn)
#     def wrapper(self, *args, **kwargs):
#         lock = self._lock if hasattr(self, "_lock") else self.ITC._lock
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

class ITCController(OphydObject):  # On off laser similar to controller
    _controller_instances = {}
    SUB_CONNECTION_CHANGE = "connection_change"

    def __init__(
            self,
            *,
            name=None,
            host="itc-optistat.psi.ch",
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
        print(f"connecting to {self.host}")
        logger.info("The connection has already been established.")
        self.ITC = MercuryITC(f"TCPIP0::{self.host}::7020::SOCKET")
        self.htr = self.ITC.modules[1]  # main htr
        self.temp = self.ITC.modules[2]
        self.aux = self.ITC.modules[0]
        self._connected = True
        # self._set_default_values()
        self.name = "MercuryITC"
        # self.is_open = True

    # def _set_default_values(self):
    #     # no. of axes controlled by each controller
    #     self._wavelength_act = 1550

    @property
    def connected(self):
        return self._connected

    # def connect(self):
    #     print(f"connecting to {self.host}")
    #     self.ITC = DLCpro(NetworkConnection(self.host)).open()
    #     # self.name = "self.ITC.system_model.get()+self.ITC.system_type.get()+ self.ITC.serial_number.get()"
    #     self._connected = True
    # def open(self):
    #     self.connect()
    #     self.is_open = True

    def off(self):
        """Close the connection to the laser"""
        logger.info("The connection is already closed.")
        self.ITC.disconnect()
        self.connected = False

    def get_laser_data(self):
        signals = {
            # "wide scan amplitude":{"value": self.ITC.laser1.wide_scan.amplitude.get()},
            # "wide scan offset":{"value": self.ITC.laser1.wide_scan.offset.get()},
            # "wide scan remaining time":{"value": self.ITC.laser1.wide_scan.remaining_time.get()},
            "Main heater volt": {"value": self.htr.volt},
            "Main heater current RO": {"value": self.htr.curr},
            "Main heater power": {"value": self.heater_power},  #
            "Main heater voltage limit": {"value": self.htr.vlim},
            "Temperature sensor volt RO": {"value": self.temp.volt},
            "Temperature sensor excitation magnitude": {"value": self.temp.exct_mag},
            "Temperature sensor scaling factor": {"value": self.temp.cal_scal},
            "Temperature sensor offset": {"value": self.temp.cal_offs},
            "Temperature sensor hot limit": {"value": self.temp.cal_hotl},
            "Temperature sensor cold limit": {"value": self.temp.cal_coldl},
            "Temperature sensor temperature": {"value": self.temp.temp},  #
            "Temperature sensor sensitivity": {"value": self.temp.slop},
            "Temperature sensor associate heater": {"value": self.temp.loop_temp},
            "Temperature sensor associate auxiliary": {"value": self.temp.loop_aux},
            "Temperature sensor propotional gain": {"value": self.temp.loop_p},
            "Temperature sensor internal gain": {"value": self.temp.loop_i},
            "Temperature sensor differential gain": {"value": self.temp.loop_d},
            "Temperature sensor Enables or disables automatic gas flow": {"value": self.temp.loop_faut},
            "Temperature sensor ramp speed in K/min": {"value": self.temp.loop_rset},
            "Temperature sensor Enables or disables temperature ramp": {"value": self.temp.loop_rena},
            "Gas flow minimum flow": {"value": self.aux.gmin},
            "Gas flow Temperature error sensitivity": {"value": self.aux.tes},
            "Gas flow Temperature voltage error sensitivity": {"value": self.aux.tves},
            "Gas flow stepper speed": {"value": self.aux.spd},
            "Gas flow position stepper motor": {"value": self.aux.step},

        }
        return signals

    #####################################
    # heater module getters and setters #
    #####################################
    def heater_power(self):
        logger.debug(f"recv heater power")
        return self.htr.powr

    # @scan_end.setter
    def heater_power_setter(self, val):
        logger.debug(f"set scan end")
        self.htr.powr(val)

    ##########################################
    # temperature module getters and setters #
    ##########################################
    def temperature(self):
        logger.debug(f"recv temperature")
        return self.temp.temp[0]

    def temperature_setter(self, val):
        logger.debug(f"set temperature")
        self.temp.temp(val)

    def flow_percentage(self):
        logger.debug(f"recv flow percentage")
        return self.temp.loop_fset

    def flow_percentage_setter(self, val):
        logger.debug(f"set flow percentage")
        self.temp.loop_fset(val)

    def temperature_set_point(self):
        logger.debug(f"recv temperature set point")
        return self.temp.loop_tset

    def temperature_set_point_setter(self, val):
        logger.debug(f"set temperature set point")
        self.temp.loop_tset(val)

    def voltage(self):
        logger.debug(f"recv voltage")
        return self.temp.volt

    def voltage_setter(self, val):
        logger.debug(f"set voltage")
        self.temp.volt(val)

    def automatic_heating(self):
        logger.debug(f"recv automatic heating")
        return self.temp.loop_enab

    def automatic_heating_setter(self, val):
        logger.debug(f"set automatic heating")
        self.temp.loop_enab(val)

    def automatic_pid(self):
        logger.debug(f"recv automatic pid")
        return self.temp.loop_pidt

    def automatic_pid_setter(self, val):
        logger.debug(f"recv automatic pid")
        self.temp.loop_pidt(val)

    ########################################
    # auxiliary module getters and setters #
    ########################################

    def valve_open_percentage(self):
        logger.debug(f"recv valve open percentage")
        return self.aux.perc

    def describe(self) -> None:
        t = PrettyTable()
        t.title = f"{self.__class__.__name__} on {self.sock.host}:{self.sock.port}"
        t.field_names = [
            "heater power",
            "temperature",
            "flow percentage",
            "temperature set point",
            "voltage",
            "automatic heating",
            "automatic pid",
            "valve open percentage",
        ]
        t.add_row(
            [
                self.heater_power(),
                self.temperature(),
                self.flow_percentage(),
                self.temperature_set_point(),
                self.voltage(),
                self.automatic_heating(),
                self.automatic_pid(),
                self.flow_percentage(),
            ]
        )
        print(t)

    # def __new__(cls, *args, **kwargs):
    #     socket = kwargs.get("socket")
    #     if not hasattr(socket, "host"):
    #         raise RuntimeError("Socket must specify a host.")
    #     if not hasattr(socket, "port"):
    #         raise RuntimeError("Socket must specify a port.")
    #     host_port = f"{socket.host}:{socket.port}"
    #     if host_port not in Controller._controller_instances:
    #         Controller._controller_instances[host_port] = object.__new__(cls)
    #     return Controller._controller_instances[host_port]


class ITCSignalBase(abc.ABC, Signal):  # Similar to socketsignal
    SUB_SETPOINT = "setpoint"

    def __init__(self, signal_name, **kwargs):
        self.signal_name = signal_name
        super().__init__(**kwargs)
        self.ITC = self.parent.itccontroller

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
        super().put(value, timestamp=timestamp, force=True)
        self._run_subs(sub_type=self.SUB_SETPOINT, old_value=old_value,
                       value=VALUE, timestamp=self.timestamp)

    def describe(self):
        if self._readback is DEFAULT_EPICSSIGNAL_VALUE:
            val = self.get()
        else:
            val = self._readback
        return {
            self.name: {
                "source": self.ITC.name,
                "dtype": data_type(val),
                "shape": data_shape(val)
            }
        }

    # def get_laser(self, item):
    #     """Get motor instance for a specified controller axis."""
    #     return self._client.get(item)


class ITCSignalRO(ITCSignalBase):
    def __init__(self, signal_name, **kwargs):
        super().__init__(signal_name, **kwargs)
        self._metadata["write_access"] = False

    # @threadlocked
    def _set(self):
        raise ReadOnlyError("Read-only signals cannot be set")


class ITCHeaterPower(ITCSignalBase):
    # @threadlocked
    def _get(self):
        return self.ITC.heater_power()

    # @threadlocked
    def _set(self, val):
        logger.info("Heater power is set to " + str(val))
        self.ITC.heater_power_setter(val)


class ITCTemperature(ITCSignalBase):
    # @threadlocked
    def _get(self):
        return self.ITC.temperature()

    # @threadlocked
    def _set(self, val):
        logger.info("Temperature is set to " + str(val))
        self.ITC.temperature(val)


class ITCFlowPercentage(ITCSignalBase):
    # @threadlocked
    def _get(self):
        return self.ITC.flow_percentage()

    # @threadlocked
    def _set(self, val):
        logger.info("Flow percentage is set to " + str(val))
        self.ITC.flow_percentage_setter(val)


class ITCTemperatureSetPoint(ITCSignalBase):
    # @threadlocked
    def _get(self):
        return self.ITC.temperature_set_point()

    # @threadlocked
    def _set(self, val):
        logger.info("Temperature Set Point is set to " + str(val))
        self.ITC.temperature_set_point_setter(val)


class ITCVoltage(ITCSignalBase):
    # @threadlocked
    def _get(self):
        return self.ITC.voltage()

    # @threadlocked
    def _set(self, val):
        logger.info("Voltage is set to " + str(val))
        self.ITC.voltage_setter(val)


class ITCAutomaticHeating(ITCSignalBase):
    # @threadlocked
    def _get(self):
        return self.ITC.automatic_heating()

    # @threadlocked
    def _set(self, val):
        logger.info("Automatic heating is set to " + str(val))
        self.ITC.automatic_heating_setter(val)


class ITCAutomaticPID(ITCSignalBase):
    # @threadlocked
    def _get(self):
        return self.ITC.automatic_pid()

    # @threadlocked
    def _set(self, val):
        logger.info("Automatic pid is set to " + str(val))
        self.ITC.automatic_pid_setter(val)


class ITCValveOpenPercentage(ITCSignalRO):
    # @threadlocked
    def _get(self):
        return self.ITC.valve_open_percentage()


class MercuryITCDevice(Device):
    # widescan_amplitude = Cpt(ITCWideScanAmplitude, signal_name="widescan_amplitude")
    # widescan_offset = Cpt(ITCWideScanOffset, signal_name="widescan_offset")
    # widescan_time = Cpt(ITCWideScanRemainingTime, signal_name="widescan_remaining_time")
    heater_power = Cpt(ITCHeaterPower, signal_name="heater_power", kind="hinted")
    temperature = Cpt(ITCTemperature, signal_name="temperature", kind="hinted")
    flow_percentage = Cpt(ITCFlowPercentage, signal_name="flow_percentage", kind="hinted")
    temperature_set_point = Cpt(ITCTemperatureSetPoint, signal_name="temperature_set_point", kind="hinted")
    voltage = Cpt(ITCVoltage, signal_name="voltage", kind="hinted")
    automatic_heating = Cpt(ITCAutomaticHeating, signal_name="automatic_heating", kind="hinted")
    automatic_pid = Cpt(ITCAutomaticPID, signal_name="automatic_pid", kind="hinted")
    valve_open_percentage = Cpt(ITCValveOpenPercentage, signal_name="valve_open_percentage", kind="hinted")

    def __init__(self, prefix, name, host, port=None, kind=None, configuration_attrs=None, parent=None,
                 config_host=None, **kwargs):
        if config_host == None:
            self.itccontroller = ITCController(host=host, port=port)
        else:
            self.itccontroller = ITCController(host=config_host["host"], port=config_host["port"])
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

    def update_heater_power(self, val):
        self.itccontroller.heater_power_setter(val)

    def update_temperature(self, val):
        self.itccontroller.temperature_setter(val)

    def update_flow_percentage(self, val):
        self.itccontroller.flow_percentage_setter(val)

    def update_temperature_set_point(self, val):
        self.itccontroller.temperature_set_point_setter(val)

    def update_voltage(self, val):
        self.itccontroller.voltage_setter(val)

    def update_automatic_heating(self, val):
        self.itccontroller.automatic_heating_setter(val)

    def update_automatic_pid(self, val):
        self.itccontroller.automatic_pid_setter(val)

    def report_heater_power(self):
        return self.heater_power.get()

    def report_temperature(self):
        return self.scan_start.get()

    def report_flow_percentage(self):
        return self.flow_percentage.get()

    def report_temperature_set_point(self):
        return self.temperature_set_point.get()

    def report_voltage(self):
        return self.voltage.get()

    def report_automatic_heating(self):
        return self.automatic_heating.get()

    def report_automatic_pid(self):
        return self.automatic_pid.get()

    def report_valve_open_percentage(self):
        return self.valve_open_percentage.get()

    def stage(self) -> List[object]:
        return super().stage()

    def unstage(self) -> List[object]:
        return super().unstage()

    def stop(self, *, success=False):
        self.controller.stop_all_axes()
        return super().stop(success=success)


if __name__ == "__main__":
    ITCD = MercuryITCDevice(prefix="...", name="ITCD", host="itc-optistat.psi.ch")
    ITCD.stage()
    print(ITCD.read())

    # print(ITCD.get())
    # print(ITCD.describe())

    ITCD.unstage()
