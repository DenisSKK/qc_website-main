# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.test import TestCase
from django.urls import reverse
from staticfiles.XMLGenerator import xml_config_to_dict, dict_to_xml_file
from django.contrib.messages import get_messages

from django.contrib.auth.models import User
from datetime import datetime

class CaylarPageViewTest(TestCase):
    def __init__(self):
        self.xml_file_path = "staticfiles/caylar.xml"
        self.caylar_host = xml_config_to_dict(self.xml_file_path)

    def setUp(self):
        self.url = reverse('caylar_page')
        self.data = {
            'caylar_host': self.caylar_host["host"],
            'caylar_port': self.caylar_host["port"],
            'caylar_current': self.caylar_host["current"],
            'caylar_field': self.caylar_host["field"],
        }

    def test_caylar_page_view_with_authenticated_user(self):
        user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/caylar.html')

    def test_caylar_page_view_with_unauthenticated_user(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('login') + '?next=' + self.url)

    def test_post_request_with_valid_form_data(self):
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)

        # Check if the caylar object is updated with the new data
        caylar_update = xml_config_to_dict(self.xml_file_path)
        self.assertEqual(caylar_update["host"], self.data['caylar_host'])
        self.assertEqual(caylar_update["port"], self.data['caylar_port'])
        self.assertEqual(caylar_update["current"], self.data['caylar_current'])
        self.assertEqual(caylar_update["field"], self.data['caylar_field'])

        # Check if success message is added to the Django messages framework
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Changes saved successfully in Caylar!')

    def test_post_request_with_invalid_form_data(self):
        invalid_data = {
            'caylar_host': '',  # This field is required
            'caylar_port': 'invalid_port',  # This field should be an integer
            'caylar_current': 'invalid_current',  # This field should be a number
        }
        response = self.client.post(self.url, data=invalid_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)

        # Check if warning message is added to the Django messages framework
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Cannot be updated!')

        # Check if the caylar object is not updated with invalid data
        caylar_update = xml_config_to_dict(self.xml_file_path)
        self.assertNotEqual(caylar_update["host"], invalid_data['caylar_host'])
        self.assertNotEqual(caylar_update["port"], invalid_data['caylar_port'])
        self.assertNotEqual(caylar_update["current"], invalid_data['caylar_current'])
        self.assertNotEqual(caylar_update["field"], invalid_data['caylar_field'])

