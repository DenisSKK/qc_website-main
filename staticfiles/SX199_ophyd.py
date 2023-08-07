from datetime import datetime

from staticfiles.instrbuilder.instrument_opening import open_by_name
from staticfiles.ophyd.ee_instruments import generate_ophyd_obj
from typing import List
from .XMLGenerator import xml_config_to_dict
from time import sleep

GAIN_CHOICES = {
    '0': 'G1nA',
    '1': 'G10nA',
    '2': 'G100nA',
    '3': 'G1uA',
    '4': 'G10uA',
    '5': 'G100uA',
    '6': 'G1mA',
    '7': 'G10mA',
    '8': 'G50mA',
}


# SX199Device class with functions to connect control and to get parameters of one, or two CS580 current sources.
# We connect to the SX199 through the network, then we can control current sources with this class.
# The commands in csv file are not only SX199 commands. There are also CS580 commands. This could be approached with
# CS580 class as well, but this approach is also efficient.
# Sleep commands might be confusing. I have tested this with CS580 and if I link to desired port number without delay
# after that, the next command is ignored and does not return anything. I don't know what's the cause.
class SX199Device():
    def __init__(self, name='sx199', **kwargs):
        self.name = name
        if name == None:
            self.name = 'sx199'
        self.sx_instr = None
        self.sx_ophyd = None
        # Initialize variables then connect
        self.connect()

    # Connect function for checking if connection is not already established, and connecting if not.
    # I have bad experience with open_by_name() function, when it doesn't connect until 3rd try when in Jupyter
    # Notebook. Therefore, the for loop with 3 attempts to connect.
    def connect(self):
        if self.sx_instr is not None and self.sx_ophyd is not None and self.is_connected():
            return True
        for _ in range(3):
            # Open by name function is from Instrbuilder library.
            self.sx_instr = open_by_name(name=self.name)
            self.sx_instr.name = self.name

            # Ophyd function to create ophyd object. We will be using mainly that
            SX, component_dict = generate_ophyd_obj(name=self.name, scpi_obj=self.sx_instr)
            self.sx_ophyd = SX(name=self.name)

            # Making sure connection was established.
            if self.is_connected():
                print(f"{self.report_id()} connected")
                return True
        return False

    # Closing PyVisa connection and setting both objects to None
    def disconnect(self):
        self.sx_instr.comm_handle.close()

    # Checking if device is connected is made by comparing returned string from get ID (*IDN? command)
    def is_connected(self):
        id_string = self.sx_ophyd.id.get()
        return id_string.startswith("Stanford_Research_Systems,SX199")

    # Checking if device is connected is made by comparing returned string from get ID (*IDN? command)
    def is_cs_connected(self, link):
        # escape() is used to make sure that if there is a previous-linked port or error, it will be reset.
        self.escape()
        self.update_link(link)
        sleep(0.005)
        try:
            id_string = self.sx_ophyd.id.get()
        except:
            return False
        sleep(0.000001)
        # escape() after dealing with desired CS is necessary to un-link already linked port.
        self.escape()
        # print(f'check: {id_string}')
        return id_string.startswith("Stanford_Research_Systems,CS580")

    # Updating parameters could be expensive operation if there is 8 of them. That's why I compare 2 xml files with
    # last set parameters, and parameters set now. This will compare two xml files and set only the values, that are
    # different from the last updating.
    # Only for first CS580
    def update_link_1_xml(self, xml_update, xml_old_update):
        actual_config = xml_config_to_dict(xml_update)
        last_config = xml_config_to_dict(xml_old_update)
        self.update_link(1)
        sleep(0.005)
        for attribute, actual_value in actual_config.items():
            last_value = last_config.get(attribute)
            if actual_value != last_value:
                if attribute == "cs_gain_1":
                    print(f"setting gain to {actual_value}")
                    self.update_gain(actual_value)
                elif attribute == "cs_input_1":
                    print(f"setting input to {actual_value}")
                    self.update_input(actual_value)
                elif attribute == "cs_speed_1":
                    print(f"setting speed to {actual_value}")
                    self.update_speed(actual_value)
                elif attribute == "cs_shield_1":
                    print(f"setting shield to {actual_value}")
                    self.update_inner_shield(actual_value)
                elif attribute == "cs_isolation_1":
                    print(f"setting isolation to {actual_value}")
                    self.update_isolation(actual_value)
                elif attribute == "cs_output_1":
                    print(f"setting output to {actual_value}")
                    self.update_output(actual_value)
                elif attribute == "cs_curr_1":
                    print(f"setting curr to {actual_value}")
                    self.update_curr(actual_value)
                elif attribute == "cs_volt_1":
                    print(f"setting volt to {actual_value}")
                    self.update_volt(actual_value)
            sleep(0.000001)
        self.escape()
        print("CS580 1 Updated")

    # Same as update_link_1_xml() but for second CS580
    def update_link_2_xml(self, xml_update, xml_old_update):
        actual_config = xml_config_to_dict(xml_update)
        last_config = xml_config_to_dict(xml_old_update)
        self.update_link(2)
        sleep(0.005)
        for attribute, actual_value in actual_config.items():
            last_value = last_config.get(attribute)
            if actual_value != last_value:
                if attribute == "cs_gain_2":
                    print(f"setting gain to {actual_value}")
                    self.update_gain(actual_value)
                elif attribute == "cs_input_2":
                    print(f"setting input to {actual_value}")
                    self.update_input(actual_value)
                elif attribute == "cs_speed_2":
                    print(f"setting speed to {actual_value}")
                    self.update_speed(actual_value)
                elif attribute == "cs_shield_2":
                    print(f"setting shield to {actual_value}")
                    self.update_inner_shield(actual_value)
                elif attribute == "cs_isolation_2":
                    print(f"setting isolation to {actual_value}")
                    self.update_isolation(actual_value)
                elif attribute == "cs_output_2":
                    print(f"setting output to {actual_value}")
                    self.update_output(actual_value)
                elif attribute == "cs_curr_2":
                    print(f"setting curr to {actual_value}")
                    self.update_curr(actual_value)
                elif attribute == "cs_volt_2":
                    print(f"setting volt to {actual_value}")
                    self.update_volt(actual_value)
            sleep(0.000001)
        self.escape()
        print("CS580 2 Updated")

    # This will get every parameter from CS580 that is connected to the link number {link}, and return them.
    def all_report_link(self, link):
        self.escape()
        self.update_link(link)
        print(f'SX report, linked {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        sleep(0.005)
        gain = self.report_gain()
        input_val = self.report_input()
        speed = self.report_speed()
        shield = self.report_inner_shield()
        isolation = self.report_isolation()
        output = self.report_output()
        curr = self.report_curr()
        volt = self.report_volt()
        sleep(0.0001)
        self.escape()
        print(f'SX report, everything read {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        # print(f"CS link {link} report")
        return curr, volt, gain, input_val, speed, shield, isolation, output

    # Unused but may be useful function.
    # It sets link {link} port, calls function from parameter {func}, unlinks, and returns the value of {func} back.
    def get_value_for(self, link, func):
        self.escape()
        self.sx_ophyd.link.set(link)
        sleep(0.001)
        func_return_val = func()
        self.escape()
        return func_return_val

    # Unused but may be useful function.
    # It sets link on {link} port, calls function from parameter {func}, unlinks.
    def set_value_for(self, link, func, val):
        self.escape()
        self.sx_ophyd.link.set(link)
        sleep(0.001)
        func(val)
        self.escape()

    # Function will send termination character to SX199 that will unlink port.
    # Also clear status from errors if some occur (error may occur when there is no link, and you send termination
    # character to device anyway).
    def escape(self):
        self.sx_ophyd.escape.set('')
        self.sx_ophyd.clear_status.set('')

    def update_link(self, val):
        self.sx_ophyd.link.set(val)

    # This function won't probably work because every command is forwarded to linked port. Even the LINK? command like
    # this one.
    def report_link(self):
        link = self.sx_ophyd.link.get()
        return link

    def update_gain(self, val):
        self.sx_ophyd.cs_gain.set(val)

    def report_gain(self):
        return self.sx_ophyd.cs_gain.get()

    def update_input(self, val):
        self.sx_ophyd.cs_analog_in.set(val)

    def report_input(self):
        return self.sx_ophyd.cs_analog_in.get()

    def update_speed(self, val):
        self.sx_ophyd.cs_speed.set(val)

    def report_speed(self):
        return self.sx_ophyd.cs_speed.get()

    def update_inner_shield(self, val):
        self.sx_ophyd.cs_inner_shield.set(val)

    def report_inner_shield(self):
        return self.sx_ophyd.cs_inner_shield.get()

    def update_isolation(self, val):
        self.sx_ophyd.cs_isolation.set(val)

    def report_isolation(self):
        return self.sx_ophyd.cs_isolation.get()

    def update_output(self, val):
        self.sx_ophyd.cs_output.set(val)

    def report_output(self):
        return self.sx_ophyd.cs_output.get()

    def update_curr(self, val):
        self.sx_ophyd.cs_dc_curr.set(val)

    def report_curr(self):
        return self.sx_ophyd.cs_dc_curr.get()

    def update_volt(self, val):
        self.sx_ophyd.cs_comp_volt.set(val)

    def report_volt(self):
        volt = self.sx_ophyd.cs_comp_volt.get()
        return volt

    def update_alarm(self, val):
        self.sx_ophyd.cs_audible_alarm.set(val)

    def report_alarm(self):
        return self.sx_ophyd.cs_audible_alarm.get()

    def update_overload(self, val):
        self.sx_ophyd.cs_overload.set(val)

    def report_overload(self):
        return self.sx_ophyd.cs_overload.get()

    def report_id(self):
        return self.sx_ophyd.id.get()

    def stage(self) -> List[object]:
        return super().stage()

    def unstage(self) -> List[object]:
        return super().unstage()


if __name__ == "__main__":
    SX = SX199Device()
