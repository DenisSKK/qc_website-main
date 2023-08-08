# forms.py
from django import forms
from django.forms.formsets import BaseFormSet
from django import forms

DEVICE_CHOICES = (
    ('laser', 'Laser'),
    ('eom', 'EOM'),
    ('aom', 'AOM'),
    ('frequency', 'Frequency'),
)

LASER_PARAMETER_CHOICES = (
    ('frequency', 'Frequency'),
    ('amplitude', 'Amplitude'),
)

FREQUENCY_CHOICES = (
    ('A', 'A'),
    ('B', 'B'),
)

GAIN_CHOICES = (
    ('0', 'G1nA'),
    ('1', 'G10nA'),
    ('2', 'G100nA'),
    ('3', 'G1uA'),
    ('4', 'G10uA'),
    ('5', 'G100uA'),
    ('6', 'G1mA'),
    ('7', 'G10mA'),
    ('8', 'G50mA'),
)

SENSITIVITY_CHOICES = (
    ('0', '2nV/fA'),
    ('1', '5nV/fA'),
    ('2', '10nV/fA'),
    ('3', '20nV/fA'),
    ('4', '50nV/fA'),
    ('5', '100nV/fA'),
    ('6', '200nV/fA'),
    ('7', '500nV/fA'),
    ('8', '1µV/pA'),
    ('9', '2µV/pA'),
    ('10', '5µV/pA'),
    ('11', '10µV/pA'),
    ('12', '20µV/pA'),
    ('13', '50µV/pA'),
    ('14', '100µV/pA'),
    ('15', '200µV/pA'),
    ('16', '500µV/pA'),
    ('17', '1mV/nA'),
    ('18', '2mV/nA'),
    ('19', '5mV/nA'),
    ('20', '10mV/nA'),
    ('21', '20mV/nA'),
    ('22', '50mV/nA'),
    ('23', '100mV/nA'),
    ('24', '200mV/nA'),
    ('25', '500mV/nA'),
    ('26', '1V/µA'),
)

TIME_CONSTANT_CHOICES = (
    ('0', '10µs'),
    ('1', '30µs'),
    ('2', '100µs'),
    ('3', '300µs'),
    ('4', '1ms'),
    ('5', '3ms'),
    ('6', '10ms'),
    ('7', '30ms'),
    ('8', '100ms'),
    ('9', '300ms'),
    ('10', '1s'),
    ('11', '3s'),
    ('12', '10s'),
    ('13', '30s'),
    ('14', '100s'),
    ('15', '300s'),
    ('16', '1ks'),
    ('17', '3ks'),
    ('18', '10ks'),
    ('19', '30ks'),
)

SLOPE_CHOICES = (
    ('0', '6 dB/oct'),
    ('1', '12 dB/oct'),
    ('2', '18 dB/oct'),
    ('3', '24 dB/oct'),
)

INPUT_CHOICES = (
    ('0', 'A'),
    ('1', 'A-B'),
    ('2', 'I(1MΩ)'),
    ('3', 'I(100MΩ)'),
)

ON_OFF_CHOICES = (
    ('0', 'OFF'),
    ('1', 'ON'),
)


class ExperimentForm(forms.Form):
    experiment_name = forms.CharField(label='Experiment Name')
    description = forms.CharField(widget=forms.Textarea, label='Description', required=False)
    file_name = forms.CharField(label='Experiment Name')