class RFSoCPageViewTest(TestCase):
    def __init__(self):
        self.xml_file_path = "staticfiles/xilinx.xml"
        self.host_xml_file_path = "staticfiles/xilinx_host.xml"
        self.rfsoc_host = xml_config_to_dict(self.host_xml_file_path)
        self.rfsoc = xml_config_to_dict(self.xml_file_path)

    def setUp(self):
        self.url = reverse('rfsoc_page')
        self.data = {
        'rfsoc_host': self.rfsoc_host["host"],
        'rfsoc_username': self.rfsoc_host["username"],
        'rfsoc_password': self.rfsoc_host["password"],
        'rfsoc_port': self.rfsoc_host["port"],
        # Add other form fields here
        'adc_trig_offset': self.rfsoc['adc_trig_offset'],
        'soft_avgs': self.rfsoc['soft_avgs'],
        'relax_delay': self.rfsoc['relax_delay'],
        'readout_length': self.rfsoc['readout_length'],
        'pulse_freq': self.rfsoc['pulse_freq'],
        'reps': self.rfsoc['reps'],
        'eom_outch': self.rfsoc['EOM']['out_ch'],
        'eom_freqseq': ', '.join(self.rfsoc['EOM']['freq_seq']),
        'eom_timeseq': ', '.join(str(val) for val in self.rfsoc['EOM']['time_seq']),
        'eom_length': self.rfsoc['EOM']['length'],
        'eom_pulsefreq': self.rfsoc['EOM']['pulse_freq'],
        'eom_zone': self.rfsoc['EOM']['zone'],
        'eom_mode': self.rfsoc['EOM']['mode'],
        'freqA_res_phase': self.rfsoc['EOM']['freqA']['res_phase'],
        'freqA_pulse_gain': self.rfsoc['EOM']['freqA']['pulse_gain'],
        'freqA_pulse_freq': self.rfsoc['EOM']['freqA']['pulse_freq'],
        'freqB_res_phase': self.rfsoc['EOM']['freqB']['res_phase'],
        'freqB_pulse_gain': self.rfsoc['EOM']['freqB']['pulse_gain'],
        'freqB_pulse_freq': self.rfsoc['EOM']['freqB']['pulse_freq'],
        'selected_pins': self.rfsoc['AOM']['pins'],
        'aom_length_0': ', '.join(str(val) for val in self.rfsoc['AOM']['length'][0]),
        'aom_length_1': ', '.join(str(val) for val in self.rfsoc['AOM']['length'][1]),
        'aom_length_2': ', '.join(str(val) for val in self.rfsoc['AOM']['length'][2]),
        'aom_length_3': ', '.join(str(val) for val in self.rfsoc['AOM']['length'][3]),
        'aom_time_0': ', '.join(str(val) for val in self.rfsoc['AOM']['time'][0]),
        'aom_time_1': ', '.join(str(val) for val in self.rfsoc['AOM']['time'][1]),
        'aom_time_2': ', '.join(str(val) for val in self.rfsoc['AOM']['time'][2]),
        'aom_time_3': ', '.join(str(val) for val in self.rfsoc['AOM']['time'][3]),
    }


    def test_rfsoc_page_view_with_authenticated_user(self):
        user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'rfsoc_page.html')

    def test_rfsoc_page_view_with_unauthenticated_user(self):
        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('login') + '?next=' + self.url)

    def test_post_request_with_valid_form_data(self):
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)

        # Check if the rfsoc host and port are updated with the new data
        rfsoc_host_update = xml_config_to_dict(self.host_xml_file_path)
        self.assertEqual(rfsoc_host_update["host"], self.data['rfsoc_host'])
        self.assertEqual(rfsoc_host_update["username"], self.data['rfsoc_username'])
        self.assertEqual(rfsoc_host_update["password"], self.data['rfsoc_password'])
        self.assertEqual(rfsoc_host_update["port"], self.data['rfsoc_port'])
        rfsoc_config_update = xml_config_to_dict(self.xml_file_path)
        self.assertEqual(rfsoc_config_update["adc_trig_offset"], self.data['adc_trig_offset'])
        self.assertEqual(rfsoc_config_update["adc_trig_offset"], self.data['adc_trig_offset'])
        self.assertEqual(rfsoc_config_update["soft_avgs"], self.data['soft_avgs'])
        self.assertEqual(rfsoc_config_update["relax_delay"], self.data['relax_delay'])
        self.assertEqual(rfsoc_config_update["readout_length"], self.data['readout_length'])
        self.assertEqual(rfsoc_config_update["pulse_freq"], self.data['pulse_freq'])
        self.assertEqual(rfsoc_config_update["reps"], self.data['reps'])
        self.assertEqual(rfsoc_config_update["EOM"]["out_ch"], self.data['eom_outch'])
        self.assertEqual(', '.join(rfsoc_config_update["EOM"]["freq_seq"]), self.data['eom_freqseq'])
        self.assertEqual(', '.join(str(val) for val in rfsoc_config_update["EOM"]["time_seq"]), self.data['eom_timeseq'])
        self.assertEqual(rfsoc_config_update["EOM"]["length"], self.data['eom_length'])
        self.assertEqual(rfsoc_config_update["EOM"]["pulse_freq"], self.data['eom_pulsefreq'])
        self.assertEqual(rfsoc_config_update["EOM"]["zone"], self.data['eom_zone'])
        self.assertEqual(rfsoc_config_update["EOM"]["mode"], self.data['eom_mode'])
        self.assertEqual(rfsoc_config_update["EOM"]["freqA"]["res_phase"], self.data['freqA_res_phase'])
        self.assertEqual(rfsoc_config_update["EOM"]["freqA"]["pulse_gain"], self.data['freqA_pulse_gain'])
        self.assertEqual(rfsoc_config_update["EOM"]["freqA"]["pulse_freq"], self.data['freqA_pulse_freq'])
        self.assertEqual(rfsoc_config_update["EOM"]["freqB"]["res_phase"], self.data['freqB_res_phase'])
        self.assertEqual(rfsoc_config_update["EOM"]["freqB"]["pulse_gain"], self.data['freqB_pulse_gain'])
        self.assertEqual(rfsoc_config_update["EOM"]["freqB"]["pulse_freq"], self.data['freqB_pulse_freq'])
        self.assertEqual(rfsoc_config_update["AOM"]["pins"], self.data['selected_pins'])
        self.assertEqual(', '.join(str(val) for val in rfsoc_config_update["AOM"]["length"][0]), self.data['aom_length_0'])
        self.assertEqual(', '.join(str(val) for val in rfsoc_config_update["AOM"]["length"][1]), self.data['aom_length_1'])
        self.assertEqual(', '.join(str(val) for val in rfsoc_config_update["AOM"]["length"][2]), self.data['aom_length_2'])
        self.assertEqual(', '.join(str(val) for val in rfsoc_config_update["AOM"]["length"][3]), self.data['aom_length_3'])
        self.assertEqual(', '.join(str(val) for val in rfsoc_config_update["AOM"]["time"][0]), self.data['aom_time_0'])
        self.assertEqual(', '.join(str(val) for val in rfsoc_config_update["AOM"]["time"][1]), self.data['aom_time_1'])
        self.assertEqual(', '.join(str(val) for val in rfsoc_config_update["AOM"]["time"][2]), self.data['aom_time_2'])
        self.assertEqual(', '.join(str(val) for val in rfsoc_config_update["AOM"]["time"][3]), self.data['aom_time_3'])

        # Add assertions for AOM length and time configuration
        # Check if the rfsoc configuration is updated with the new data
        rfsoc_config_update = xml_config_to_dict(self.xml_file_path)
        # Add assertions for other fields in the rfsoc configuration

        # Check if success messages are added to the Django messages framework
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 2)
        self.assertEqual(str(messages[0]), 'Changes saved successfully in RFSoC!')
        self.assertEqual(str(messages[1]), 'Changes saved successfully!')

    def test_post_request_with_invalid_form_data(self):
        invalid_data = {
            'rfsoc_host': '',  # This field is required
            'rfsoc_username': 'testuser',
            'rfsoc_password': 'testpassword',
            'rfsoc_port': 'invalid_port',  # This field should be an integer
            # Add other invalid fields here
        }
        response = self.client.post(self.url, data=invalid_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)

        # Check if warning message is added to the Django messages framework
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Cannot save changes. Please check the form for errors.')

        # Check if the rfsoc host and port are not updated with the invalid data
        rfsoc_host_update = xml_config_to_dict(self.host_xml_file_path)
        self.assertNotEqual(rfsoc_host_update["host"], invalid_data['rfsoc_host'])
        self.assertNotEqual(rfsoc_host_update["port"], invalid_data['rfsoc_port'])

        # Check if the rfsoc configuration is not updated with the invalid data
        rfsoc_config_update = xml_config_to_dict(self.xml_file_path)
        # Add assertions for other fields in the rfsoc configuration

