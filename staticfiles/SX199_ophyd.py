from staticfiles.instrbuilder.instrument_opening import open_by_name
from staticfiles.ophyd.ee_instruments import generate_ophyd_obj
from typing import List


class SX199Device():
    def __init__(self, name='sx199', **kwargs):
        if name == None:
            name = 'sx199'
        sx = open_by_name(name=name)
        sx.name = name

        SX, component_dict = generate_ophyd_obj(name=name, scpi_obj=sx)
        self.sx_o = SX(name=name)

    def is_connected(self):
        id_string = self.sx_o.id.get()
        return id_string.startswith("Stanford_Research_Systems,SX199")

    def update_all_xml(self, xml):
        from .XMLGenerator import xml_config_to_dict
        try:
            self.config = xml_config_to_dict(xml)
            try:
                self.update_link(self.config["link"])
            except:
                print("Updating link failed")
            print("SX199 Updated")
        except:
            print("XML not Found")

    def update_link(self, val):
        self.sx_o.link(val)

    def report_link(self):
        link = self.sx_o.link.get()
        ret_str = ''

        if link == 0:
            ret_str = 'No link established'
        else:
            r = link // 10
            p = link % 10

            if r == 1:
                ret_str = f'RS-232 linked to port {p}'
            elif r == 2:
                ret_str = f'GPIB linked to port {p}'
            elif r == 3:
                ret_str = f'Ethernet linked to port {p}'

        return ret_str

    def report_id(self):
        return self.sx_o.id.get()

    def stage(self) -> List[object]:
        return super().stage()

    def unstage(self) -> List[object]:
        return super().unstage()


if __name__ == "__main__":
    SX = SX199Device()
