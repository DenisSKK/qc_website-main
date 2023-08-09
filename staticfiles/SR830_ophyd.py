from datetime import datetime

from staticfiles.instrbuilder.instrument_opening import open_by_name
from staticfiles.ophyd.ee_instruments import generate_ophyd_obj
from typing import List
from .XMLGenerator import xml_config_to_dict
from time import sleep


SENSITIVITY_CHOICES = {
    0: '2nV/fA',
    1: '5nV/fA',
    2: '10nV/fA',
    3: '20nV/fA',
    4: '50nV/fA',
    5: '100nV/fA',
    6: '200nV/fA',
    7: '500nV/fA',
    8: '1µV/pA',
    9: '2µV/pA',
    10: '5µV/pA',
    11: '10µV/pA',
    12: '20µV/pA',
    13: '50µV/pA',
    14: '100µV/pA',
    15: '200µV/pA',
    16: '500µV/pA',
    17: '1mV/nA',
    18: '2mV/nA',
    19: '5mV/nA',
    20: '10mV/nA',
    21: '20mV/nA',
    22: '50mV/nA',
    23: '100mV/nA',
    24: '200mV/nA',
    25: '500mV/nA',
    26: '1V/µA',
}

TIME_CONSTANT_CHOICES = {
    0: '10µs',
    1: '30µs',
    2: '100µs',
    3: '300µs',
    4: '1ms',
    5: '3ms',
    6: '10ms',
    7: '30ms',
    8: '100ms',
    9: '300ms',
    10: '1s',
    11: '3s',
    12: '10s',
    13: '30s',
    14: '100s',
    15: '300s',
    16: '1ks',
    17: '3ks',
    18: '10ks',
    19: '30ks',
}

SLOPE_CHOICES = {
    0: '6 dB/oct',
    1: '12 dB/oct',
    2: '18 dB/oct',
    3: '24 dB/oct',
}

INPUT_CHOICES = {
    0: 'A',
    1: 'A-B',
    2: 'I(1MΩ)',
    3: 'I(100MΩ)',
}

ON_OFF_CHOICES = {
    0: 'OFF',
    1: 'ON',
}

COUPLE_CHOICES = {
    0: 'AC',
    1: 'DC',
}

SHIELD_CHOICES = {
    0: 'Float',
    1: 'Ground',
}

FREQ_SOURCE_CHOICES = {
    0: 'External',
    1: 'Internal',
}

class SR830Device:
    """
    SR830 Lock in amplifier ophyd wrapper made for ophyd object made with instrbuilder
    """
    def __init__(self, name='sr830', **kwargs):
        self.name = name
        if name == None:
            self.name = 'sr830'
        self.sr_instr = None
        self.sr_ophyd = None
        # Get a list of all methods and attributes in the class
        all_members = dir(SR830Device)
        # Filter only the methods you consider useful
        self.device_read_functions = [member for member in all_members if member.startswith('read_')]
        self.device_write_functions = [member for member in all_members if member.startswith('write_')]
        # Initialize variables then connect
        self._connected = False
        self.connect()

    #
    #
    #
    def connect(self):
        """
        Connect function for checking if connection is not already established, and connecting if not.
        I have bad experience with open_by_name() function, when it doesn't connect until 3rd try when in Jupyter
        Notebook. Therefore, the for loop with 3 attempts to connect.
        :return: True if connection was successful and *IDN? works. False if not
        """
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

    def disconnect(self):
        """
        Closing PyVisa connection
        """
        try:
            self.sr_instr.comm_handle.close()
        except:
            print('Disconnecting error: Object does not have Socket opened.')

    def is_connected(self):
        """
        Checking if device is connected by comparing returned string from get ID (*IDN? command)
        Value True or False will also be saved into _connected
        :return: True if *IDN? works. False if not.
        """
        self._connected = self.sr_ophyd.id.get().startswith("Stanford_Research_Systems,SR830")
        return self._connected

    def update_parameters(self, xml_update, xml_old_update):
        """
        Updating parameters could be expensive operation if there is many of them. That's why I compare 2 xml files with
        last set parameters, and parameters set now. This will compare two xml files and set only the values, that are
        different from the last updating.
        :param xml_update: XML file with new values to set
        :param xml_old_update: XML file with values that were set last time
        """
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
        
    def read_device_data(self):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        x_val, y_val, r_val, o_val = self.read_xyr0()
        sens_val = self.read_sensitivity()
        sens_label = SENSITIVITY_CHOICES.get(sens_val, sens_val)
        time_const_val = self.read_time_constant()
        time_const_label = TIME_CONSTANT_CHOICES.get(time_const_val, time_const_val)
        slope_val = self.read_slope()
        slope_label = SLOPE_CHOICES.get(slope_val, slope_val)
        synch_filter_val = self.read_synch_filter()
        synch_filter_label = ON_OFF_CHOICES.get(synch_filter_val, synch_filter_val)
        input_config_val = self.read_input_config()
        input_label = INPUT_CHOICES.get(input_config_val, input_config_val)
        couple_val = self.read_couple()
        couple_label = COUPLE_CHOICES.get(couple_val, couple_val)
        shield_val = self.read_shield()
        shield_label = SHIELD_CHOICES.get(shield_val, shield_val)
        freq_val = self.read_freq()
        ref_source_val = self.read_reference_source()
        ref_source_label = FREQ_SOURCE_CHOICES.get(ref_source_val, ref_source_val)
        data = [timestamp, x_val, y_val, r_val, o_val, sens_label, time_const_label, slope_label,
                       synch_filter_label, input_label, couple_label, shield_label, freq_val, ref_source_label]
        header = ['timestamp', 'x_value', 'y_value', 'r_value', 'O_value', 'sensitivity', 'time_constant', 'slope',
                  'synch_filter', 'input_config', 'couple', 'shield', 'frequency', 'frequency_source']
        return data, header

    def read_xyr0(self):
        """
        Read all X, Y, R, 0 values together with SNAP command for SR and then split it into 4 variables.
        :return: values of X, Y, R, 0 from the device
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