class LaserPageViewTestCase(TestCase):
    def __init__(self):
        self.xml_file_path = "staticfiles/toptica.xml"
        self.toptica_host = xml_config_to_dict(self.xml_file_path)
    def setUp(self):
        self.url = reverse('laser_page')
        self.data = {
            'laser_host': self.toptica_host["host"],
            'laser_port': self.toptica_host["port"],
            'wavelength_act': self.toptica_host["wavelength_act"],
            'scan_end': self.toptica_host["scan_end"],
            'scan_start': self.toptica_host["scan_start"],
            'scan_freq': self.toptica_host["scan_freq"],
            'scan_offset': self.toptica_host["scan_offset"],
        }

    def test_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/laser.html')

    def test_post_request(self):
        response = self.client.post(self.url, data=self.data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)

        # Check if the laser object is updated with the new data
        toptica_update = xml_config_to_dict(self.xml_file_path)
        self.assertEqual(toptica_update["host"], self.data['laser_host'])
        self.assertEqual(toptica_update["port"], self.data['laser_port'])
        self.assertEqual(toptica_update["wavelength_act"], self.data['wavelength_act'])
        self.assertEqual(toptica_update["scan_end"], self.data['scan_end'])
        self.assertEqual(toptica_update["scan_start"], self.data['scan_start'])
        self.assertEqual(toptica_update["scan_freq"], self.data['scan_freq'])
        self.assertEqual(toptica_update["scan_offset"], self.data['scan_offset'])

        # Check if success message is added to the Django messages framework
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Changes saved successfully in Toptica!')

    def test_invalid_form_data(self):
        invalid_data = {
            'laser_host': '',  # This field is required
            'laser_port': 'invalid_port',  # This field should be an integer
            'wavelength_act': 'invalid_wavelength',  # This field should be a number
        }
        response = self.client.post(self.url, data=invalid_data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)

        # Check if warning message is added to the Django messages framework
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Cannot be updated!')

        # Check if the laser object is not updated with invalid data
        # self.assertFalse(Laser.objects.exists())

