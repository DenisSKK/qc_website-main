import functools
import threading
import time
from typing import List
from .log_ophyd import log_ophyd

import numpy as np
from ophyd import Component as Cpt
from ophyd import Device, Signal
from ophyd.status import wait as status_wait
from ophyd.utils import LimitError, ReadOnlyError
from prettytable import PrettyTable

from .sockets import SocketIO, SocketSignal
from .controller import Controller, threadlocked
#caylar_magnet.py
logger = log_ophyd("mag_log.txt",__name__)

class MagneticCommunicationError(Exception):
    pass

class MagneticError(Exception):
    pass

def retry_once(fcn):
    """
    The `retry_once` function is a decorator that allows a function to be rerun once if a
    `CommunicationError` or `MagneticError` is raised.
    @param fcn - The parameter `fcn` is a function that will be decorated with the `retry_once`
    decorator.
    @returns The decorator function `retry_once` returns the wrapper function `wrapper`.
    """
    """Decorator to rerun a function in case a CommunicationError was raised. This may happen if the buffer was not empty."""

    @functools.wraps(fcn)
    def wrapper(self, *args, **kwargs):
        try:
            val = fcn(self, *args, **kwargs)
        except (MagneticCommunicationError, MagneticError):
            val = fcn(self, *args, **kwargs)
        return val

    return wrapper

