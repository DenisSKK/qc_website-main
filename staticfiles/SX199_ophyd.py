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

class SX199Device():
    def __init__(self, name='sx199', **kwargs):
        self.name = name
        if name == None:
            self.name = 'sx199'
        self.connect(name=name)

    def connect(self, name):
        # for _ in range(4):
        self.sx = open_by_name(name=name)
        self.sx.name = name

        SX, component_dict = generate_ophyd_obj(name=name, scpi_obj=self.sx)
        self.sx_o = SX(name=name)

        if self.is_connected():
            print(f"{self.report_id()} connected")
            return True
        return False

    def disconnect(self):
        self.sx.close()

    def is_connected(self):
        id_string = self.sx_o.id.get()
        return id_string.startswith("Stanford_Research_Systems,SX199")

    def is_cs_connected(self, link):
        self.sx_o.link.set(1)
        id_string = self.sx_o.id.get()
        return id_string.startswith("Stanford_Research_Systems,CS580")

    def is_linked(self):
        if self.sx_o.link.get() != 0:
            return True
        elif self.sx_o.link.get() == 0:
            return False
        return False

    def update_link_1_xml(self, xml_update, xml_old_update):
        # if not self.is_connected():
        #     if not self.connect(self.name):
        #         print("SX199 is not connected")
        #         return
        # Load the configurations from the XML files
        actual_config = xml_config_to_dict(xml_update)
        last_config = xml_config_to_dict(xml_old_update)

        # Compare the attributes and update only the ones that are different
        for attribute, actual_value in actual_config.items():
            last_value = last_config.get(attribute)

            if actual_value != last_value:
                if attribute == "cs_gain_1":
                    self.set_value_for(1, self.update_gain, str(actual_value))
                elif attribute == "cs_input_1":
                    self.set_value_for(1, self.update_input, str(actual_value))
                elif attribute == "cs_speed_1":
                    self.set_value_for(1, self.update_speed, str(actual_value))
                elif attribute == "cs_shield_1":
                    self.set_value_for(1, self.update_inner_shield, str(actual_value))
                elif attribute == "cs_isolation_1":
                    self.set_value_for(1, self.update_isolation, str(actual_value))
                elif attribute == "cs_output_1":
                    self.set_value_for(1, self.update_output, str(actual_value))
                elif attribute == "cs_curr_1":
                    self.set_value_for(1, self.update_curr, str(actual_value))
                elif attribute == "cs_volt_1":
                    self.set_value_for(1, self.update_volt, str(actual_value))
        print("SX199 Updated")

    def update_link_2_xml(self, xml_update, xml_old_update):
        # if not self.is_connected():
        #     if not self.connect(self.name):
        #         print("SX199 is not connected")
        #         return
        # Load the configurations from the XML files
        actual_config = xml_config_to_dict(xml_update)
        last_config = xml_config_to_dict(xml_old_update)

        # Compare the attributes and update only the ones that are different
        for attribute, actual_value in actual_config.items():
            last_value = last_config.get(attribute)

            if actual_value != last_value:
                if attribute == "cs_gain_2":
                    self.set_value_for(2, self.update_gain, str(actual_value))
                elif attribute == "cs_input_2":
                    self.set_value_for(2, self.update_input, str(actual_value))
                elif attribute == "cs_speed_2":
                    self.set_value_for(2, self.update_speed, str(actual_value))
                elif attribute == "cs_shield_2":
                    self.set_value_for(2, self.update_inner_shield, str(actual_value))
                elif attribute == "cs_isolation_2":
                    self.set_value_for(2, self.update_isolation, str(actual_value))
                elif attribute == "cs_output_2":
                    self.set_value_for(2, self.update_output, str(actual_value))
                elif attribute == "cs_curr_2":
                    self.set_value_for(2, self.update_curr, str(actual_value))
                elif attribute == "cs_volt_2":
                    self.set_value_for(2, self.update_volt, str(actual_value))
        print("SX199 Updated")


    def get_value_for(self, link, func):
        if self.is_connected():
            print('inside get_value_for()')
            self.update_link(link)
            func_return_val = func()
            self.escape()
            return func_return_val
        else:
            print("Device is not connected.")

    def set_value_for(self, link, func, val):
        if self.is_connected():
            self.sx_o.link.set(link)
            func(val)
            self.escape()
        else:
            print("Device is not connected.")

    def escape(self):
        self.sx_o.escape.set('')
        self.sx_o.clear_status.set('')

    def update_link(self, val):
        self.sx_o.link.set(val)
    def report_link(self):
        link = self.sx_o.link.get()
        return link

    def update_gain(self, val):
        print(f'inside update_gain() {val}')
        self.sx_o.cs_gain.set(val)
        print('')
        # print(self.sx_o.id.get())
        # print(f'update_gain id call {self.sx_o.id.get()}')

    def report_gain(self):
        print('inside report_gain()')
        return self.sx_o.cs_gain.get()
        # return self.

    def update_input(self, val):
        self.sx_o.cs_analog_in.set(val)
    def report_input(self):
        return self.sx_o.cs_analog_in.get()

    def update_speed(self, val):
        self.sx_o.cs_speed.set(val)
    def report_speed(self):
        return self.sx_o.cs_speed.get()

    def update_inner_shield(self, val):
        self.sx_o.cs_inner_shield.set(val)
    def report_inner_shield(self):
        return self.sx_o.cs_inner_shield.get()

    def update_isolation(self, val):
        self.sx_o.cs_isolation.set(val)
    def report_isolation(self):
        return self.sx_o.cs_isolation.get()

    def update_output(self, val):
        self.sx_o.cs_output.set(val)
    def report_output(self):
        return self.sx_o.cs_output.get()

    def update_curr(self, val):
        self.sx_o.cs_dc_curr.set(val)
    def report_curr(self):
        return self.sx_o.cs_dc_curr.get()

    def update_volt(self, val):
        self.sx_o.cs_comp_volt.set(val)
    def report_volt(self):
        return self.sx_o.cs_comp_volt.get()

    def update_alarm(self, val):
        self.sx_o.cs_audible_alarm.set(val)
    def report_alarm(self):
        return self.sx_o.cs_audible_alarm.get()

    def update_overload(self, val):
        self.sx_o.cs_overload.set(val)
    def report_overload(self):
        return self.sx_o.cs_overload.get()

    def report_id(self):
        return self.sx_o.id.get()

    def stage(self) -> List[object]:
        return super().stage()

    def unstage(self) -> List[object]:
        return super().unstage()


if __name__ == "__main__":
    SX = SX199Device()
