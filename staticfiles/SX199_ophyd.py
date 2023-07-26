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

    def connect(self):
        for _ in range(4):
            self.sx_instr = open_by_name(name=self.name)
            self.sx_instr.name = self.name

            SX, component_dict = generate_ophyd_obj(name=self.name, scpi_obj=self.sx_instr)
            self.sx_ophyd = SX(name=self.name)

            if self.is_connected():
                print(f"{self.report_id()} connected")
                return True
            return False

    def disconnect(self):
        self.sx_instr.comm_handle.close()

    def is_connected(self):
        id_string = self.sx_ophyd.id.get()
        return id_string.startswith("Stanford_Research_Systems,SX199")

    def is_cs_connected(self, link):
        self.escape()
        self.update_link(link)
        sleep(0.001)
        try:
            id_string = self.sx_ophyd.id.get()
        except:
            return False
        sleep(0.000001)
        self.escape()
        print(f'check: {id_string}')
        return id_string.startswith("Stanford_Research_Systems,CS580")

    def update_link_1_xml(self, xml_update, xml_old_update):
        actual_config = xml_config_to_dict(xml_update)
        last_config = xml_config_to_dict(xml_old_update)
        self.update_link(1)
        sleep(0.001)
        for attribute, actual_value in actual_config.items():
            last_value = last_config.get(attribute)
            if actual_value != last_value:
                if attribute == "cs_gain_1":
                    print(f"setting gain to {actual_value}")
                    self.set_value_for(1, self.update_gain, str(actual_value))
                elif attribute == "cs_input_1":
                    print(f"setting input to {actual_value}")
                    self.set_value_for(1, self.update_input, str(actual_value))
                elif attribute == "cs_speed_1":
                    print(f"setting speed to {actual_value}")
                    self.set_value_for(1, self.update_speed, str(actual_value))
                elif attribute == "cs_shield_1":
                    print(f"setting shield to {actual_value}")
                    self.set_value_for(1, self.update_inner_shield, str(actual_value))
                elif attribute == "cs_isolation_1":
                    print(f"setting isolation to {actual_value}")
                    self.set_value_for(1, self.update_isolation, str(actual_value))
                elif attribute == "cs_output_1":
                    print(f"setting output to {actual_value}")
                    self.set_value_for(1, self.update_output, str(actual_value))
                elif attribute == "cs_curr_1":
                    print(f"setting curr to {actual_value}")
                    self.set_value_for(1, self.update_curr, actual_value)
                elif attribute == "cs_volt_1":
                    print(f"setting volt to {actual_value}")
                    self.set_value_for(1, self.update_volt, actual_value)
            sleep(0.000001)
        self.escape()
        print("CS580 1 Updated")

    def update_link_2_xml(self, xml_update, xml_old_update):
        actual_config = xml_config_to_dict(xml_update)
        last_config = xml_config_to_dict(xml_old_update)
        self.update_link(2)
        sleep(0.001)
        for attribute, actual_value in actual_config.items():
            last_value = last_config.get(attribute)
            if actual_value != last_value:
                if attribute == "cs_gain_2":
                    print(f"setting gain to {actual_value}")
                    self.set_value_for(2, self.update_gain, str(actual_value))
                elif attribute == "cs_input_2":
                    print(f"setting input to {actual_value}")
                    self.set_value_for(2, self.update_input, str(actual_value))
                elif attribute == "cs_speed_2":
                    print(f"setting speed to {actual_value}")
                    self.set_value_for(2, self.update_speed, str(actual_value))
                elif attribute == "cs_shield_2":
                    print(f"setting shield to {actual_value}")
                    self.set_value_for(2, self.update_inner_shield, str(actual_value))
                elif attribute == "cs_isolation_2":
                    print(f"setting isolation to {actual_value}")
                    self.set_value_for(2, self.update_isolation, str(actual_value))
                elif attribute == "cs_output_2":
                    print(f"setting output to {actual_value}")
                    self.set_value_for(2, self.update_output, str(actual_value))
                elif attribute == "cs_curr_2":
                    print(f"setting curr to {actual_value}")
                    self.set_value_for(2, self.update_curr, actual_value)
                elif attribute == "cs_volt_2":
                    print(f"setting volt to {actual_value}")
                    self.set_value_for(2, self.update_volt, actual_value)
            sleep(0.000001)
        self.escape()
        print("CS580 2 Updated")

    from time import sleep

    def all_report_link(self, link):
        self.escape()
        self.update_link(link)
        sleep(0.001)
        gain = self.report_gain()
        input_val = self.report_input()
        speed = self.report_speed()
        shield = self.report_inner_shield()
        isolation = self.report_isolation()
        output = self.report_output()
        curr = self.report_curr()
        volt = self.report_volt()
        sleep(0.001)
        self.escape()
        print(f"CS link {link} report")
        return gain, input_val, speed, shield, isolation, output, curr, volt

    def get_value_for(self, link, func):
        self.escape()
        self.sx_ophyd.link.set(link)
        sleep(0.001)
        func_return_val = func()
        self.escape()
        return func_return_val

    def set_value_for(self, link, func, val):
        # if self.is_connected():
            # self.sx_o.link.set(link)
        func(val)
            # self.escape()
        # else:
        #     print("Device is not connected.")

    def escape(self):
        self.sx_ophyd.escape.set('')
        self.sx_ophyd.clear_status.set('')

    def update_link(self, val):
        self.sx_ophyd.link.set(val)
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