# The MagneticController class is a subclass of the Controller class.
class MagneticController(Controller):
    USER_ACCESS = [
        "describe",
        "show_running_threads",
        "magnetic_show_all",
        "socket_put_and_receive",
        "socket_put_confirmed",
    ]

    def __init__(
        self,
        *,
        name="MagneticController",
        kind=None,
        parent=None,
        socket=None,
        attr_name="",
        labels=None,
    ):
        if not hasattr(self, "_initialized") or not self._initialized:
            # self._Magnetic_axis_per_controller = 8
            # self._axis = [None for axis_num in range(self._galil_axis_per_controller)]
            super().__init__(
                name=name,
                socket=socket,
                attr_name=attr_name,
                parent=parent,
                labels=labels,
                kind=kind,
            )

    def on(self) -> None:
        """
        The function `on` opens a socket connection to a controller and returns whether the connection
        was successfully established.
        @returns a boolean value. If the connection is successfully established, it returns True. If the
        connection cannot be established, it returns False. If the connection has already been
        established, it also returns True.
        """
        """Open a new socket connection to the controller"""
        if not self.connected:
            try:
                self.sock.open()
                self.connected = True
                print("Caylar connection has already been established.")
                return True
            except:
                print("Caylar connection cannot already been established.")
                self.connected = False
                return False
        else:
            logger.info("Caylar connection has already been established.")
            # warnings.warn(f"The connection has already been established.", stacklevel=2)
            return True

    def off(self) -> None:
        """
        The `off` function closes the socket connection to the controller if it is currently open.
        """
        """Close the socket connection to the controller"""
        if self.connected:
            self.sock.close()
            self.connected = False
        else:
            logger.info("The connection is already closed.")

    def _remove_trailing_characters(self, var) -> str:
        """
        The function removes trailing characters from a string by splitting it at the first occurrence
        of "\r\n" and returning the first part.
        @param var - The `var` parameter is a string that represents a variable.
        @returns a string.
        """
        if len(var) > 1:
            return var.split("\r\n")[0]
        return var

    @threadlocked
    def socket_put(self, val: str) -> None:
        """
        The function `socket_put` takes a string `val` as input and sends it over a socket connection.
        @param {str} val - The parameter `val` is a string that represents the value that you want to
        send over the socket connection.
        """
        self.sock.put(bytes(val, "ascii"))

    @threadlocked
    def socket_get(self) -> str:
        """
        The function `socket_get` receives data from a socket and returns it as a string, splitting it
        into a list of words.
        @returns a string.
        """
        return self.sock.receive().decode("ascii").split(' ')

    @retry_once
    def socket_put_and_receive(self, val: str, remove_trailing_chars=False) -> str:
        """
        The function `socket_put_and_receive` sends a value over a socket connection, receives a
        response, and optionally removes trailing characters from the response.
        @param {str} val - The `val` parameter is a string that represents the value to be sent through
        the socket.
        @param [remove_trailing_chars=False] - The `remove_trailing_chars` parameter is a boolean flag
        that determines whether or not to remove trailing characters from the received data. If set to
        `True`, the function will call the `_remove_trailing_characters` method to remove the trailing
        characters. If set to `False`, the function will not
        @returns a string.
        """
        self.socket_put(val)
        if remove_trailing_chars:
            return self._remove_trailing_characters(self.sock.receive().decode ("ascii").split(' ') [1])
        return self.socket_get()

    @retry_once
    def socket_put_confirmed(self, val: str) -> None:
        """Send message to controller and ensure that it is received by checking that the socket receives a colon.

        Args:
            val (str): Message that should be sent to the socket

        Raises:
            MagneticCommunicationError: Raised if the return value is not a colon.

        """
        return_val = self.socket_put_and_receive(val)
        if return_val != ":":
            raise MagneticCommunicationError(
                f"Expected return value of ':' but instead received {return_val}"
            )

    def get_current(self) -> str:
        """
        The function `get_current` sends a command to a socket and receives the current value as a
        string.
        @returns the value of the variable "current", which is a string.
        """
        current = self.socket_put_and_receive("GET_CURRENT\n")
        return current

    def set_field(self, val) -> None:
        """
        The function sets a field value and logs the action.
        @param val - The parameter "val" represents the value that you want to set for the field.
        """
        logger.info("Field is set to "+str(val))
        self.socket_put_and_receive("SET_FIELD +"+str(val)+"\n")

    def set_current(self, val) -> None:
        """
        The function sets the current value and logs the action.
        @param val - The parameter "val" represents the value that you want to set as the current.
        """
        logger.info("Current is set to "+str(val))
        self.socket_put_and_receive("SET_CURRENT +"+str(val)+"\n")

    def get_field(self) -> str:
        """
        The function `get_field` sends a request to a socket server to retrieve a field and returns the
        received field as a string.
        @returns a string value.
        """
        field = self.socket_put_and_receive("GET_FIELD\n")
        return field

    def get_voltage(self) -> str:
        """
        The function `get_voltage` sends a command to a socket and receives the voltage value as a
        string.
        @returns the voltage as a string.
        """
        voltage = self.socket_put_and_receive("GET_VOLTAGE\n")
        return voltage

    def get_adc_dac_temp(self) -> str:
        """
        The function `get_adc_dac_temp` sends a command to a socket and receives the ADC/DAC temperature
        as a string.
        @returns the value of the variable "adc_dac_temp", which is a string.
        """
        adc_dac_temp = self.socket_put_and_receive("GET_ADC_DAC_TEMP\n")
        return adc_dac_temp

    def get_box_temp(self) -> str:
        """
        The function `get_box_temp` sends a command to a socket and receives the box temperature as a
        string.
        @returns the value of the variable "box_temp", which is a string.
        """
        box_temp = self.socket_put_and_receive("GET_BOX_TEMP\n")
        return box_temp

    def get_rack_temp(self) -> str:
        """
        The function `get_rack_temp` sends a command to a socket and receives the rack temperature as a
        string.
        @returns the value of the variable "rack_temp".
        """
        rack_temp = self.socket_put_and_receive("GET_RACK_TEMP\n")
        return rack_temp

    def get_water_temp(self) -> str:
        """
        The function `get_water_temp` sends a command to a socket and receives the water temperature as
        a string.
        @returns the water temperature as a string.
        """
        water_temp = self.socket_put_and_receive("GET_WATER_TEMP\n")
        return water_temp

    def get_water_flow(self) -> str:
        """
        The function `get_water_flow` sends a command to a socket and receives the water flow value as a
        string.
        @returns the value of the variable "water_flow".
        """
        water_flow = self.socket_put_and_receive("GET_WATER_FLOW\n")
        return water_flow

    def describe(self) -> None:
        """
        The `describe` function prints a table with various measurements of a device's current, field,
        voltage, temperatures, and water flow.
        """
        t = PrettyTable()
        t.title = f"{self.__class__.__name__} on {self.sock.host}:{self.sock.port}"
        t.field_names = [
            "Current",
            "Field",
            "Voltage",
            "Adc Dac Temp",
            "Box Temp",
            "Rack Temp",
            "Water Temp",
            "Water Flow"
        ]
        t.add_row(
                    [
                        self.get_current(),
                        self.get_field(),
                        self.get_voltage(),
                        self.get_adc_dac_temp(),
                        self.get_box_temp(),
                        self.get_rack_temp(),
                        self.get_water_temp(),
                        self.get_water_flow()
                    ]
                )
        print(t)

        # self.show_running_threads()

    def magnetic_show_all(self) -> None:
        """
        The function "magnetic_show_all" iterates through all the controller instances and calls the
        "describe" method for instances of the "MagneticController" class.
        """
        for controller in self._controller_instances.values():
            if isinstance(controller, MagneticController):
                controller.describe()

# The class MagneticSignalBase is a subclass of SocketSignal.
class MagneticSignalBase(SocketSignal):
    def __init__(self, signal_name, **kwargs):
        self.signal_name = signal_name
        super().__init__(**kwargs)
        self.controller = self.parent.controller
        self.sock = self.parent.controller.sock


