# Import the QICK drivers and auxiliary libraries
from qick import *
from qick.parser import load_program
from sequence import sequence_TTL
import numpy as np
from math import asin
from create_json import import_json_file, save_list_to_json_file
from XMLGenerator import xml_config_to_dict
# config = import_json_file("config.json")
config = xml_config_to_dict("xilinx.xml")

# Load bitstream with custom overlay
soc = QickSoc()

soccfg = soc
out_chs = [0,1]

def divide_nested_list(nested_list, divisor):
    """
    The function `divide_nested_list` takes a nested list of numbers and a divisor, and returns a new
    nested list where each number is divided by the divisor and rounded to the nearest whole number.
    @param nested_list - A nested list containing sublists of numbers.
    @param divisor - The divisor is a number that will be used to divide each element in the nested
    list.
    @returns a new nested list where each number in the original nested list has been divided by the
    given divisor and rounded to the nearest whole number.
    """
    result = []
    for sublist in nested_list:
        divided_sublist = []
        for number in sublist:
            divided_sublist.append(round(number / divisor))
        result.append(divided_sublist)
    return result

def phase_generator(freq):
    return asin(freq/1000)

# The class MultiSequenceProgram is a subclass of AveragerProgram.
class MultiSequenceProgram(AveragerProgram):
    def __init__(self,soccfg, cfg):
        super().__init__(soccfg, cfg)

    def initialize(self):
        cfg=self.cfg

        #EOM
        for ch in out_chs: #[0,1]
            #READOUT AT CHANNEL 0 and 1
            self.declare_readout(ch=ch, length=self.cfg["readout_length"],
                                 freq=self.cfg["pulse_freq"])

        idata0 = 30000*np.ones(16*cfg["EOM"]["length0"])
        idata1 = 30000*np.ones(16*cfg["EOM"]["length1"])
#         qdata = 30000*np.ones(16*cfg["length"])

        for ch in self.cfg["EOM"]['out_ch']:
            #GENERATE AT CHANNEL 0 and 1
            self.declare_gen(ch=ch, nqz=cfg["EOM"]["zone"+str(ch)])
            #ADD PULSE AT CHANNEL 0 and 1
            if ch == 0:
                self.add_pulse(ch=ch, name="measure", idata=idata0)
            else:
                self.add_pulse(ch=ch, name="measure", idata=idata1)
#             self.add_pulse(ch=ch, name="measure", idata=idata,qdata=qdata)

        freq=soccfg.freq2reg(cfg["pulse_freq"])  # convert frequency to dac frequency
#         self.trigger(pins=[0], t=0) # send a pulse on pmod0_0, for scope trigger
        for ii, ch in enumerate(self.cfg["EOM"]['out_ch']):
            #PULSE REGISTER AT CHANNEL 0 and 1
            self.default_pulse_registers(ch=ch,style="arb",waveform="measure", mode=cfg["EOM"]["mode"+str(ch)])

    def body(self):
        """
        The function triggers ADC acquisition, sets pulse registers, plays readout pulses, and triggers
        AOM sequences.
        """
        cfg=self.cfg

        #EOM
        self.trigger(adcs=[0,1],adc_trig_offset=cfg["adc_trig_offset"])  # trigger the adc acquisition
        for ii, freqseq in enumerate(cfg["EOM"]['freq_seq0']):
            for kk, ch in [0,1]:
                self.set_pulse_registers(ch=ch, freq=soccfg.freq2reg(freqseq), phase=soccfg.deg2reg(phase_generator(freqseq)), gain=cfg["EOM"]["gain_seq0"][ii])
                #PULSE AT CHANNEL 0 and 1
                self.pulse(ch=ch, t=cfg["EOM"]["time_seq"][ii]) # play readout pulse

        #AOM
        self.cfg["AOM"]["time"] = divide_nested_list(self.cfg["AOM"]["time"],2.6)
        self.cfg["AOM"]["length"] = divide_nested_list(self.cfg["AOM"]["length"],2.6)

        time_list,length,pins_seq = sequence_TTL(self.cfg["AOM"]["time"], self.cfg["AOM"]["length"], self.cfg["AOM"]["pins"])
        for time_index, time in enumerate(time_list):
            self.trigger(adcs=self.ro_chs,
                    pins=pins_seq[time_index],
                    adc_trig_offset=self.cfg["adc_trig_offset"],
                     t = time,
                    width = length[time_index])
        self.wait_all()
        self.sync_all(self.us2cycles(self.cfg["relax_delay"]))

prog = MultiSequenceProgram(soccfg, config)

iq_list = prog.acquire_decimated(soc)
# to switch off output
soc.reset_gens()