class BaseExperimentForm(BaseFormSet):
    def has_duplicate_keys(self, dictionary):
        return len(dictionary) != len(set(dictionary.keys()))

    def clean(self):
        if any(self.errors):
            return
        # device = laser_parameter = laser_frequency = laser_amplitude = eom_frequency = eom_time_start = eom_length = aom_pins = aom_start_time = aom_length = frequency_name = frequency_frequency = frequency_phase = frequency_amplitude = []
        device = {'laser': {},
                  'eom': {'frequency': [], 'start_time': [], 'length': []},
                  'aom': {'start_time': [], 'pins': [], 'length': []},
                  'frequency_name': {'A': {}, 'B': {}}}
        for form in self.forms:
            if form.cleaned_data:
                device = form.cleaned_data['device']
                laser_parameter = form.cleaned_data['laser_parameter']
                laser_frequency = form.cleaned_data['laser_frequency']
                laser_amplitude = form.cleaned_data['laser_amplitude']
                eom_frequency = form.cleaned_data['eom_frequency']
                eom_time_start = form.cleaned_data['eom_time_start']
                eom_length = form.cleaned_data['eom_length']
                aom_pins = form.cleaned_data['aom_pins']
                aom_start_time = form.cleaned_data['aom_start_time']
                aom_length = form.cleaned_data['aom_length']
                frequency_name = form.cleaned_data['frequency_name']
                frequency_frequency = form.cleaned_data['frequency_frequency']
                frequency_phase = form.cleaned_data['frequency_phase']
                frequency_amplitude = form.cleaned_data['frequency_amplitude']

                if device:
                    if device == 'laser' or device == 'Laser':
                        if laser_parameter and laser_frequency:
                            device['laser'][laser_parameter] = laser_frequency
                            if self.has_duplicate_keys(device['laser']):
                                duplicates = True
                        else:
                            raise forms.ValidationError(
                                'All Laser frequency input should be chosen.',
                                code='incomplete_laser_frequency_form'
                            )
                        if laser_parameter and laser_amplitude:
                            device['laser'][laser_parameter] = laser_amplitude
                            if self.has_duplicate_keys(device['laser']):
                                duplicates = True
                        else:
                            raise forms.ValidationError(
                                'All Laser amplitude input should be chosen.',
                                code='incomplete_laser_amplitude_form'
                            )
                        if duplicates:
                            raise forms.ValidationError(
                                'Laser Input Should be unique',
                                code='duplicate_laser'
                            )
                    elif device == "eom" or device == "EOM":
                        if eom_frequency and eom_time_start and eom_length:
                            if eom_time_start in device['eom']['start_time']:
                                duplicates = True
                            device['eom']['start_time'].append(eom_time_start)
                            device['eom']['frequency'].append(eom_frequency)
                            device['eom']['length'].append(eom_length)
                        else:
                            raise forms.ValidationError(
                                'All eom input should be chosen.',
                                code='incomplete_eom_form'
                            )
                        if duplicates:
                            raise forms.ValidationError(
                                'Laser Input Should be unique',
                                code='duplicate_eom'
                            )
                    elif device == "aom" or device == "AOM":
                        if aom_pins and aom_start_time and aom_length:
                            if aom_start_time in device['aom']['start_time']:
                                duplicates = True
                            device['aom']['start_time'].append(aom_start_time)
                            device['aom']['pins'].append(aom_pins)
                            device['aom']['length'].append(aom_length)
                        else:
                            raise forms.ValidationError(
                                'All eom input should be chosen.',
                                code='incomplete_eom_form'
                            )
                        if duplicates:
                            raise forms.ValidationError(
                                'Laser Input Should be unique',
                                code='duplicate_aom'
                            )
                    elif device == "frequency" or device == "Frequency":
                        if frequency_name and frequency_frequency and frequency_amplitude and frequency_phase:
                            if frequency_name == "A" and len(device['frequency_name']["A"]) == 0:
                                duplicates = True
                            device['frequency_name']["A"] = {"frequency": frequency_frequency,
                                                             "amplitude": frequency_amplitude, "phase": frequency_phase}
                            if frequency_name == "B" and len(device['frequency_name']["B"]) == 0:
                                duplicates = True
                            device['frequency_name']["B"] = {"frequency": frequency_frequency,
                                                             "amplitude": frequency_amplitude, "phase": frequency_phase}
                        else:
                            raise forms.ValidationError(
                                'All Frequency input should be chosen.',
                                code='incomplete_freq_form'
                            )
                        if duplicates:
                            raise forms.ValidationError(
                                'Frequency Input Should be unique',
                                code='duplicate_freq'
                            )


class LaserForm(forms.Form):
    laser_host = forms.CharField(label='IP Address', max_length=100)
    laser_port = forms.IntegerField(label='Port', required=False)
    wavelength_act = forms.FloatField(label='Wavelength')
    scan_end = forms.FloatField(label='Scan End')
    scan_start = forms.FloatField(label='Scan Start')
    scan_freq = forms.FloatField(label='Scan Frequency')
    voltage_act = forms.FloatField(label='Voltage')
    current_act = forms.FloatField(label='Current')


