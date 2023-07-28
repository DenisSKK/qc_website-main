# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
# TODO comment code
from django import template
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse
from django.shortcuts import render, redirect
from .construct_object import construct_object, construct_caylar, construct_itc, construct_rfsoc, construct_toptica, \
    construct_sx
from django.forms.formsets import formset_factory
from .forms import LaserForm, RFSoCConfigForm, RFSoCConfigFormIP, CaylarForm, SX199Form, MercuryForm, ExperimentForm, \
    LaserFormConfig, LaserFormIP, RFSoCEOMSequenceForm, RFSoCAOMSequenceForm, CaylarFormIP, CaylarFormConfig, \
    MercuryFormConfig, MercuryFormIP
from staticfiles.XMLGenerator import xml_config_to_dict, dict_to_xml_file

from django.contrib import messages
import os
import shutil

SX_instance = None


@login_required(login_url="/login/")
def laser_page_view(request):
    # Load the data from the laser XML file

    Update_Laser = construct_toptica()
    connected = Update_Laser.try_connect()
    toptica_host = xml_config_to_dict("staticfiles/toptica.xml")
    context = {}
    if connected:
        Update_Laser.update_all_xml("staticfiles/toptica.xml")
        context["wavelength_act"] = Update_Laser.report_ctl_wavelength_act()
        context["scan_end"] = Update_Laser.report_scan_end()
        context["scan_start"] = Update_Laser.report_scan_start()
        context["scan_freq"] = Update_Laser.report_scan_frequency()
        context["scan_offset"] = Update_Laser.report_scan_offset()
        context["current_act"] = Update_Laser.report_current_act()
        context["voltage_act"] = Update_Laser.report_voltage_act()
        toptica_host["time_update"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        dict_to_xml_file(toptica_host, "staticfiles/toptica.xml")
        toptica_host = xml_config_to_dict("staticfiles/toptica.xml")
    else:
        info = "Last time connected " + toptica_host["time_update"] + " because not connected with the device!"
        # info = "Parameter has not updated since "+toptica_host["time_update"]+" because not connected with the device!"
        messages.info(request, info)

    if request.method == 'POST':
        if "updateall" in request.POST:
            form = LaserForm(request.POST)
            if form.is_valid():

                toptica_host["host"] = form.cleaned_data['laser_host']
                toptica_host["port"] = form.cleaned_data['laser_port']
                toptica_host["wavelength_act"] = form.cleaned_data['wavelength_act']
                toptica_host["scan_end"] = form.cleaned_data['scan_end']
                toptica_host["scan_start"] = form.cleaned_data['scan_start']
                toptica_host["scan_freq"] = form.cleaned_data['scan_freq']
                toptica_host["scan_offset"] = form.cleaned_data['scan_offset']
                dict_to_xml_file(toptica_host, "staticfiles/toptica.xml")
                if connected:
                    Update_Laser.try_connect()
                    Update_Laser.update_all_xml("staticfiles/toptica.xml")
                    Update_Laser.disconnect()
                    messages.success(request, 'Changes saved successfully in Toptica!')
                else:
                    # Add success message to the Django messages framework
                    messages.success(request, 'Changes saved successfully in XML!')

                # Redirect to the laser page to reload the page with the updated values
                return redirect('laser_page')
            else:
                messages.warning(request, 'Cannot be updated!')
                return redirect('laser_page')
        elif "updateip" in request.POST:
            form = LaserFormIP(request.POST)
            if form.is_valid():

                toptica_host["host"] = form.cleaned_data['laser_host']
                toptica_host["port"] = form.cleaned_data['laser_port']
                dict_to_xml_file(toptica_host, "staticfiles/toptica.xml")
                # Add success message to the Django messages framework
                messages.success(request, 'Changes saved successfully in XML!')
                # Redirect to the laser page to reload the page with the updated values
                return redirect('laser_page')
            else:
                messages.warning(request, 'Cannot be updated!')
                return redirect('laser_page')
        elif "updateconfig" in request.POST:
            form = LaserFormConfig(request.POST)
            if form.is_valid():
                toptica_host["wavelength_act"] = form.cleaned_data['wavelength_act']
                toptica_host["scan_end"] = form.cleaned_data['scan_end']
                toptica_host["scan_start"] = form.cleaned_data['scan_start']
                toptica_host["scan_freq"] = form.cleaned_data['scan_freq']
                toptica_host["scan_offset"] = form.cleaned_data['scan_offset']
                dict_to_xml_file(toptica_host, "staticfiles/toptica.xml")
                if connected:
                    Update_Laser.try_connect()
                    Update_Laser.update_all_xml("staticfiles/toptica.xml")
                    Update_Laser.disconnect()
                    messages.success(request, 'Changes saved successfully in Toptica!')
                else:
                    # Add success message to the Django messages framework
                    messages.success(request, 'Changes saved successfully in XML!')

                # Redirect to the laser page to reload the page with the updated values
                return redirect('laser_page')
            else:
                messages.warning(request, 'Cannot be updated!')
                return redirect('laser_page')

    else:
        # Initialize the form with the current laser information

        form = LaserForm(initial={
            'laser_host': toptica_host["host"] if toptica_host["host"] is not None else '',
            'laser_port': toptica_host["port"] if toptica_host["port"] is not None else '',
            'wavelength_act': toptica_host["wavelength_act"] if toptica_host["wavelength_act"] is not None else '',
            'scan_end': toptica_host["scan_end"] if toptica_host["scan_end"] is not None else '',
            'scan_start': toptica_host["scan_start"] if toptica_host["scan_start"] is not None else '',
            'scan_freq': toptica_host["scan_freq"] if toptica_host["scan_freq"] is not None else '',
            'scan_offset': toptica_host["scan_offset"] if toptica_host["scan_offset"] is not None else '',
        })

    context["connected"] = connected
    context["form"] = form
    Update_Laser.disconnect()

    return render(request, 'home/laser.html', context)


@login_required(login_url="/login/")
def caylar_page_view(request):
    # Load the data from the magnet XML file
    context = {}
    Update_caylar = construct_caylar()
    connected = Update_caylar.try_connect()
    caylar_host = xml_config_to_dict("staticfiles/caylar.xml")
    if connected:
        Update_caylar.update_all_xml("staticfiles/caylar.xml")
        context["caylar_current"] = Update_caylar.current()
        context["caylar_field"] = Update_caylar.field()
        context["caylar_voltage"] = Update_caylar.voltage()
        context["caylar_ADCDAC_temp"] = Update_caylar.ADCDAC_temp()
        context["caylar_box_temp"] = Update_caylar.box_temp()
        context["caylar_rack_temp"] = Update_caylar.rack_temp()
        context["caylar_water_temp"] = Update_caylar.water_temp()
        context["caylar_water_flow"] = Update_caylar.water_flow()
        caylar_host["time_update"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        dict_to_xml_file(caylar_host, "staticfiles/caylar.xml")
        caylar_host = xml_config_to_dict("staticfiles/caylar.xml")
    else:
        info = "Parameter has not updated since " + caylar_host[
            "time_update"] + " because not connected with the device!"
        messages.info(request, info)

    if request.method == 'POST':
        if "updateall" in request.POST:
            form = CaylarForm(request.POST)
            if form.is_valid():
                caylar_host["host"] = form.cleaned_data['caylar_host']
                caylar_host["port"] = form.cleaned_data['caylar_port']
                caylar_host["current"] = form.cleaned_data['caylar_current']
                caylar_host["field"] = form.cleaned_data['caylar_field']
                dict_to_xml_file(caylar_host, "staticfiles/caylar.xml")

                if connected:
                    Update_caylar.update_all_xml("staticfiles/caylar.xml")
                    messages.success(request, 'Changes saved successfully in Caylar!')
                else:
                    # Add success message to the Django messages framework
                    messages.success(request, 'Changes saved successfully in XML!')

                # Redirect to the magnet page to reload the page with the updated values
                return redirect('caylar_page')
            else:
                messages.warning(request, 'Cannot be updated!')
                return redirect('caylar_page')
        elif "updateip" in request.POST:
            form = CaylarFormIP(request.POST)
            if form.is_valid():
                caylar_host["host"] = form.cleaned_data['caylar_host']
                caylar_host["port"] = form.cleaned_data['caylar_port']
                dict_to_xml_file(caylar_host, "staticfiles/caylar.xml")
                messages.success(request, 'Changes saved successfully in XML!')
                # Redirect to the magnet page to reload the page with the updated values
                return redirect('caylar_page')
            else:
                messages.warning(request, 'Cannot be updated!')
                return redirect('caylar_page')
        elif "updateconfig" in request.POST:
            form = CaylarFormConfig(request.POST)
            if form.is_valid():
                caylar_host["current"] = form.cleaned_data['caylar_current']
                caylar_host["field"] = form.cleaned_data['caylar_field']
                dict_to_xml_file(caylar_host, "staticfiles/caylar.xml")

                if connected:
                    Update_caylar.update_all_xml("staticfiles/caylar.xml")
                    messages.success(request, 'Changes saved successfully in Caylar!')
                else:
                    # Add success message to the Django messages framework
                    messages.success(request, 'Changes saved successfully in XML!')

                # Redirect to the magnet page to reload the page with the updated values
                return redirect('caylar_page')
            else:
                messages.warning(request, 'Cannot be updated!')
                return redirect('caylar_page')
    else:
        # Initialize the form with the current magnet information
        form = CaylarForm(initial={
            'caylar_host': caylar_host["host"] if caylar_host["host"] is not None else '',
            'caylar_port': caylar_host["port"] if caylar_host["port"] is not None else '',
            'caylar_current': caylar_host["current"] if caylar_host["current"] is not None else '',
            'caylar_field': caylar_host["field"] if caylar_host["field"] is not None else '',
        })

    # Assign the variables with the initial values
    # magnet_host = caylar_host["host"] if caylar_host["host"] is not None else ''
    # magnet_port = caylar_host["port"] if caylar_host["port"] is not None else ''
    # magnet_current = caylar_host["current"] if caylar_host["current"] is not None else ''
    # magnet_field = caylar_host["field"] if caylar_host["field"] is not None else ''
    context["form"] = form
    context["connected"] = connected
    return render(request, 'home/caylar.html', context)


@login_required(login_url="/login/")
def rfsoc_page_view(request):
    # Load the data from the rfsoc XML file
    Update_rfsoc = construct_rfsoc()
    connected = Update_rfsoc.try_connect()

    xilinx_host = xml_config_to_dict("staticfiles/xilinx_host.xml")
    # IF FILE IS NOT FOUND MAYBE CAN BUILD ONE
    rfsoc_config = xml_config_to_dict("staticfiles/xilinx.xml")
    if connected:
        Update_rfsoc.build_config(rfsoc_config)
        Update_rfsoc.get_config()
        rfsoc_config = xml_config_to_dict("staticfiles/xilinx.xml")
        xilinx_host["time_update"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        dict_to_xml_file(xilinx_host, "staticfiles/xilinx_host.xml")
    else:
        info = "Parameter has not updated since " + xilinx_host[
            "time_update"] + " because not connected with the device!"
        messages.info(request, info)

    FormsetChannel = formset_factory(RFSoCEOMSequenceForm, extra=0)
    FormsetAOM = formset_factory(RFSoCAOMSequenceForm, extra=0)

    if request.method == 'POST':
        if "updateall" in request.POST:
            form = RFSoCConfigForm(request.POST)
            Formset0 = FormsetChannel(request.POST, prefix='formset0')
            Formset1 = FormsetAOM(request.POST, prefix='formset1')

            if all([form.is_valid(), Formset0.is_valid(), Formset1.is_valid()]):
                channel0 = []
                frequency0 = []
                phase0 = []
                gain0 = []
                time0 = []
                length0 = []
                for form0 in Formset0:
                    if form0.cleaned_data.get('channel0') != None:
                        channel0.append([int(x) for x in form0.cleaned_data.get('channel0')])
                    if form0.cleaned_data.get('time0') != None:
                        time0.append(form0.cleaned_data.get('time0'))
                    if form0.cleaned_data.get('length0') != None:
                        length0.append(form0.cleaned_data.get('length0'))
                    if form0.cleaned_data.get('frequency0') != None:
                        frequency0.append(form0.cleaned_data.get('frequency0'))
                    if form0.cleaned_data.get('phase0') != None:
                        phase0.append(form0.cleaned_data.get('phase0'))
                    if form0.cleaned_data.get('gain0') != None:
                        gain0.append(form0.cleaned_data.get('gain0'))
                rfsoc_config["EOM"]["channel_seq0"] = channel0
                rfsoc_config["EOM"]["freq_seq0"] = frequency0
                rfsoc_config["EOM"]["phase_seq0"] = phase0
                rfsoc_config["EOM"]["gain_seq0"] = gain0
                rfsoc_config["EOM"]["time_seq0"] = time0
                rfsoc_config["EOM"]["lengthseq0"] = length0
                time1 = [[], [], [], []]
                length1 = [[], [], [], []]
                pins1 = []
                timeformttl = []
                lengthformttl = []
                pinsformttl = []
                for form1 in Formset1:
                    if form1.cleaned_data.get('aom_pins') != None:
                        pinsformttl.append([int(x) for x in form1.cleaned_data.get('aom_pins')])
                        for pin in form1.cleaned_data.get('aom_pins'):
                            if int(pin) not in pins1:
                                pins1.append(int(pin))
                                pins1.sort()
                            if form1.cleaned_data.get('time1') != None:
                                time1[int(pin)].append(form1.cleaned_data.get('time1'))
                            if form1.cleaned_data.get('length1') != None:
                                length1[int(pin)].append(form1.cleaned_data.get('length1'))
                    if form1.cleaned_data.get('time1') != None:
                        timeformttl.append(form1.cleaned_data.get('time1'))
                    if form1.cleaned_data.get('length1') != None:
                        lengthformttl.append(form1.cleaned_data.get('length1'))

                rfsoc_config["AOM"]["time"] = time1
                rfsoc_config["AOM"]["pins"] = pins1
                rfsoc_config["AOM"]["length"] = length1
                rfsoc_config["AOM"]["timeseqformttl"] = timeformttl
                rfsoc_config["AOM"]["pinsformttl"] = pinsformttl
                rfsoc_config["AOM"]["lengthseqttl"] = lengthformttl
                # Update RFSoC host and port
                xilinx_host["host"] = form.cleaned_data['rfsoc_host']
                xilinx_host["username"] = form.cleaned_data['rfsoc_username']
                xilinx_host["password"] = form.cleaned_data['rfsoc_password']
                xilinx_host["port"] = form.cleaned_data['rfsoc_port'] if form.cleaned_data[
                                                                             'rfsoc_port'] is not None else ''
                xilinx_host["time_update"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                dict_to_xml_file(xilinx_host, "staticfiles/xilinx_host.xml")

                # Update General configuration
                rfsoc_config["adc_trig_offset"] = form.cleaned_data['adc_trig_offset']
                rfsoc_config["soft_avgs"] = form.cleaned_data['soft_avgs']
                rfsoc_config["relax_delay"] = form.cleaned_data['relax_delay']
                rfsoc_config["readout_length"] = form.cleaned_data['readout_length']
                rfsoc_config["pulse_freq"] = form.cleaned_data['pulse_freq']
                rfsoc_config["reps"] = form.cleaned_data['reps']

                # Update EOM configuration
                rfsoc_config["EOM"]["length0"] = form.cleaned_data['eom_length0']
                rfsoc_config["EOM"]["length1"] = form.cleaned_data['eom_length1']
                rfsoc_config["EOM"]["zone0"] = form.cleaned_data['eom_zone0']
                rfsoc_config["EOM"]["mode0"] = form.cleaned_data['eom_mode0']
                rfsoc_config["EOM"]["zone1"] = form.cleaned_data['eom_zone1']
                rfsoc_config["EOM"]["mode1"] = form.cleaned_data['eom_mode1']

                # Update the rfsoc.xml file
                dict_to_xml_file(rfsoc_config, "staticfiles/xilinx.xml")

                if connected:
                    Update_rfsoc.build_config(rfsoc_config)
                    messages.success(request, 'Changes saved successfully in RFSoC!')
                else:
                    # Add success message to the Django messages framework
                    messages.success(request, 'Changes saved successfully in XML!')
                # Add success message to the Django messages framework
                messages.success(request, 'Changes saved successfully!')

                # Redirect to the rfsoc page to reload the page with the updated values
                return redirect('rfsoc_page')
            else:
                messages.warning(request, 'Cannot be updated!')
                return redirect('rfsoc_page')
        elif "updateip" in request.POST:
            form = RFSoCConfigFormIP(request.POST)
            if form.is_valid():
                xilinx_host["host"] = form.cleaned_data['rfsoc_host']
                xilinx_host["username"] = form.cleaned_data['rfsoc_username']
                xilinx_host["password"] = form.cleaned_data['rfsoc_password']
                xilinx_host["port"] = form.cleaned_data['rfsoc_port'] if form.cleaned_data[
                                                                             'rfsoc_port'] is not None else ''
                xilinx_host["time_update"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                dict_to_xml_file(xilinx_host, "staticfiles/xilinx_host.xml")
    else:
        form = RFSoCConfigForm()
        initial_data0 = [
            {'time0': t, 'channel0': ''.join(map(str, c)), 'length0': l, 'frequency0': f, 'phase0': p, 'gain0': g} for
            t, c, l, f, p, g in zip(rfsoc_config["EOM"]["time_seq0"], rfsoc_config["EOM"]["channel_seq0"],
                                    rfsoc_config["EOM"]["lengthseq0"], rfsoc_config["EOM"]["freq_seq0"],
                                    rfsoc_config["EOM"]["phase_seq0"], rfsoc_config["EOM"]["gain_seq0"])]
        initial_data1 = [{'time1': t, 'aom_pins': p, 'length1': l} for t, p, l in
                         zip(rfsoc_config["AOM"]["timeseqformttl"], rfsoc_config["AOM"]["pinsformttl"],
                             rfsoc_config["AOM"]["lengthseqttl"])]
        if len(initial_data0) != 0:
            Formset0 = FormsetChannel(initial=initial_data0, prefix='formset0')
        else:
            FormsetChannel = formset_factory(RFSoCEOMSequenceForm)
            Formset0 = FormsetChannel(prefix='formset0')
        if len(initial_data1) != 0:
            Formset1 = FormsetAOM(initial=initial_data1, prefix='formset1')
        else:
            FormsetAOM = formset_factory(RFSoCAOMSequenceForm)
            Formset1 = FormsetAOM(prefix='formset1')

        # Initialize the form with the current rfsoc information
        form = RFSoCConfigForm(initial={
            'rfsoc_host': xilinx_host["host"],
            'rfsoc_port': xilinx_host["port"],
            'rfsoc_username': xilinx_host["username"],
            'rfsoc_password': xilinx_host["password"],
            'adc_trig_offset': rfsoc_config["adc_trig_offset"],
            'soft_avgs': rfsoc_config["soft_avgs"],
            'relax_delay': rfsoc_config["relax_delay"],
            'readout_length': rfsoc_config["readout_length"],
            'pulse_freq': rfsoc_config["pulse_freq"],
            'reps': rfsoc_config["reps"],
            'eom_length0': rfsoc_config["EOM"]["length0"],
            'eom_length1': rfsoc_config["EOM"]["length1"],
            'eom_zone0': rfsoc_config["EOM"]["zone0"],
            'eom_mode0': rfsoc_config["EOM"]["mode0"],
            'eom_zone1': rfsoc_config["EOM"]["zone1"],
            'eom_mode1': rfsoc_config["EOM"]["mode1"],
        })
    context = {
        "form": form,
        "formset0": Formset0,
        "formset1": Formset1
    }
    return render(request, 'home/rfsoc.html', context)


@login_required(login_url="/login/")
def sx_page_view(request):
    # Load the data from the cryostat XML file
    global SX_instance
    context = {}
    connected = False
    connected_link_1 = False
    connected_link_2 = False
    xml_path = os.path.join("staticfiles", "sx199.xml")
    old_xml_path = os.path.join("staticfiles", "sx199-old.xml")
    if SX_instance is None:
        print("Constructing sx")
        SX_instance = construct_sx()

    SX_instance.connect()
    connected = SX_instance.is_connected()
    if connected:
        connected_link_1 = SX_instance.is_cs_connected(1)
        connected_link_2 = SX_instance.is_cs_connected(2)
    else:
        info = f'SX199 is not connected!'
        messages.error(request, info)

    sx_xml_dict = xml_config_to_dict(xml_path)
    # if connected and connected_link_1:
    if connected_link_1:
        # SX_instance.update_link_2_xml(xml_path, old_xml_path)
        sx_xml_dict["cs_gain_1"], sx_xml_dict["cs_input_1"], sx_xml_dict["cs_speed_1"], sx_xml_dict["cs_shield_1"], \
            sx_xml_dict["cs_isolation_1"], sx_xml_dict["cs_output_1"], sx_xml_dict["cs_curr_1"], sx_xml_dict[
            "cs_volt_1"] = SX_instance.all_report_link(1)
        context["gain1"] = sx_xml_dict["cs_gain_1"]
        context["input1"] = sx_xml_dict["cs_input_1"]
        context["speed1"] = sx_xml_dict["cs_speed_1"]
        context["shield1"] = sx_xml_dict["cs_shield_1"]
        context["isolation1"] = sx_xml_dict["cs_isolation_1"]
        context["output1"] = sx_xml_dict["cs_output_1"]
        context["curr1"] = sx_xml_dict["cs_curr_1"]
        context["volt1"] = sx_xml_dict["cs_volt_1"]
        sx_xml_dict["time_update"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        dict_to_xml_file(sx_xml_dict, xml_path)
        sx_xml_dict = xml_config_to_dict(xml_path)
    else:
        info = "Parameter current source 1 has not updated since " + sx_xml_dict[
            "time_update"] + " because not connected with the device!"
        messages.warning(request, info)

    # if connected and connected_link_2:
    if connected_link_2:
        # SX_instance.update_link_2_xml(xml_path, old_xml_path)
        sx_xml_dict["cs_gain_2"], sx_xml_dict["cs_input_2"], sx_xml_dict["cs_speed_2"], sx_xml_dict["cs_shield_2"], \
            sx_xml_dict["cs_isolation_2"], sx_xml_dict["cs_output_2"], sx_xml_dict["cs_curr_2"], sx_xml_dict[
            "cs_volt_2"] = SX_instance.all_report_link(2)
        context["gain2"] = sx_xml_dict["cs_gain_2"]
        context["input2"] = sx_xml_dict["cs_input_2"]
        context["speed2"] = sx_xml_dict["cs_speed_2"]
        context["shield2"] = sx_xml_dict["cs_shield_2"]
        context["isolation2"] = sx_xml_dict["cs_isolation_2"]
        context["output2"] = sx_xml_dict["cs_output_2"]
        context["curr2"] = sx_xml_dict["cs_curr_2"]
        context["volt2"] = sx_xml_dict["cs_volt_2"]
        sx_xml_dict["time_update"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        dict_to_xml_file(sx_xml_dict, xml_path)
        sx_xml_dict = xml_config_to_dict(xml_path)
    else:
        info = "Parameter current source 2 has not updated since " + sx_xml_dict[
            "time_update"] + " because not connected with the device!"
        messages.warning(request, info)
    if isinstance(sx_xml_dict, str):
        sx_xml_dict = {}

    if request.method == 'POST':
        # Save old XML before updating
        shutil.copy(xml_path, old_xml_path)
        gain_to_current = {
            '0': (-2e-09, 2e-09),
            '1': (-2e-08, 2e-08),
            '2': (-2e-07, 2e-07),
            '3': (-2e-06, 2e-06),
            '4': (-2e-05, 2e-05),
            '5': (-2e-04, 2e-04),
            '6': (-2e-03, 2e-03),
            '7': (-2e-02, 2e-02),
            '8': (-1e-01, 1e-01),
        }
        GAIN_CHOICES = {
            '0': '1nA',
            '1': '10nA',
            '2': '100nA',
            '3': '1uA',
            '4': '10uA',
            '5': '100uA',
            '6': '1mA',
            '7': '10mA',
            '8': '50mA',
        }
        if "update-link-1" in request.POST:
            form = SX199Form(request.POST)
            if form.is_valid() and connected and connected_link_1:
                min_current, max_current = gain_to_current.get(form.cleaned_data['gain1'], (0, 0))
                if min_current <= form.cleaned_data['curr1'] <= max_current:
                    sx_xml_dict["cs_gain_1"] = form.cleaned_data['gain1']
                    sx_xml_dict["cs_input_1"] = form.cleaned_data['input1']
                    sx_xml_dict["cs_speed_1"] = form.cleaned_data['speed1']
                    sx_xml_dict["cs_shield_1"] = form.cleaned_data['shield1']
                    sx_xml_dict["cs_isolation_1"] = form.cleaned_data['isolation1']
                    sx_xml_dict["cs_output_1"] = form.cleaned_data['output1']
                    sx_xml_dict["cs_curr_1"] = form.cleaned_data['curr1']
                    sx_xml_dict["cs_volt_1"] = form.cleaned_data['volt1']
                    dict_to_xml_file(sx_xml_dict, xml_path)
                    # if connected and connected_link_1:
                    #     print("is connected. attempt to update_xml for 1")
                    SX_instance.update_link_1_xml(xml_path, old_xml_path)
                    messages.success(request, 'Changes saved successfully in current source 1!')
                    # else:
                    # Add success message to the Django messages framework
                    # messages.warning(request, 'Device not connected, changes saved only to XML!')
                else:
                    messages.error(request,
                                   f"Invalid current value {form.cleaned_data['curr1']} for Gain "
                                   f"{GAIN_CHOICES.get(form.cleaned_data['gain1'])}. Valid range: "
                                   f"{min_current} to {max_current}")
            else:
                messages.warning(request, 'Invalid current source 1 values! Cannot be updated!')
        elif "update-link-2" in request.POST:
            form = SX199Form(request.POST)
            if form.is_valid() and connected and connected_link_2:
                min_current, max_current = gain_to_current.get(form.cleaned_data['gain2'], (0, 0))
                if min_current <= form.cleaned_data['curr2'] <= max_current:
                    sx_xml_dict["cs_gain_2"] = form.cleaned_data['gain2']
                    sx_xml_dict["cs_input_2"] = form.cleaned_data['input2']
                    sx_xml_dict["cs_speed_2"] = form.cleaned_data['speed2']
                    sx_xml_dict["cs_shield_2"] = form.cleaned_data['shield2']
                    sx_xml_dict["cs_isolation_2"] = form.cleaned_data['isolation2']
                    sx_xml_dict["cs_output_2"] = form.cleaned_data['output2']
                    sx_xml_dict["cs_curr_2"] = form.cleaned_data['curr2']
                    sx_xml_dict["cs_volt_2"] = form.cleaned_data['volt2']
                    dict_to_xml_file(sx_xml_dict, xml_path)
                    # if connected and connected_link_2:
                    #     print("is connected. attempt to update_xml for 2")
                    SX_instance.update_link_2_xml(xml_path, old_xml_path)
                    messages.success(request, 'Changes saved successfully in current source 2!')
                    # else:
                    # Add success message to the Django messages framework
                    # messages.warning(request, 'Device not connected, changes saved only to XML!')
                else:
                    messages.error(request,
                                   f"Invalid current value {form.cleaned_data['curr2']} for Gain "
                                   f"{GAIN_CHOICES.get(form.cleaned_data['gain2'])}. Valid range: "
                                   f"{min_current} to {max_current}")

                # Redirect to the cryostat page to reload the page with the updated values
            else:
                messages.warning(request, 'Invalid current source 2 values! Cannot be updated!')
        return redirect('sx_page')

    else:
        # Initialize the form with the current cryostat information
        form = SX199Form(initial={
            'gain1': sx_xml_dict.get("cs_gain_1", ""),
            'gain2': sx_xml_dict.get("cs_gain_2", ""),
            'input1': sx_xml_dict.get("cs_input_1", ""),
            'input2': sx_xml_dict.get("cs_input_2", ""),
            'shield1': sx_xml_dict.get("cs_shield_1", ""),
            'shield2': sx_xml_dict.get("cs_shield_2", ""),
            'speed1': sx_xml_dict.get("cs_speed_1", ""),
            'speed2': sx_xml_dict.get("cs_speed_2", ""),
            'isolation1': sx_xml_dict.get("cs_isolation_1", ""),
            'isolation2': sx_xml_dict.get("cs_isolation_2", ""),
            'output1': sx_xml_dict.get("cs_output_1", ""),
            'output2': sx_xml_dict.get("cs_output_2", ""),
            'curr1': sx_xml_dict.get("cs_curr_1", ""),
            'curr2': sx_xml_dict.get("cs_curr_2", ""),
            'volt1': sx_xml_dict.get("cs_volt_1", ""),
            'volt2': sx_xml_dict.get("cs_volt_2", ""),
        })

    # Assign the variables with the initial values
    context['connected'] = connected
    context['connectedlink1'] = connected_link_1
    context['connectedlink2'] = connected_link_2
    context['form'] = form
    return render(request, 'home/sx199.html', context)


@login_required(login_url="/login/")
def mercury_page_view(request):
    # Load the data from the cryostat XML file
    context = {}
    Update_mercury = construct_itc()
    connected = Update_mercury.try_connect()
    mercury_host = xml_config_to_dict("staticfiles/mercuryITC.xml")
    if connected:
        Update_mercury.update_all_xml("staticfiles/mercuryITC.xml")
        context["mercury_heater_power"] = Update_mercury.report_heater_power()
        context["mercury_itc_temperature"] = Update_mercury.report_temperature()
        context["mercury_itc_flow_percentage"] = Update_mercury.report_flow_percentage()
        context["mercury_itc_temperature_set_point"] = Update_mercury.report_temperature_set_point()
        context["mercury_itc_voltage"] = Update_mercury.report_voltage()
        context["mercury_itc_automatic_heating"] = Update_mercury.report_automatic_heating()
        context["mercury_itc_automatic_pid"] = Update_mercury.report_automatic_pid()
        context["mercury_itc_valve_open_percentage"] = Update_mercury.report_valve_open_percentage()
        mercury_host["time_update"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        dict_to_xml_file(mercury_host, "staticfiles/mercuryITC.xml")
        mercury_host = xml_config_to_dict("staticfiles/mercuryITC.xml")
    else:
        info = "Parameter has not updated since " + mercury_host[
            "time_update"] + " because not connected with the device!"
        messages.info(request, info)
    if isinstance(mercury_host, str):
        mercury_host = {}

    if request.method == 'POST':
        if "updateall" in request.POST:
            form = MercuryForm(request.POST)
            if form.is_valid():
                mercury_host["host"] = form.cleaned_data['mercury_host']
                mercury_host["port"] = form.cleaned_data['mercury_port']
                mercury_host["heater_power"] = form.cleaned_data['mercury_heater_power']
                # mercury_host["temperature"] = form.cleaned_data['mercury_itc_temperature']
                mercury_host["flow_percentage"] = form.cleaned_data['mercury_itc_flow_percentage']
                mercury_host["temperature_set_point"] = form.cleaned_data['mercury_itc_temperature_set_point']
                mercury_host["voltage"] = form.cleaned_data['mercury_itc_voltage']
                mercury_host["automatic_heating"] = form.cleaned_data['mercury_itc_automatic_heating']
                mercury_host["automatic_pid"] = form.cleaned_data['mercury_itc_automatic_pid']
                dict_to_xml_file(mercury_host, "staticfiles/mercuryITC.xml")

                if connected:
                    Update_mercury.update_all_xml("staticfiles/mercuryITC.xml")
                    messages.success(request, 'Changes saved successfully in MercuryITC!')
                else:
                    # Add success message to the Django messages framework
                    messages.success(request, 'Changes saved successfully in XML!')

                # Redirect to the cryostat page to reload the page with the updated values
                return redirect('mercury_page')
            else:
                messages.warning(request, 'Cannot be updated!')
                return redirect('mercury_page')
        elif "updateip" in request.POST:
            form = MercuryFormIP(request.POST)
            if form.is_valid():
                mercury_host["host"] = form.cleaned_data['mercury_host']
                mercury_host["port"] = form.cleaned_data['mercury_port']
                dict_to_xml_file(mercury_host, "staticfiles/mercuryITC.xml")
                # Add success message to the Django messages framework
                messages.success(request, 'Changes saved successfully in XML!')
        elif "updateconfig" in request.POST:
            form = MercuryFormConfig(request.POST)
            if form.is_valid():
                mercury_host["heater_power"] = form.cleaned_data['mercury_heater_power']
                # mercury_host["ITC_temperature"] = form.cleaned_data['mercury_itc_temperature']
                mercury_host["ITC_flow_percentage"] = form.cleaned_data['mercury_itc_flow_percentage']
                mercury_host["ITC_temperature_set_point"] = form.cleaned_data['mercury_itc_temperature_set_point']
                mercury_host["ITC_voltage"] = form.cleaned_data['mercury_itc_voltage']
                mercury_host["ITC_automatic_heating"] = form.cleaned_data['mercury_itc_automatic_heating']
                mercury_host["ITC_automatic_pid"] = form.cleaned_data['mercury_itc_automatic_pid']
                dict_to_xml_file(mercury_host, "staticfiles/mercuryITC.xml")

                if connected:
                    Update_mercury.update_all_xml("staticfiles/mercuryITC.xml")
                    messages.success(request, 'Changes saved successfully in MercuryITC!')
                else:
                    # Add success message to the Django messages framework
                    messages.success(request, 'Changes saved successfully in XML!')

                # Redirect to the cryostat page to reload the page with the updated values
                return redirect('mercury_page')
            else:
                messages.warning(request, 'Cannot be updated!')
                return redirect('mercury_page')
    else:
        # Initialize the form with the current cryostat information
        form = MercuryForm(initial={
            'mercury_host': mercury_host.get("host", ""),
            'mercury_port': mercury_host.get("port", ""),
            'mercury_heater_power': mercury_host.get("heater_power", ""),
            'mercury_itc_flow_percentage': mercury_host.get("ITC_flow_percentage", ""),
            'mercury_itc_temperature_set_point': mercury_host.get("ITC_temperature_set_point", ""),
            'mercury_itc_voltage': mercury_host.get("ITC_voltage", ""),
            'mercury_itc_automatic_heating': mercury_host.get("ITC_automatic_heating", ""),
            'mercury_itc_automatic_pid': mercury_host.get("ITC_automatic_pid", ""),
        })

    # Assign the variables with the initial values
    # cryostat_host = mercury_host.get("host", "")
    # cryostat_port = mercury_host.get("port", "")
    context['connected'] = connected
    context['form'] = form
    return render(request, 'home/mercury.html', context)


GRFSoC = None
GLaser = None
GCaylar = None
GmercuryITC = None


def start_experiment(request):
    global GRFSoC
    global GLaser
    global GCaylar
    global GmercuryITC
    choosed_device = request.POST.getlist('selected_devices[]')
    choosed_device.append("RFSoC")
    off_device = ["Laser", "RFSoC", "Mercury", "Caylar"]
    on_device = []
    RFSoC, Laser, Caylar, mercuryITC, SX = construct_object()
    rfsoc_status = "OFF"
    if RFSoC.try_connect():
        on_device.append(RFSoC)
        off_device.remove("RFSoC")
        GRFSoC = RFSoC
    if Laser.try_connect() and "Laser" in choosed_device:
        on_device.append(Laser)
        off_device.remove("Laser")
        GLaser = Laser
    if mercuryITC.try_connect() and "Mercury" in choosed_device:
        on_device.append(mercuryITC)
        off_device.remove("Mercury")
        GmercuryITC = mercuryITC
    if Caylar.try_connect() and "Caylar" in choosed_device:
        on_device.append(Caylar)
        off_device.remove("Caylar")
        GCaylar = Caylar

    common_off_devices = set(off_device).intersection(choosed_device)
    if common_off_devices:
        off_device_names = ", ".join(common_off_devices)
        message = f"Experiment cannot be started because {off_device_names} are offline."
        for i in on_device:
            i.disconnect()
        GRFSoC = None
        GLaser = None
        GCaylar = None
        GmercuryITC = None
        return JsonResponse({'message': message}, status=400)

    # All devices are online, continue with starting the experiment
    # Your logic for starting the experiment here
    try:
        os.makedirs(request.POST['file_name'], exist_ok=True)
        print("Directory '%s' created successfully" % request.POST['file_name'])
        # Create and write the information.txt file
        file_path = os.path.join(request.POST['file_name'], 'information.txt')
        with open(file_path, 'w') as file:
            file.write(f"Experiment Name: {request.POST['experiment_name']}\n")
            file.write(f"Description: {request.POST['description']}\n")
    except OSError as error:
        print("Directory '%s' can not be created" % request.POST['file_name'])
        message = ("Directory '%s' can not be created" % request.POST['file_name'])
        return JsonResponse({'message': message}, status=400)
    message = 'Experiment started successfully.'
    return JsonResponse({'message': message})


def stop_experiment(request):
    global GRFSoC
    global GLaser
    global GCaylar
    global GmercuryITC
    GRFSoC.disconnect()
    GLaser.disconnect()
    GCaylar.disconnect()
    GmercuryITC.disconnect()
    GRFSoC = None
    GLaser = None
    GCaylar = None
    GmercuryITC = None
    message = 'Experiment stopped successfully.'
    return JsonResponse({'message': message})


import json
import csv
from datetime import datetime


def append_to_csv(file_path, data, column_headers):
    file_exists = os.path.isfile(file_path)
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(column_headers)
        writer.writerow(data)


def get_live_data_and_run_rfsoc(request):
    global GRFSoC
    global GLaser
    global GCaylar
    global GmercuryITC
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    data = {'laser_status': "OFF",
            'rfsoc_status': "OFF",
            'mercury_status': "OFF",
            'caylar_status': "OFF"}
    if GLaser != None:
        data['laser_status'] = "ON"
        laser_scan_end = GLaser.report_scan_end()
        laser_scan_start = GLaser.report_scan_start()
        laser_scan_offset = GLaser.report_scan_offset()
        laser_scan_frequency = GLaser.report_scan_frequency()
        laser_wavelength = GLaser.report_ctl_wavelength_act()
        laser_current = GLaser.report_current_act()
        laser_voltage = GLaser.report_voltage_act()
        laser_emission = ULaser.report_emission()
        laser_system_health = ULaser.report_system_health()
        laser_column_headers = ['timestamp', 'scan start', 'scan end', 'scan offset', 'scan frequency', 'wavelength',
                                'current', 'voltage', 'emission', 'system health']
        laser_data_row = [timestamp, laser_scan_start, laser_scan_end, laser_scan_offset, laser_scan_frequency,
                          laser_wavelength, laser_current, laser_voltage, laser_emission, laser_system_health]
        laser_csv_file_path = 'laser.csv'
        append_to_csv(laser_csv_file_path, laser_data_row, laser_column_headers)
        data['laser_scan_end'] = laser_scan_end,
        data['laser_scan_start'] = laser_scan_start,
        data['laser_scan_offset'] = laser_scan_offset,
        data['laser_scan_frequency'] = laser_scan_frequency,
        data['laser_wavelength'] = laser_wavelength,
        data['laser_current'] = laser_current,
        data['laser_voltage'] = laser_voltage,
        data['laser_emission'] = laser_emission,
        data['laser_system_health'] = laser_system_health,
    if GCaylar != None:
        data['caylar_status'] = "ON"
        caylar_current = GCaylar.current()
        caylar_field = GCaylar.field()
        caylar_ADCDAC_temp = GCaylar.ADCDAC_temp()
        caylar_box_temp = GCaylar.box_temp()
        caylar_rack_temp = GCaylar.rack_temp()
        caylar_water_temp = GCaylar.water_temp()
        caylar_water_flow = GCaylar.water_flow()
        caylar_column_headers = ['timestamp', 'current', 'field', 'ADCDAC temp', 'box temp', 'rack temp', 'water temp',
                                 'water flow']
        caylar_data_row = [timestamp, caylar_current, caylar_field, caylar_ADCDAC_temp, caylar_box_temp,
                           caylar_rack_temp, caylar_water_temp, caylar_water_flow]
        caylar_csv_file_path = 'caylar.csv'
        append_to_csv(caylar_csv_file_path, caylar_data_row, caylar_column_headers)
        data['caylar_current'] = caylar_current,
        data['caylar_field'] = caylar_field,
        data['caylar_ADCDAC_temp'] = caylar_ADCDAC_temp,
        data['caylar_box_temp'] = caylar_box_temp,
        data['caylar_rack_temp'] = caylar_rack_temp,
        data['caylar_water_temp'] = caylar_water_temp,
        data['caylar_water_flow'] = caylar_water_flow,
    if GmercuryITC != None:
        data['mercury_status'] = "ON"
        itc_heater_power = GmercuryITC.report_heater_power()
        itc_temperature = GmercuryITC.report_temperature()
        itc_flow_percentage = GmercuryITC.report_flow_percentage()
        itc_temperature_set_point = GmercuryITC.report_temperature_set_point()
        itc_voltage = GmercuryITC.report_voltage()
        itc_automatic_heating = GmercuryITC.report_automatic_heating()
        itc_automatic_pid = GmercuryITC.report_automatic_heating()
        itc_temperature = GmercuryITC.report_automatic_pid()
        itc_data_row = [timestamp, itc_heater_power, itc_temperature]
        itc_column_headers = ['timestamp', 'Heater Power', 'temperature']
        itc_csv_file_path = 'itc.csv'
        append_to_csv(itc_csv_file_path, itc_data_row, itc_column_headers)
        data['itc_heater_power'] = itc_heater_power,
        data['itc_temperature'] = itc_temperature,

    return JsonResponse(data)


@login_required(login_url="/login/")
def index(request):
    form = ExperimentForm()
    if not request.session.get('script_executed', False):
        request.session['script_executed'] = True
        # Execute any additional logic or actions you need before rendering the HTML
    return render(request, 'home/index.html', {'form': form, 'run': True})


# URFSoC = None
ULaser = None
UCaylar = None
UmercuryITC = None


def update_live_plot(request):
    global ULaser
    global UCaylar
    global UmercuryITC

    data = {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    if ULaser != None:
        data['laser_status'] = "ON"
        laser_scan_end = ULaser.report_scan_end()
        laser_scan_start = ULaser.report_scan_start()
        laser_scan_offset = ULaser.report_scan_offset()
        laser_scan_frequency = ULaser.report_scan_frequency()
        laser_wavelength = ULaser.report_ctl_wavelength_act()
        laser_current = ULaser.report_current_act()
        laser_voltage = ULaser.report_voltage_act()
        laser_emission = ULaser.report_emission()
        laser_system_health = ULaser.report_system_health()
        data['laser_scan_end'] = laser_scan_end,
        data['laser_scan_start'] = laser_scan_start,
        data['laser_scan_offset'] = laser_scan_offset,
        data['laser_scan_frequency'] = laser_scan_frequency,
        data['laser_wavelength'] = laser_wavelength,
        data['laser_current'] = laser_current,
        data['laser_voltage'] = laser_voltage,
        data['laser_emission'] = laser_emission,
        data['laser_system_health'] = laser_system_health,
    if UCaylar != None:
        data['caylar_status'] = "ON"
        caylar_current = UCaylar.current()
        caylar_field = UCaylar.field()
        caylar_ADCDAC_temp = UCaylar.ADCDAC_temp()
        caylar_box_temp = UCaylar.box_temp()
        caylar_rack_temp = UCaylar.rack_temp()
        caylar_water_temp = UCaylar.water_temp()
        caylar_water_flow = UCaylar.water_flow()
        data['caylar_current'] = caylar_current,
        data['caylar_field'] = caylar_field,
        data['caylar_ADCDAC_temp'] = caylar_ADCDAC_temp,
        data['caylar_box_temp'] = caylar_box_temp,
        data['caylar_rack_temp'] = caylar_rack_temp,
        data['caylar_water_temp'] = caylar_water_temp,
        data['caylar_water_flow'] = caylar_water_flow,
    if UmercuryITC != None:
        data['mercury_status'] = "ON"
        itc_heater_power = UmercuryITC.report_heater_power()
        itc_temperature = UmercuryITC.report_temperature()
        data['itc_heater_power'] = itc_heater_power,
        data['itc_temperature'] = itc_temperature,

    return JsonResponse(data)


Drfsoc_status = None
Dlaser_status = None
Dmercury_status = None
Dcaylar_status = None
Dsx_status = None
Dtime = None


def status(request):
    global URFSoC
    global ULaser
    global UCaylar
    global UmercuryITC
    global SX_instance
    global Drfsoc_status
    global Dlaser_status
    global Dmercury_status
    global Dcaylar_status
    global Dsx_status
    global Dtime

    status = {
        'rfsoc_status': Drfsoc_status,
        'laser_status': Dlaser_status,
        'mercury_status': Dmercury_status,
        'caylar_status': Dcaylar_status,
        'sx_status': Dsx_status,
        'Dtime': Dtime
    }

    return JsonResponse(status)


def statusSX(request):
    # global URFSoC
    global SX_instance
    global Dsx_status
    if SX_instance != None:
        SX_instance.disconnect()
        SX_instance = None
    SX = construct_sx()

    if SX.is_connected():
        sx_status = "ON"
        SX_instance = SX
        # Laser.disconnect()
        Dsx_status = sx_status
    else:
        sx_status = "OFF"
        Dsx_status = sx_status

    status = {
        'sx_status': sx_status,
    }
    return JsonResponse(status)


def statusLaser(request):
    # global URFSoC
    global ULaser
    global Dlaser_status
    if ULaser != None:
        ULaser.disconnect()
        ULaser = None
    Laser = construct_toptica()

    if Laser.try_connect():
        laser_status = "ON"
        ULaser = Laser
        # Laser.disconnect()
        Dlaser_status = laser_status
    else:
        laser_status = "OFF"
        Dlaser_status = laser_status

    status = {
        'laser_status': laser_status,
    }
    return JsonResponse(status)


def statusRFSoC(request):
    global URFSoC
    global Drfsoc_status

    RFSoC = construct_rfsoc()
    if RFSoC.try_connect():
        rfsoc_status = "ON"
        URFSoC = RFSoC
        Drfsoc_status = rfsoc_status
    else:
        rfsoc_status = "OFF"
        Drfsoc_status = rfsoc_status

    status = {
        'rfsoc_status': rfsoc_status,
    }

    return JsonResponse(status)


def statusMercury(request):
    global UmercuryITC
    global Dmercury_status

    if UmercuryITC != None:
        UmercuryITC = None
    mercuryITC = construct_itc()

    if mercuryITC.try_connect():
        mercury_status = "ON"
        UmercuryITC = mercuryITC
        Dmercury_status = mercury_status
    else:
        mercury_status = "OFF"
        Dmercury_status = mercury_status

    status = {
        'mercury_status': mercury_status,
    }

    return JsonResponse(status)


def statusCaylar(request):
    global UCaylar
    global Dcaylar_status
    global Dtime
    if UCaylar != None:
        UCaylar = None
    Caylar = construct_caylar()

    if Caylar.try_connect():
        caylar_status = "ON"
        UCaylar = Caylar
        Dcaylar_status = caylar_status
    else:
        caylar_status = "OFF"
        Dcaylar_status = caylar_status

    Dtime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    status = {
        'caylar_status': caylar_status,

    }

    return JsonResponse(status)


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))
