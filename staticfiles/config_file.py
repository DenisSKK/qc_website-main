
from qick import *
from qick.parser import load_program
# Load bitstream with custom overlay
soc = QickSoc()

soccfg = soc
freqA0 = {"res_phase": 90 , # The phase of the signal
        "pulse_gain": 2000, # [DAC units]
        "pulse_freq": soccfg.adcfreq(999.9999984741211, gen_ch=0, ro_ch=0), # [MHz]
        }
freqB0 = {"res_phase": 180 , # The phase of the signal
        "pulse_gain": 3000, # [DAC units]
        "pulse_freq": soccfg.adcfreq(999.9999984741211, gen_ch=0, ro_ch=0), # [MHz]
        }
freqA1 = {"res_phase": 90 , # The phase of the signal
        "pulse_gain": 1000, # [DAC units]
        "pulse_freq": soccfg.adcfreq(999.9999984741211, gen_ch=1, ro_ch=1), # [MHz]
        }
freqB1 = {"res_phase": 180 , # The phase of the signal
        "pulse_gain": 1500, # [DAC units]
        "pulse_freq": soccfg.adcfreq(999.9999984741211, gen_ch=1, ro_ch=1), # [MHz]
        }
configEOM={"out_ch":[0, 1],
        "freqA0": freqA0,
        "freqB0": freqB0,
        "freqA1": freqA1,
        "freqB1": freqB1,
        "freq_seq0": ['freqA0', 'freqB0', 'freqA0', 'freqB0'],
        "freq_seq1": ['freqA1', 'freqB1', 'freqA1', 'freqB1'],
        "time_seq0":[50, 190, 370, 700],
        "time_seq1":[60, 200, 380, 710],
        "length0":100, # [Clock ticks]
        "length1":110, # [Clock ticks]
        "pulse_freq":soccfg.adcfreq(999.9999984741211, gen_ch=0, ro_ch=0), # [MHz]
        "zone0": 1,
        "mode0": "periodic",
        "zone1": 1,
        "mode1": "periodic",
}

#TTL
configAOM={
        "length":[[200, 200, 200, 200], [200, 200, 200, 200], [200, 200, 200, 200], [200, 200, 200, 200]], # [Clock ticks]
        "pins":[1, 2, 0, 3],
        "time":[[0, 400, 800, 1200], [0, 400, 800, 1200], [0, 400, 800, 1200], [0, 400, 800, 1200]],
}
config= {
"adc_trig_offset": 100, # [Clock ticks]
"soft_avgs":1,
"relax_delay":1.0, # --us
#Readout
"readout_length": 2000, # [Clock ticks]
"pulse_freq":soccfg.adcfreq(999.9999984741211, gen_ch=0, ro_ch=0),
"reps":1, # --Fixed
"EOM":configEOM,
"AOM":configAOM
}

from XMLGenerator import dict_to_xml_file,xml_config_to_dict
dict_to_xml_file(config, "xilinx.xml")