class LaserFormIP(forms.Form):
    laser_host = forms.CharField(label='IP Address', max_length=100)
    laser_port = forms.IntegerField(label='Port', required=False)


class LaserFormConfig(forms.Form):
    wavelength_act = forms.FloatField(label='Wavelength')
    scan_end = forms.FloatField(label='Scan End')
    scan_start = forms.FloatField(label='Scan Start')
    scan_freq = forms.FloatField(label='Scan Frequency')
    voltage_act = forms.FloatField(label='Voltage')
    current_act = forms.FloatField(label='Current')


# forms.py
class CaylarForm(forms.Form):
    caylar_host = forms.CharField(label='IP Address', max_length=100)
    caylar_port = forms.IntegerField(label='Port', required=False)
    caylar_current = forms.FloatField(label='Current', required=False)
    caylar_field = forms.FloatField(label='Field', required=False)


class CaylarFormCurrent(forms.Form):
    caylar_current = forms.FloatField(label='Current')


class CaylarFormIP(forms.Form):
    caylar_host = forms.CharField(label='IP Address', max_length=100)
    caylar_port = forms.IntegerField(label='Port', required=False)


class CaylarFormField(forms.Form):
    caylar_field = forms.FloatField(label='Field')


class SX199Form(forms.Form):
    gain1 = forms.ChoiceField(label='CS580 1 Gain', required=False, choices=GAIN_CHOICES)
    gain2 = forms.ChoiceField(label='CS580 2 Gain', required=False, choices=GAIN_CHOICES)
    input1 = forms.ChoiceField(label='CS580 1 Input', required=False, choices=ON_OFF_CHOICES)
    input2 = forms.ChoiceField(label='CS580 2 Input', required=False, choices=ON_OFF_CHOICES)
    speed1 = forms.ChoiceField(label='CS580 1 Speed', required=False, choices=[('0', 'FAST'), ('1', 'SLOW')])
    speed2 = forms.ChoiceField(label='CS580 2 Speed', required=False, choices=[('0', 'FAST'), ('1', 'SLOW')])
    shield1 = forms.ChoiceField(label='CS580 1 Inner Shield', required=False, choices=[('0', 'GUARD'), ('1', 'RETURN')])
    shield2 = forms.ChoiceField(label='CS580 2 Inner Shield', required=False, choices=[('0', 'GUARD'), ('1', 'RETURN')])
    isolation1 = forms.ChoiceField(label='CS580 1 Isolation', required=False, choices=[('0', 'GROUND'), ('1', 'FLOAT')])
    isolation2 = forms.ChoiceField(label='CS580 2 Isolation', required=False, choices=[('0', 'GROUND'), ('1', 'FLOAT')])
    output1 = forms.ChoiceField(label='CS580 1 Output', required=False, choices=ON_OFF_CHOICES)
    output2 = forms.ChoiceField(label='CS580 2 Output', required=False, choices=ON_OFF_CHOICES)
    curr1 = forms.FloatField(label='CS580 1 DC Current', required=False)
    curr2 = forms.FloatField(label='CS580 2 DC Current', required=False)
    volt1 = forms.FloatField(label='CS580 1 Voltage', required=False, min_value=0, max_value=50)
    volt2 = forms.FloatField(label='CS580 2 Voltage', required=False, min_value=0, max_value=50)


class SR830Form(forms.Form):
    sensitivity = forms.ChoiceField(label='SR830 Sensitivity', required=False, choices=SENSITIVITY_CHOICES)
    time_constant = forms.ChoiceField(label='SR830 Time Constant', required=False, choices=TIME_CONSTANT_CHOICES)
    slope = forms.ChoiceField(label='SR830 Slope', required=False, choices=SLOPE_CHOICES)
    synch_filter = forms.ChoiceField(label='SR830 Synch Filter', required=False, choices=ON_OFF_CHOICES)
    input = forms.ChoiceField(label='SR830 Input', required=False, choices=INPUT_CHOICES)
    couple = forms.ChoiceField(label='SR830 Couple', required=False, choices=[('0', 'AC'), ('1', 'DC')])
    shield = forms.ChoiceField(label='SR830 Input Shield Grounding', required=False,
                               choices=[('0', 'Float'), ('1', 'Ground')])
    freq_source = forms.ChoiceField(label='SR830 Frequency Source', required=False,
                                    choices=[('0', 'External'), ('1', 'Internal')])
    frequency = forms.FloatField(label='SR830 Frequency', required=False, min_value=0.001, max_value=102000)


