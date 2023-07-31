
from qick import *
from qick.parser import load_program
# Load bitstream with custom overlay
soc = QickSoc()

soccfg = soc
configEOM={"freq_seq0": [1000.0, 1000.0, 1000.0, 1000.0],
        "gain_seq0": [16384.0, 16384.0, 16384.0, 16384.0],
        "time_seq0":[0.0, 0.0, 200.0, 200.0],
        "length0":100.0, # [Clock ticks]
        "length1":100.0, # [Clock ticks]
        "zone0": 1.0,
        "mode0": "periodic",
        "zone1": 1.0,
        "mode1": "periodic",
}

#TTL
configAOM={
        "length":[[1.0, 4.0], [1.0, 4.0], [1.0, 6.0], [6.0]], # [Clock ticks]
        "pins":[0, 1, 2, 3],
        "time":[[11.0, 1.0], [1.0, 1.0], [1.0, 6.0], [6.0]],
        "timeseqformttl":[11.0, 1.0, 1.0, 6.0],
        "pinsformttl":[[0], [1, 2], [0, 1], [2, 3]],
        "lengthseqttl":[1.0, 1.0, 4.0, 6.0],
}
config= {
"adc_trig_offset": 100.0, # [Clock ticks]
"soft_avgs":1.0,
"relax_delay":1.0, # --us
#Readout
"readout_length": 2000.0, # [Clock ticks]
"pulse_freq":soccfg.adcfreq(999.9999984741211, gen_ch=0, ro_ch=0),
"reps":1.0, # --Fixed
"EOM":configEOM,
"AOM":configAOM
}

from XMLGenerator import dict_to_xml_file,xml_config_to_dict
dict_to_xml_file(config, "xilinx.xml")