from .forms import MercuryForm
class MercuryPageViewTest(TestCase):
    def setUp(self):
        self.url = reverse('mercury_page')
        self.xml_file_path = "staticfiles/mercury.xml"
        self.mercury_config = xml_config_to_dict(self.xml_file_path)

    def test_get_request(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/mercury.html')
        self.assertIsInstance(response.context['form'], MercuryForm)
        self.assertEqual(response.context['mercury_host'], "")
        self.assertEqual(response.context['mercury_port'], "")
        self.assertEqual(response.context['mercury_heater_power'], "")
        self.assertEqual(response.context['mercury_itc_temperature'], "")

    def test_post_request_with_valid_form(self):
        form_data = {
            'mercury_host': self.mercury_config["host"],
            'mercury_port': self.mercury_config["port"],
            'mercury_heater_power': self.mercury_config["heater_power"],
            'mercury_itc_temperature': self.mercury_config["ITC_temperature"],
        }

        response = self.client.post(self.url, data=form_data)
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Changes saved successfully in MercuryITC!')

        # Additional assertions for the updated values
        mercury_host = xml_config_to_dict("staticfiles/mercuryITC.xml")
        self.assertEqual(mercury_host["host"], 'example.com')
        self.assertEqual(mercury_host["port"], '1234')
        self.assertEqual(mercury_host["heater_power"], '50')
        self.assertEqual(mercury_host["ITC_temperature"], '25')

    def test_post_request_with_invalid_form(self):
        form_data = {
            'mercury_host': 'example.com',
            'mercury_port': '1234',
            'mercury_heater_power': '',
            'mercury_itc_temperature': '25',
        }

        response = self.client.post(self.url, data=form_data)
        messages = list(get_messages(response.wsgi_request))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Cannot be updated!')

        # Additional assertions for the unchanged values
        mercury_host = xml_config_to_dict("staticfiles/mercuryITC.xml")
        self.assertNotEqual(mercury_host["host"], 'example.com')
        self.assertNotEqual(mercury_host["port"], '1234')
        self.assertNotEqual(mercury_host["heater_power"], '')
        self.assertNotEqual(mercury_host["ITC_temperature"], '25')
