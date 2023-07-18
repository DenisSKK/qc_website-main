from XMLGenerator import xml_config_to_dict

rfsoc_config = xml_config_to_dict("staticfiles/xilinx.xml")
print(rfsoc_config)