class MercuryForm(forms.Form):
    mercury_host = forms.CharField(label='IP Address', max_length=100)
    mercury_port = forms.IntegerField(label='Port', required=False)
    mercury_heater_power = forms.FloatField(label='Heater Power', required=False)
    mercury_itc_flow_percentage = forms.FloatField(label='ITC Flow Percentage', required=False)
    mercury_itc_temperature_set_point = forms.FloatField(label='ITC Temperature Set Point', required=False)
    mercury_itc_voltage = forms.FloatField(label='ITC Voltage', required=False)
    mercury_itc_automatic_heating = forms.ChoiceField(label='ITC Automatic Heating', required=False,
                                                      choices=ON_OFF_CHOICES)
    mercury_itc_automatic_pid = forms.ChoiceField(label='ITC Automatic PID', required=False,
                                                  choices=ON_OFF_CHOICES)


class MercuryFormIP(forms.Form):
    mercury_host = forms.CharField(label='IP Address', max_length=100)
    mercury_port = forms.IntegerField(label='Port', required=False)


class MercuryFormConfig(forms.Form):
    mercury_heater_power = forms.FloatField(label='Heater Power', required=False)
    mercury_itc_flow_percentage = forms.FloatField(label='ITC Flow Percentage', required=False)
    mercury_itc_temperature_set_point = forms.FloatField(label='ITC Temperature Set Point', required=False)
    mercury_itc_voltage = forms.FloatField(label='ITC Voltage', required=False)
    mercury_itc_automatic_heating = forms.ChoiceField(label='ITC Automatic Heating', required=False,
                                                      choices=ON_OFF_CHOICES)
    mercury_itc_automatic_pid = forms.ChoiceField(label='ITC Automatic PID', required=False,
                                                  choices=ON_OFF_CHOICES)


class RFSoCConfigForm(forms.Form):
    rfsoc_host = forms.CharField(label='IP Address', max_length=100)
    rfsoc_port = forms.IntegerField(label='Port', required=False)
    rfsoc_username = forms.CharField(label='Username', required=False)
    rfsoc_password = forms.CharField(label='Password', required=False)
    adc_trig_offset = forms.FloatField(label='ADC Trigger Offset', required=False)
    soft_avgs = forms.FloatField(label='Soft Averages', required=False)
    relax_delay = forms.FloatField(label='Relax Delay', required=False)
    readout_length = forms.FloatField(label='Readout Length', required=False)
    pulse_freq = forms.FloatField(label='Pulse Frequency', required=False)
    reps = forms.FloatField(label='Repetitions', required=False)
    eom_outch = forms.CharField(label='EOM Out Ch', required=False)
    eom_length0 = forms.FloatField(label='EOM Length 0', required=False)
    eom_length1 = forms.FloatField(label='EOM Length 1', required=False)
    eom_zone0 = forms.FloatField(label='EOM Zone 0', required=False)
    eom_mode0 = forms.CharField(label='EOM Mode 0', required=False)
    eom_zone1 = forms.FloatField(label='EOM Zone 1', required=False)
    eom_mode1 = forms.CharField(label='EOM Mode 1', required=False)




class RFSoCConfigFormIP(forms.Form):
    rfsoc_host = forms.CharField(label='IP Address', max_length=100)
    rfsoc_port = forms.IntegerField(label='Port', required=False)
    rfsoc_username = forms.CharField(label='Username', required=False)
    rfsoc_password = forms.CharField(label='Password', required=False)




class RFSoCEOMSequenceForm(forms.Form):
    frequency0 = forms.FloatField(label='EOM Frequency')
    gain0 = forms.FloatField(label='EOM Gain')
    time0 = forms.FloatField(label='EOM Time')


class RFSoCAOMSequenceForm(forms.Form):
    aom_pins = forms.MultipleChoiceField(
        choices=[('0', '0'), ('1', '1'), ('2', '2'), ('3', '3')],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    time1 = forms.FloatField(label='EOM Length 1', required=False)
    length1 = forms.FloatField(label='EOM Length 1', required=False)
