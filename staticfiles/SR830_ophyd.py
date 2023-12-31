from typing import List

from staticfiles.instrbuilder.instrument_opening import open_by_name
from staticfiles.ophyd.ee_instruments import generate_ophyd_obj
from .XMLGenerator import xml_config_to_dict


# SR830 ophyd wrapper class
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
    # Connecting to it for 3 attempts
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
    def update_parameters(self, xml_update, xml_old_update):
        actual_config = xml_config_to_dict(xml_update)
        last_config = xml_config_to_dict(xml_old_update)
        for attribute, actual_value in actual_config.items():
            last_value = last_config.get(attribute)
            if actual_value != last_value:
                if attribute == "sensitivity":
                    print(f"setting sensitivity to {actual_value}")
                    self.write_sensitivity(actual_value)
                elif attribute == "time_constant":
                    print(f"setting time constant to {actual_value}")
                    self.write_time_constant(actual_value)
                elif attribute == "slope":
                    print(f"setting slope to {actual_value}")
                    self.write_slope(actual_value)
                elif attribute == "synch_filter":
                    print(f"setting synch filter to {actual_value}")
                    self.write_synch_filter(actual_value)
                elif attribute == "input":
                    print(f"setting input to {actual_value}")
                    self.write_input_config(actual_value)
                elif attribute == "couple":
                    print(f"setting couple to {actual_value}")
                    self.write_couple(actual_value)
                elif attribute == "shield":
                    print(f"setting shield to {actual_value}")
                    self.write_shield(actual_value)
                elif attribute == "freq_source":
                    print(f"setting freq source to {actual_value}")
                    self.write_reference_source(actual_value)
                elif attribute == "frequency":
                    print(f"setting frequency to {actual_value}")
                    self.write_freq(actual_value)
        print("SR830 Updated")

    def read_xyr0(self):
        """
        This function reads 4 values from SR. X, Y, R, 0 values. Returns them as string separated by commas. After
        splitting them to 4 variables it returns them.
        :return: X, Y, R, 0 values in variables
        """
        x, y, r, o = map(str, self.sr_ophyd.read_vals.get(configs={'i': '1', 'j': '2', 'k': ',3,4'}).split(','))
        return x, y, r, o

    def read_sensitivity(self):
        return self.sr_ophyd.sensitivity.get()

    def write_sensitivity(self, value):
        return self.sr_ophyd.sensitivity.set(value)

    def read_time_constant(self):
        return self.sr_ophyd.time_const.get()

    def write_time_constant(self, value):
        return self.sr_ophyd.time_const.set(value)

    def read_slope(self):
        return self.sr_ophyd.low_pass_filter_slope.get()

    def write_slope(self, value):
        return self.sr_ophyd.low_pass_filter_slope.set(value)

    def read_synch_filter(self):
        return self.sr_ophyd.synch_filter_status.get()

    def write_synch_filter(self, value):
        return self.sr_ophyd.synch_filter_status.set(value)

    def read_input_config(self):
        return self.sr_ophyd.in_conf.get()

    def write_input_config(self, value):
        return self.sr_ophyd.in_conf.set(value)

    def read_couple(self):
        return self.sr_ophyd.in_coupling.get()

    def write_couple(self, value):
        return self.sr_ophyd.in_coupling.set(value)

    def read_shield(self):
        return self.sr_ophyd.in_shield_gnd.get()

    def write_shield(self, value):
        return self.sr_ophyd.in_shield_gnd.set(value)

    def read_freq(self):
        return self.sr_ophyd.ref_freq.get()

    def write_freq(self, value):
        return self.sr_ophyd.ref_freq.set(value)

    def read_reference_source(self):
        return self.sr_ophyd.ref_source.get()

    def write_reference_source(self, value):
        return self.sr_ophyd.ref_source.set(value)

    def report_id(self):
        return self.sr_ophyd.id.get()

    def stage(self) -> List[object]:
        return super().stage()

    def unstage(self) -> List[object]:
        return super().unstage()


if __name__ == "__main__":
    SX = SR830Device()