# The class MagneticSignalRO is a subclass of MagneticSignalBase.
class MagneticSignalRO(MagneticSignalBase):
    def __init__(self, signal_name, **kwargs):
        super().__init__(signal_name, **kwargs)
        self._metadata["write_access"] = False

    def _socket_set(self, val):
        raise ReadOnlyError("Read-only signals cannot be set")

# The MagneticField class is a subclass of MagneticSignalBase.
class MagneticField(MagneticSignalBase):
    def _socket_get(self) -> float:
        try:
            return float(self.controller.get_field()[1])
        except:
            return float(self.controller.get_field()[1][1:-1])
    @retry_once
    @threadlocked
    def _socket_set(self, val: float) -> None:
        self.controller.set_field(val)

class MagneticCurrent(MagneticSignalBase):
    def _socket_get(self) -> float:
        try:
            return float(self.controller.get_current()[1])
        except:
            return float(self.controller.get_current()[1][1:-1])

    @retry_once
    @threadlocked
    def _socket_set(self, val: float) -> None:
        self.controller.set_current(val)

class MagneticVoltage(MagneticSignalRO):
    @threadlocked
    def _socket_get(self):
        try:
            return float(self.controller.get_voltage()[1])
        except:
            return float(self.controller.get_voltage()[1][1:-1])

class MagneticADCDACTemp(MagneticSignalRO):
    @threadlocked
    def _socket_get(self):
        return float(self.controller.get_adc_dac_temp()[1])

class MagneticBoxTemp(MagneticSignalRO):
    @threadlocked
    def _socket_get(self):
        return float(self.controller.get_box_temp()[1])

class MagneticRackTemp(MagneticSignalRO):
    @threadlocked
    def _socket_get(self):
        return float(self.controller.get_rack_temp()[1])

class MagneticWaterTemp(MagneticSignalRO):
    @threadlocked
    def _socket_get(self):
        return float(self.controller.get_water_temp()[1])

class MagneticWaterFlow(MagneticSignalRO):
    @threadlocked
    def _socket_get(self):
        return float(self.controller.get_water_flow()[1])

