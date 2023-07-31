import functools
import threading
import warnings

from ophyd.ophydobj import OphydObject
from .sockets import SocketIO


def threadlocked(fcn):
    """
    The `threadlocked` decorator ensures that the thread acquires and releases a lock before and after
    executing the decorated function.
    @param fcn - The parameter `fcn` is a function that will be wrapped by the `threadlocked` decorator.
    @returns The function being returned is a wrapper function that ensures that the thread acquires and
    releases a lock before and after executing the original function.
    """
    """Ensure that the thread acquires and releases the lock."""

    @functools.wraps(fcn)
    def wrapper(self, *args, **kwargs):
        lock = self._lock if hasattr(self, "_lock") else self.controller._lock
        with lock:
            return fcn(self, *args, **kwargs)

    return wrapper


class SingletonController:
    _controller_instance = None

    def __init__(self) -> None:
        self._lock = threading.RLock()

    def on(self):
        pass

    def off(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not SingletonController._controller_instance:
            SingletonController._controller_instance = object.__new__(cls)
        return SingletonController._controller_instance


class Controller(OphydObject):
    _controller_instances = {}

    SUB_CONNECTION_CHANGE = "connection_change"

    def __init__(
        self,
        *,
        name=None,
        socket=None,
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
            self._initialize(socket)
            self._initialized = True

    def _initialize(self, socket):
        self._connected = False
        # self._set_default_values()
        self.sock = socket if socket is not None else SocketIO()

    # def _set_default_values(self):
    #     # no. of axes controlled by each controller
    #     self._axis_per_controller = 8
    #     self._motors = [None for axis_num in range(self._axis_per_controller)]

    @property
    def connected(self):
        """
        The function returns the value of the "_connected" attribute.
        @returns The method is returning the value of the variable `_connected`.
        """
        return self._connected

    @connected.setter
    def connected(self, value):
        """
        The function sets the value of the "_connected" attribute and runs any subscribed functions for
        connection change events.
        @param value - The "value" parameter is a boolean value that represents the connection status.
        It is used to set the "_connected" attribute of the object to either True or False.
        """
        self._connected = value
        self._run_subs(sub_type=self.SUB_CONNECTION_CHANGE)

    def on(self, controller_num=0):
        """
        The function opens a new socket connection to the controller.
        @param [controller_num=0] - The parameter `controller_num` is an optional parameter that
        specifies the number of the controller to connect to. If no value is provided, it defaults to 0.
        """
        """Open a new socket connection to the controller"""
        if not self.connected:
            self.connected = True
        else:
            warnings.warn(f"The connection has already been established.", stacklevel=2)

    def off(self):
        """Close the socket connection to the controller"""
        self.sock.close()
        self.connected = False

    def __new__(cls, *args, **kwargs):
        socket = kwargs.get("socket")
        if not hasattr(socket, "host"):
            raise RuntimeError("Socket must specify a host.")
        if not hasattr(socket, "port"):
            raise RuntimeError("Socket must specify a port.")
        host_port = f"{socket.host}:{socket.port}"
        if host_port not in Controller._controller_instances:
            Controller._controller_instances[host_port] = object.__new__(cls)
        return Controller._controller_instances[host_port]
