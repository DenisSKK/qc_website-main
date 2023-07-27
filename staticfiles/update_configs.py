from .XMLGenerator import xml_config_to_dict, dict_to_xml
import os
import ruamel.yaml
import xml.etree.ElementTree as Et

config_file_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
config_file_dest = os.path.expanduser("~/.instrbuilder/config.yaml")
# Read data from staticfiles/config.yaml
yaml_src = ruamel.yaml.YAML()
with open(config_file_src, "r") as f:
    config_data_src = yaml_src.load(f)


def update_configs():
    update_sx_config()
    update_itc_config()
    update_rfsoc_config()
    update_toptica_config()
    update_caylar_config()


def update_sx_config():
    # Extract sx199 host and port
    sx199_host = config_data_src["instruments"]["sx199"]["host"]
    sx199_port = config_data_src["instruments"]["sx199"]["port"]

    # Create path for .instrbuilder/config.yaml and yaml object
    yaml_dest = ruamel.yaml.YAML()

    # Read the .instrbuilder/config.yaml file
    with open(config_file_dest, "r") as f:
        config_data_dest = yaml_dest.load(f)

    # Update the pyvisa section for sx199 in .instrbuilder/config.yaml
    config_data_dest["instruments"]["sx199"]["address"]["pyvisa"] = f"TCPIP::{sx199_host}::{sx199_port}::SOCKET"

    # Write the updated config_data_dest back to the .instrbuilder/config.yaml file
    with open(config_file_dest, "w") as f:
        yaml_dest.dump(config_data_dest, f)


def update_itc_config():
    # Extract itc host and port
    itc_host = config_data_src["instruments"]["itc"]["host"]
    itc_port = config_data_src["instruments"]["itc"]["port"]

    # Create path for staticfiles/mercuryITC.xml
    itc_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mercuryITC.xml")

    # Update the host and port in staticfiles/mercuryITC.xml
    itc_config_dict = xml_config_to_dict(itc_config_path)
    itc_config_dict['host'] = itc_host
    itc_config_dict['port'] = itc_port
    dict_to_xml(itc_config_dict, itc_config_path)


def update_rfsoc_config():
    # Read data from staticfiles/config.yaml
    yaml_src = ruamel.yaml.YAML()
    with open(config_file_src, "r") as f:
        config_data_src = yaml_src.load(f)

    # Extract itc host and port
    rfsoc_host = config_data_src["instruments"]["rfsoc"]["host"]
    rfsoc_username = config_data_src["instruments"]["rfsoc"]["username"]
    rfsoc_password = config_data_src["instruments"]["rfsoc"]["password"]

    # Create path for staticfiles/xilinx_host.xml
    rfsoc_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xilinx_host.xml")

    # Update the host and port in staticfiles/xilinx_host.xml
    rfsoc_config_dict = xml_config_to_dict(rfsoc_config_path)
    rfsoc_config_dict['host'] = rfsoc_host
    rfsoc_config_dict['username'] = rfsoc_username
    rfsoc_config_dict['password'] = rfsoc_password
    dict_to_xml(rfsoc_config_dict, rfsoc_config_path)


def update_toptica_config():

    # Extract itc host and port
    toptica_host = config_data_src["instruments"]["toptica"]["host"]
    toptica_port = config_data_src["instruments"]["toptica"]["port"]

    # Create path for staticfiles/toptica.xml
    toptica_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "toptica.xml")

    # Update the host and port in staticfiles/toptica.xml
    toptica_config_dict = xml_config_to_dict(toptica_config_path)
    toptica_config_dict['host'] = toptica_host
    toptica_config_dict['port'] = toptica_port
    dict_to_xml(toptica_config_dict, toptica_config_path)


def update_caylar_config():
    # Extract itc host and port
    caylar_host = config_data_src["instruments"]["caylar"]["host"]
    caylar_port = config_data_src["instruments"]["caylar"]["port"]

    # Create path for staticfiles/caylar.xml
    caylar_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "caylar.xml")

    # Update the host and port in staticfiles/caylar.xml
    caylar_config_dict = xml_config_to_dict(caylar_config_path)
    caylar_config_dict['host'] = caylar_host
    caylar_config_dict['port'] = caylar_port
    dict_to_xml(caylar_config_dict, caylar_config_path)