# The CaylarMagnet class is a subclass of the Device class.
class CaylarMagnet(Device):
    USER_ACCESS = ["controller"]
    magnetic_current = Cpt(MagneticCurrent, signal_name = "Magnetic current",kind="hinted")
    magnetic_field = Cpt(MagneticField, signal_name = "Magnetic field",kind="hinted")
    magnetic_voltage = Cpt(MagneticVoltage, signal_name = "Magnetic voltage",kind="hinted")
    magnetic_ADCDAC_temp = Cpt(MagneticADCDACTemp, signal_name = "Magnetic ADCDAC temp",kind="hinted")
    magnetic_box_temp = Cpt(MagneticBoxTemp, signal_name = "Magnetic box temp",kind="hinted")
    magnetic_rack_temp = Cpt(MagneticRackTemp, signal_name = "Magnetic rack temp",kind="hinted")
    magnetic_water_temp = Cpt(MagneticWaterTemp, signal_name = "Magnetic water temp",kind="hinted")
    magnetic_water_flow = Cpt(MagneticWaterFlow, signal_name = "Magnetic water flow",kind="hinted")

    SUB_READBACK = "readback"
    SUB_CONNECTION_CHANGE = "connection_change"
    _default_sub = SUB_READBACK

    def __init__(
        self,
        prefix="",
        *,
        name,
        kind=None,
        read_attrs=None,
        configuration_attrs=None,
        parent=None,
        host="129.129.131.154",
        port=1234,
        sign=1,
        socket_cls=SocketIO,
        device_manager=None,
        limits=None,
        config_host=None,**kwargs,
    ):
        self.sign = sign
        if config_host==None:
            self.controller = MagneticController(socket=socket_cls(host=host, port=port))
        else:
            self.controller = MagneticController(socket=socket_cls(host=config_host["host"], port=config_host["port"]))
        # self.controller.on()
        self.device_manager = device_manager
        super().__init__(
            prefix,
            name=name,
            kind=kind,
            read_attrs=read_attrs,
            configuration_attrs=configuration_attrs,
            parent=parent,
            **kwargs,
        )
        self.name = name
        self.controller.subscribe(
            self._update_connection_state, event_type=self.SUB_CONNECTION_CHANGE
        )
        self._update_connection_state()
        # self.readback.subscribe(self._forward_readback, event_type=self.readback.SUB_VALUE)
    def disconnect(self):
        """
        The function disconnect turns off the controller.
        @returns The method `disconnect` is returning the result of calling the `off` method on the
        `controller` object.
        """
        return self.controller.off()
    def try_connect(self):
        """
        The function `try_connect` attempts to turn on the controller.
        @returns The method `try_connect` is returning the result of calling the `on` method on the
        `self.controller` object.
        """
        return self.controller.on()

    def update_all_xml(self, xml):
        """
        The function updates the XML configuration file and prints a message indicating whether the
        update was successful or if the XML file was not found.
        @param xml - The `xml` parameter is a string that represents the XML content that needs to be
        updated.
        """
        from .XMLGenerator import xml_config_to_dict
        try:
            self.config = xml_config_to_dict(xml)
            self.current_setter(self.config["current"])
            self.field_setter(self.config["field"])
            print("Caylar Updated")
        except:
            print("XML not Found")

    def _update_connection_state(self, **kwargs):
        """
        The function updates the "connected" metadata attribute of all items in a walk based on the
        "connected" attribute of the controller.
        """
        for walk in self.walk_signals():
            walk.item._metadata["connected"] = self.controller.connected

    def _forward_readback(self, **kwargs):
        """
        The function removes the "sub_type" key from the kwargs dictionary and then runs the readback
        subroutine.
        """
        kwargs.pop("sub_type")
        self._run_subs(sub_type="readback", **kwargs)

    @property
    def current(self):
        """
        The function returns the value of the magnetic current.
        @returns The method `current` is returning the value of `self.magnetic_current`.
        """
        return self.magnetic_current.get()

    def current_setter(self, val):
        """
        The function sets the value of a magnetic current if the input is a float.
        @param val - The parameter "val" is the value that you want to set for the magnetic current.
        @returns The method `current_setter` returns the result of calling the `put` method on the
        `magnetic_current` object with the `val` parameter as an argument.
        """
        if isinstance(val, float):
            return self.magnetic_current.put(val)
    @property
    def field(self):
        """
        The function returns the value of the magnetic field.
        @returns The method is returning the value of the `magnetic_field` attribute.
        """
        return self.magnetic_field.get()

    def field_setter(self, val):
        """
        The function sets the value of a magnetic field if the input is a float.
        @param val - The parameter "val" is the value that will be set for the magnetic field. It is
        expected to be a float.
        @returns The method is returning the result of the `put` method of the `magnetic_field` object.
        """
        if isinstance(val, float):
            return self.magnetic_field.put(val)
    @property
    def voltage(self):
        """
        The function returns the value of the magnetic voltage.
        @returns The method is returning the value of the magnetic voltage.
        """
        return self.magnetic_voltage.get()
    @property
    def ADCDAC_temp(self):
        """
        The function returns the temperature value from the magnetic ADCDAC sensor.
        @returns the value of `self.magnetic_ADCDAC_temp`.
        """
        return self.magnetic_ADCDAC_temp.get()

    @property
    def box_temp(self):
        """
        The function returns the value of the magnetic box temperature.
        @returns The method is returning the value of the attribute `magnetic_box_temp`.
        """
        return self.magnetic_box_temp.get()

    @property
    def rack_temp(self):
        """
        The function returns the value of the magnetic rack temperature.
        @returns The method `rack_temp` is returning the value of `self.magnetic_rack_temp`.
        """
        return self.magnetic_rack_temp.get()

    @property
    def water_temp(self):
        """
        The function returns the value of the magnetic water temperature.
        @returns The method is returning the value of the `magnetic_water_temp` attribute.
        """
        return self.magnetic_water_temp.get()
    @property
    def water_flow(self):
        """
        The function returns the value of the magnetic water flow.
        @returns The method is returning the value of the `magnetic_water_flow` attribute.
        """
        return self.magnetic_water_flow.get()
    def stage(self) -> List[object]:
        """
        The function returns the result of calling the `stage()` method of the superclass.
        @returns The method is returning a list of objects.
        """
        return super().stage()

    def unstage(self) -> List[object]:
        """
        The function unstage returns a list of objects by calling the unstage method of the superclass.
        @returns The method is returning a list of objects.
        """
        return super().unstage()

    def stop(self, *, success=False):
        """
        The function stops all axes and returns a success status.
        @param [success=False] - The `success` parameter is a keyword-only argument that defaults to
        `False`. It is used to indicate whether the stop operation was successful or not.
        @returns The `stop` method is returning the result of calling the `stop` method of the
        superclass, with the `success` argument passed in.
        """
        self.controller.stop_all_axes()
        return super().stop(success=success)


if __name__ == "__main__":
    magneticIR = CaylarMagnet("H", name="magneticIR")
    # print(magneticIR.stage())

    print(magneticIR.read())

    # print(magneticIR.get())
    # print(magneticIR.describe())

    # magneticIR.unstage()

    # from sockets import SocketMock

    # magneticIR = Magnet(
    #     "H", name="magneticIR", host="mpc2680.psi.ch", port=8081, socket_cls=SocketMock
    # )
    # magneticIR.stage()

    # magneticIR.controller.magnetic_show_all()
