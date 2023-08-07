from datetime import datetime

from staticfiles.instrbuilder.instrument_opening import open_by_name
from staticfiles.ophyd.ee_instruments import generate_ophyd_obj
from typing import List
from .XMLGenerator import xml_config_to_dict
from time import sleep


# SX199Device class with functions to connect control and to get parameters of one, or two CS580 current sources.
# We connect to the SX199 through the network, then we can control current sources with this class.
# The commands in csv file are not only SX199 commands. There are also CS580 commands. This could be approached with
# CS580 class as well, but this approach is also efficient.
# Sleep commands might be confusing. I have tested this with CS580 and if I link to desired port number without delay
# after that, the next command is ignored and does not return anything. I don't know what's the cause.
class SR830Device():
    def __init__(self, name='sr830', **kwargs):
        self.name = name
        if name == None:
            self.name = 'sr830'
        self.sr_instr = None
        self.sr_ophyd = None
        # Initialize variables then connect
        self.connect()

    # Connect function for checking if connection is not already established, and connecting if not.
    # I have bad experience with open_by_name() function, when it doesn't connect until 3rd try when in Jupyter
    # Notebook. Therefore, the for loop with 3 attempts to connect.
    def connect(self):
        if self.sr_instr is not None and self.sr_ophyd is not None and self.is_connected():
            return True
        for _ in range(3):
            # Open by name function is from Instrbuilder library.
            self.sr_instr = open_by_name(name=self.name)
            self.sr_instr.name = self.name

            # Ophyd function to create ophyd object. We will be using mainly that
            SR, component_dict = generate_ophyd_obj(name=self.name, scpi_obj=self.sr_instr)
            self.sr_ophyd = SR(name=self.name)

            # Making sure connection was established.
            if self.is_connected():
                print(f"{self.report_id()} connected")
                return True
        return False

    # Closing PyVisa connection and setting both objects to None
    def disconnect(self):
        try:
            self.sr_instr.comm_handle.close()
        except:
            print('Disconnecting error: Object does not have Socket opened.')

    # Checking if device is connected is made by comparing returned string from get ID (*IDN? command)
    def is_connected(self):
        id_string = self.sr_ophyd.id.get()
        return id_string.startswith("Stanford_Research_Systems,SR830")

    # Updating parameters could be expensive operation if there is 8 of them. That's why I compare 2 xml files with
    # last set parameters, and parameters set now. This will compare two xml files and set only the values, that are
    # different from the last updating.
    # Only for first CS580
    """def update_link_1_xml(self, xml_update, xml_old_update):
        actual_config = xml_config_to_dict(xml_update)
        last_config = xml_config_to_dict(xml_old_update)
        self.update_link(1)
        sleep(0.0001)
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
        print("CS580 1 Updated")"""

    # This will get every parameter from CS580 that is connected to the link number {link}, and return them.
    """def all_report_link(self, link):
        self.escape()
        self.update_link(link)
        print(f'SX report, linked {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        sleep(0.0001)
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
        return curr, volt, gain, input_val, speed, shield, isolation, output"""

    def read_xyr0(self):
        x, y, r, o = map(str, self.sr_ophyd.read_vals.get(configs={'i': '1', 'j': '2', 'k': ',3,4'}).split(','))
        return x, y, r, o

    def read_sensitivity(self):
        return self.sr_ophyd.sensitivity.get()

    def report_id(self):
        return self.sr_ophyd.id.get()

    def stage(self) -> List[object]:
        return super().stage()

    def unstage(self) -> List[object]:
        return super().unstage()


if __name__ == "__main__":
    SX = SR830Device()
