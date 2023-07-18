from XMLGenerator import xml_config_to_dict, dict_to_xml_file
from datetime import datetime
config_laser = xml_config_to_dict("staticfiles/xilinx.xml")
print(config_laser)
config_laser["time_update"] =  datetime.now().strftime("%d/%m/%Y %H:%M:%S")


dict_to_xml_file(config_laser, r"staticfiles/xilinx.xml")
config_laser = xml_config_to_dict("staticfiles/xilinx.xml")

print(config_laser)