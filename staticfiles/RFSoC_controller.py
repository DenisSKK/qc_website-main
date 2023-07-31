from .ssh import SSH
import os
from .XMLGenerator import xml_config_to_dict, dict_to_xml_file

from .create_json import import_json_file, save_list_to_json_file

class RFSoC_controller:
    def __init__(self, host="", username="xilinx", password="xilinx", config_host=None):
        if config_host==None:
            self.host = host
            self.username = username
            self.password = password
        else:
            self.host = config_host["host"]
            self.username = config_host["username"]
            self.password = config_host["password"]
        self.RFSoC = SSH(self.host,self.username,self.password)
        # self.try_connect()

    def try_connect(self):
        """
        The function "try_connect" attempts to establish a connection with an RFSoC device and returns
        True if successful, or False if not.
        @returns a boolean value. If the connection is successfully established, it returns True. If the
        connection cannot be established, it returns False.
        """
        try:
            self.RFSoC.connect()
            print("Connection was established")
            return True
        except:
            print("Connection cannot be established")
            return False

    def disconnect(self):
        """
        The function disconnect() is used to disconnect from an RFSoC device.
        """
        self.RFSoC.disconnect()

    def build_config(self, config=None):
        """
        The function `build_config` builds a configuration file based on the provided input and
        transfers it to an RFSoC device.
        @param config - The `config` parameter is a dictionary that contains the configuration settings
        for the `build_config` method. It has the following structure:
        """
        if not self.get_config():
            if config==None:
                self.configEOM={"freq_seq0": [1,1,2],
                        "gain_seq0": [1,1,2],
                        "time_seq0":[190,370,700],
                        "length0":100, # [Clock ticks]
                        "length1":100, # [Clock ticks]
                        # "pulse_freq":{"freq":1000, "gen_ch":0, "ro_ch":0}, #readout freq
                        "zone0": 1,
                        "mode0": "periodic",
                        "zone1": 1,
                        "mode1": "periodic",
                }

                #TTL
                self.configAOM={
                        "length":[[200,200,200,200],[200,200,200,200],[200,200,200,200],[200,200,200,200]], # [Clock ticks]
                        "pins":[1,2,0,3],
                        "time":[[0,400,800,1200],[0,400,800,1200],[0,400,800,1200],[0,400,800,1200]],
                        "timeseqformttl": [1.0, 1.0, 2.0],
                        "pinsformttl": [[0], [1, 2], [0, 1]],
                        "lengthseqttl": [1.0, 1.0, 4.0]
                }
                self.configG= {
                "adc_trig_offset": 100, # [Clock ticks]
                "soft_avgs":1,
                "relax_delay":1.0, # --us
                #Readout
                "readout_length": 2000, # [Clock ticks]
                "pulse_freq":{"freq":1000, "gen_ch":0, "ro_ch":0},
                "reps":1, # --Fixed
                }
            else:
                print("Config Receive")
                self.configEOM={"freq_seq0": config["EOM"]["freq_seq0"],
                        "gain_seq0": config["EOM"]["gain_seq0"],
                        "time_seq0":config["EOM"]["time_seq0"],
                        "length0":config["EOM"]["length0"], # [Clock ticks]
                        "length1":config["EOM"]["length1"], # [Clock ticks]
                        "zone0": config["EOM"]["zone0"],
                        "mode0": config["EOM"]["mode0"],
                        "zone1": config["EOM"]["zone1"],
                        "mode1": config["EOM"]["mode1"],
                }

                #TTL
                self.configAOM={
                        "length":config["AOM"]["length"], # [Clock ticks]
                        "pins":config["AOM"]["pins"],
                        "time":config["AOM"]["time"],
                        "timeseqformttl": config["AOM"]["timeseqformttl"],
                        "pinsformttl": config["AOM"]["pinsformttl"],
                        "lengthseqttl": config["AOM"]["lengthseqttl"]
                }
                self.configG= {
                "adc_trig_offset": config["adc_trig_offset"], # [Clock ticks]
                "soft_avgs":config["soft_avgs"],
                "relax_delay":config["relax_delay"], # --us
                #Readout
                "readout_length": config["readout_length"], # [Clock ticks]
                "pulse_freq":{"freq":config["pulse_freq"], "gen_ch":0, "ro_ch":0},
                "reps":config["reps"], # --Fixed
                }
            file_name = "staticfiles/config_file.py"
            file_content ='''
from qick import *
from qick.parser import load_program
# Load bitstream with custom overlay
soc = QickSoc()

soccfg = soc
configEOM={"freq_seq0": '''+str(self.configEOM["freq_seq0"])+''',
        "gain_seq0": '''+str(self.configEOM["gain_seq0"])+''',
        "time_seq0":'''+str(self.configEOM["time_seq0"])+''',
        "length0":'''+str(self.configEOM["length0"])+''', # [Clock ticks]
        "length1":'''+str(self.configEOM["length1"])+''', # [Clock ticks]
        "zone0": '''+str(self.configEOM["zone0"])+''',
        "mode0": "'''+str(self.configEOM["mode0"])+'''",
        "zone1": '''+str(self.configEOM["zone1"])+''',
        "mode1": "'''+str(self.configEOM["mode1"])+'''",
}

#TTL
configAOM={
        "length":'''+str(self.configAOM["length"])+''', # [Clock ticks]
        "pins":'''+str(self.configAOM["pins"])+''',
        "time":'''+str(self.configAOM["time"])+''',
        "timeseqformttl":'''+str(self.configAOM["timeseqformttl"])+''',
        "pinsformttl":'''+str(self.configAOM["pinsformttl"])+''',
        "lengthseqttl":'''+str(self.configAOM["lengthseqttl"])+''',
}
config= {
"adc_trig_offset": '''+str(self.configG["adc_trig_offset"])+''', # [Clock ticks]
"soft_avgs":'''+str(self.configG["soft_avgs"])+''',
"relax_delay":'''+str(self.configG["relax_delay"])+''', # --us
#Readout
"readout_length": '''+str(self.configG["readout_length"])+''', # [Clock ticks]
"pulse_freq":soccfg.adcfreq('''+str(self.configG["pulse_freq"]["freq"])+''', gen_ch='''+str(self.configG["pulse_freq"]["gen_ch"])+''', ro_ch='''+str(self.configG["pulse_freq"]["ro_ch"])+'''),
"reps":'''+str(self.configG["reps"])+''', # --Fixed
"EOM":configEOM,
"AOM":configAOM
}

from XMLGenerator import dict_to_xml_file,xml_config_to_dict
dict_to_xml_file(config, "xilinx.xml")
'''
            # Open the file in write mode and write the content
            with open(file_name, "w") as file:
                    file.write(file_content)
            self.RFSoC.transfer_file(r"staticfiles/config_file.py",r"/home/xilinx/jupyter_notebooks/qick/qick_demos/ssh_control/config_file.py")
            self.RFSoC.run_code("config_file")
            self.RFSoC.download_file(r"/home/xilinx/jupyter_notebooks/qick/qick_demos/ssh_control/xilinx.xml",r"staticfiles/xilinx.xml")
    def update_config(self):
        """
        The function updates the configuration file on an RFSoC device and downloads an XML file.
        """
        self.RFSoC.transfer_file(r"staticfiles/config_file.py",r"/home/xilinx/jupyter_notebooks/qick/qick_demos/ssh_control/config_file.py")
        self.RFSoC.run_code("config_file")
        self.RFSoC.download_file(r"/home/xilinx/jupyter_notebooks/qick/qick_demos/ssh_control/xilinx.xml",r"staticfiles/xilinx.xml")
    def run_code(self):
        """
        The function `run_code` builds a configuration, transfers a file, and runs code on an RFSoC
        device.
        """
        self.build_config()
        self.RFSoC.transfer_file(r"staticfiles/config_file.py",r"/home/xilinx/jupyter_notebooks/qick/qick_demos/ssh_control/config_file.py")
        self.RFSoC.run_code("RFSoC")

    def get_config(self,print=False):
        """
        The function `get_config` downloads an XML file and converts it to a dictionary, and optionally
        prints the dictionary.
        @param [print=False] - The `print` parameter is a boolean flag that determines whether the
        configuration should be printed or not. If `print` is set to `True`, the configuration will be
        printed. If `print` is set to `False`, the configuration will not be printed.
        @returns a boolean value. If the file path does not exist or if there is an exception while
        parsing the XML file, it returns False. Otherwise, if the "print" parameter is set to True, it
        prints the configuration and returns True.
        """
        file_path = "staticfiles/xilinx.xml"  # Replace with the actual file path

        if not os.path.exists(file_path):
            try:
                self.RFSoC.download_file(r"/home/xilinx/jupyter_notebooks/qick/qick_demos/ssh_control/xilinx.xml",r"staticfiles/xilinx.xml")
            except Exception as e:
                return False
        try:
            self.config = xml_config_to_dict(file_path)
            if print:
                print(self.config)
                return True

        except Exception as e:
            return False

    def set_config(self, category, key,value="",delete=False): #EXCEPT FREQUENCY FOR EOM ONLY FOR TTL AND GENERAL EOM AND AOM
        """
        The `set_config` function sets or deletes configuration values in a dictionary and saves the
        dictionary as an XML file.
        @param category - The "category" parameter is used to specify the category of the configuration
        setting. It can have the following values:
        @param key - The "key" parameter is a string that represents the specific configuration setting
        that you want to set or delete. It is used as a key to access the corresponding value in the
        configuration dictionary.
        @param value - The "value" parameter is the value that you want to set for the specified key in
        the configuration. It is optional and can be left empty if you want to delete the key instead.
        @param [delete=False] - The `delete` parameter is a boolean flag that determines whether to
        delete a configuration key or not. If `delete` is set to `True`, the specified key will be
        deleted from the configuration. If `delete` is set to `False`, the specified key will be set to
        the provided value
        @returns the string "Configuration set successfully".
        """
        if category == "G":
            try:
                if delete:
                    del self.config[key]
                else:
                    self.config[key] =value
            except Exception as e:
                # Exception handling code
                print(f"An error occurred: {str(e)}")
        elif category == "EOM":
            try:
                if delete:
                    del self.config["EOM"][key]
                else:
                    self.config["EOM"][key] =value
            except Exception as e:
                # Exception handling code
                print(f"An error occurred: {str(e)}")
        elif category == "AOM":
            try:
                if delete:
                    del self.config["AOM"][key]
                else:
                    self.config["AOM"][key] =value
            except Exception as e:
                # Exception handling code
                print(f"An error occurred: {str(e)}")
        elif category == "freqA":
            try:
                if delete:
                    del self.config["EOM"]["freqA"][key]
                else:
                    self.config["EOM"]["freqA"][key] =value
            except Exception as e:
                # Exception handling code
                print(f"An error occurred: {str(e)}")
        elif category == "freqB":
            try:
                if delete:
                    del self.config["EOM"]["freqB"][key]
                else:
                    self.config["EOM"]["freqB"][key] =value
            except Exception as e:
                # Exception handling code
                print(f"An error occurred: {str(e)}")
        dict_to_xml_file(self.config, "staticfiles/xilinx.xml")
        self.RFSoC.transfer_file(r"staticfiles/xilinx.xml",r"/home/xilinx/jupyter_notebooks/qick/qick_demos/ssh_control/xilinx.xml")
        return "Configuration set successfully"