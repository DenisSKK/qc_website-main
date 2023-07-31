# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import os
# The above code is importing the `reverse` function from the `django.urls` module.

# TODO comment code
from django.views.decorators.csrf import csrf_exempt
import numpy as np
from django import template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms.formsets import formset_factory
# The above code is importing the `require_POST` decorator from the `django.views.decorators.http`
# module. This decorator is used to ensure that a view function only accepts POST requests and returns
# a 405 Method Not Allowed response for any other request method.
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.urls import reverse

from staticfiles.XMLGenerator import xml_config_to_dict, dict_to_xml_file
from .construct_object import construct_object, construct_caylar, construct_itc, construct_rfsoc, construct_toptica, \
    construct_sx
from .forms import LaserForm, RFSoCConfigForm, RFSoCConfigFormIP, CaylarForm, MercuryForm, ExperimentForm, \
    LaserFormConfig, LaserFormIP, RFSoCEOMSequenceForm, RFSoCAOMSequenceForm, CaylarFormIP, CaylarFormConfig, \
    MercuryFormConfig, MercuryFormIP

import threading
import shutil
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Agg')


def two_decimal(number):
    return round(number, 2)


def find_csv(name_file, header):
    # Construct the file path
    csv_file_path = name_file

    # Initialize an empty list to store the data
    data = []

    try:
        with open(csv_file_path, 'r', newline='') as csv_file:
            csv_reader = csv.reader(csv_file)
            csv_header = next(csv_reader)  # Read the header row to get column names

            # Check if the specified header exists in the CSV file
            if header not in csv_header:
                raise ValueError(f"Header '{header}' not found in the CSV file.")

            # Get the index of the specified header
            header_index = csv_header.index(header)

            # Read the data rows and store the last 100 rows in 'data' list
            for data_row in csv_reader:
                value_str = data_row[header_index]
                try:
                    value = float(value_str)  # Attempt to convert to float
                except ValueError:
                    value = value_str  # Use the original value if conversion fails

                data.append(value)

                # Limit the number of rows to 100
                if len(data) > 100:
                    data.pop(0)  # Remove the oldest data entry

    except FileNotFoundError as file_not_found_err:
        print(f"File not found: {file_not_found_err}")
        return False
    except ValueError as value_err:
        print(f"Value error: {value_err}")
        return False

    return data


def format_timestamps(timestamps):
    formatted_timestamps = []

    for timestamp in timestamps:
        dt_obj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        formatted_timestamp = dt_obj.strftime('%Y-%m-%d %H:%M:%S')
        formatted_timestamps.append(formatted_timestamp)

    return formatted_timestamps


import io
import urllib, base64


@csrf_exempt
def plot_view(request):
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        # Read the data from the file
        data = np.loadtxt(file, delimiter='\t')  # Assuming the data is tab-separated

        # Separate the columns
        x = data[:, 0]
        y = data[:, 1]

        # Create the plot
        plt.plot(x, y)
        plt.xlabel("X-axis")
        plt.ylabel("Y-axis")

        # Save the plot to a file with the specified name and path
        today = datetime.today().strftime("%Y-%m-%d")
        plot_directory = f"results/{today}"
        os.makedirs(plot_directory, exist_ok=True)
        plot_count = len(os.listdir(plot_directory))
        plot_path = f"{plot_directory}/result.png"
        plt.savefig(plot_path)
        plt.close()
        plt.plot(x, y)
        plt.xlabel("X-axis")
        plt.ylabel("Y-axis")

        # Save the plot to a file with the specified name and path
        plot_path = "apps/static/assets/img/theme/result.png"
        plt.savefig(plot_path)
        plt.close()

        # Return the plot URL to the frontend
        plot_url = "static/assets/img/theme/result.png"  # Assuming the static files are served from the root
        return JsonResponse({"plot_url": plot_url})

    return render(request, "home/plotresult.html")


SX_instance = None


@login_required(login_url="/login/")
def laser_page_view(request):
    """
    The `laser_page_view` function is a Django view that loads data from an XML file, updates the XML
    file with new values if a form is submitted, and renders a template with the updated values.

    @param request The `request` parameter is an object that represents the HTTP request made by the
    client. It contains information such as the request method (GET, POST, etc.), headers, user session,
    and any data sent with the request. It is used to handle and process the request and generate an
    appropriate response

    @return a rendered HTML template called 'laser.html' with the context data.
    """
    # Load the data from the laser XML file

    Update_Laser = construct_toptica()
    connected = Update_Laser.try_connect()
    toptica_host = xml_config_to_dict("staticfiles/toptica.xml")
    context = {}
    if connected:
        Update_Laser.update_all_xml("staticfiles/toptica.xml")
        context["wavelength_act"] = two_decimal(Update_Laser.report_ctl_wavelength_act())
        context["scan_end"] = two_decimal(Update_Laser.report_scan_end())
        context["scan_start"] = two_decimal(Update_Laser.report_scan_start())
        context["scan_freq"] = two_decimal(Update_Laser.report_scan_frequency())
        context["current_act"] = two_decimal(Update_Laser.report_current_act())
        context["voltage_act"] = two_decimal(Update_Laser.report_voltage_act())
        if Update_Laser.report_standby() == 0:
            context["standby"] = "Power Mode"
        elif Update_Laser.report_standby() == 1:
            context["standby"] = "Standby Mode"
        else:
            context["standby"] = "Transition from standby mode to power mode"
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
                toptica_host["wavelength_act"] = form.cleaned_data['wavelength_act']
                toptica_host["scan_end"] = form.cleaned_data['scan_end']
                toptica_host["scan_start"] = form.cleaned_data['scan_start']
                toptica_host["scan_freq"] = form.cleaned_data['scan_freq']
                toptica_host["voltage_act"] = form.cleaned_data['voltage_act']
                toptica_host["current_act"] = form.cleaned_data['current_act']
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
                toptica_host["voltage_act"] = form.cleaned_data['voltage_act']
                toptica_host["current_act"] = form.cleaned_data['current_act']
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
            'wavelength_act': toptica_host["wavelength_act"] if toptica_host["wavelength_act"] is not None else '',
            'scan_end': toptica_host["scan_end"] if toptica_host["scan_end"] is not None else '',
            'scan_start': toptica_host["scan_start"] if toptica_host["scan_start"] is not None else '',
            'scan_freq': toptica_host["scan_freq"] if toptica_host["scan_freq"] is not None else '',
            'voltage_act': toptica_host["voltage_act"] if toptica_host["voltage_act"] is not None else '',
            'current_act': toptica_host["current_act"] if toptica_host["current_act"] is not None else '',
        })

    context["connected"] = connected
    context["form"] = form
    Update_Laser.disconnect()

    return render(request, 'home/laser.html', context)


@login_required(login_url="/login/")
def caylar_page_view(request):
    """
    The `caylar_page_view` function is a view function in a Django web application that handles requests
    to the Caylar page, updates the XML file with new values, and renders the Caylar template with the
    updated values.

    @param request The `request` parameter is an object that represents the HTTP request made by the
    client. It contains information such as the HTTP method (GET, POST, etc.), headers, user session,
    and any data sent in the request. It is typically passed to view functions in Django to handle the
    request and

    @return a rendered HTML template called 'caylar.html' with the context data.
    """
    # Load the data from the magnet XML file
    context = {}
    Update_caylar = construct_caylar()
    connected = Update_caylar.try_connect()
    caylar_host = xml_config_to_dict("staticfiles/caylar.xml")
    if connected:
        Update_caylar.update_all_xml("staticfiles/caylar.xml")
        context["caylar_current"] = two_decimal(Update_caylar.current)
        context["caylar_field"] = two_decimal(Update_caylar.field)
        context["caylar_voltage"] = two_decimal(Update_caylar.voltage)
        context["caylar_ADCDAC_temp"] = two_decimal(Update_caylar.ADCDAC_temp)
        context["caylar_box_temp"] = two_decimal(Update_caylar.box_temp)
        context["caylar_rack_temp"] = two_decimal(Update_caylar.rack_temp)
        context["caylar_water_temp"] = two_decimal(Update_caylar.water_temp)
        context["caylar_water_flow"] = two_decimal(Update_caylar.water_flow)
        caylar_host["time_update"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        dict_to_xml_file(caylar_host, "staticfiles/caylar.xml")
        caylar_host = xml_config_to_dict("staticfiles/caylar.xml")
    else:
        info = "Parameter has not updated since " + caylar_host[
            "time_update"] + " because not connected with the device!"
        messages.info(request, info)

    if request.method == 'POST':
        if "updatecurrent" in request.POST:
            form = CaylarFormCurrent(request.POST)
            if form.is_valid():
                caylar_host["current"] = form.cleaned_data['caylar_current']
                dict_to_xml_file(caylar_host, "staticfiles/caylar.xml")

                if connected:
                    Update_caylar.current_setter(caylar_host["current"])
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
        elif "updatefield" in request.POST:
            form = CaylarFormField(request.POST)
            if form.is_valid():
                caylar_host["field"] = form.cleaned_data['caylar_field']
                dict_to_xml_file(caylar_host, "staticfiles/caylar.xml")

                if connected:
                    Update_caylar.field_setter(caylar_host["field"])
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
    context["form"] = form
    context["connected"] = connected
    return render(request, 'home/caylar.html', context)


@login_required(login_url="/login/")
def rfsoc_page_view(request):
    """
    The function `rfsoc_page_view` is a view function in a Django web application that handles the
    rendering and processing of a form for updating RFSoC configuration settings.

    @param request The `request` parameter is an object that represents the HTTP request made by the
    client. It contains information such as the HTTP method (GET, POST, etc.), headers, user session,
    and any data sent in the request. It is used to handle and process the request and generate an
    appropriate response

    @return a rendered HTML template with the context variables "form", "formset0", and "formset1".
    """
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
                rfsoc_config = {"EOM": {}, "AOM": {}}
                frequency0 = []
                gain0 = []
                time0 = []
                for form0 in Formset0:
                    if form0.cleaned_data.get('time0') != None:
                        time0.append(form0.cleaned_data.get('time0'))
                    if form0.cleaned_data.get('frequency0') != None:
                        frequency0.append(form0.cleaned_data.get('frequency0'))
                    if form0.cleaned_data.get('gain0') != None:
                        gain0.append(form0.cleaned_data.get('gain0'))
                rfsoc_config["EOM"]["freq_seq0"] = frequency0
                rfsoc_config["EOM"]["gain_seq0"] = gain0
                rfsoc_config["EOM"]["time_seq0"] = time0
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
        initial_data0 = [{'time0': t, 'frequency0': f, 'gain0': int(g)} for t, f, g in
                         zip(rfsoc_config["EOM"]["time_seq0"], rfsoc_config["EOM"]["freq_seq0"],
                             rfsoc_config["EOM"]["gain_seq0"])]
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
    """
    The `mercury_page_view` function loads data from an XML file, updates the XML file if connected to a
    device, and handles form submissions to update the XML file with new values.

    @param request The `request` parameter is an object that represents the HTTP request made by the
    client. It contains information such as the HTTP method (GET, POST, etc.), headers, user session,
    and any data sent in the request. It is typically passed to view functions in Django to handle the
    request and

    @return a rendered HTML template called 'mercury.html' with the context variables.
    """
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

    context['connected'] = connected
    context['form'] = form
    return render(request, 'home/mercury.html', context)


def start_rfsoc_experiment(done_event):
    RRFSoC = construct_rfsoc()
    RRFSoC.try_connect()
    RRFSoC.run_code()
    done_event.set()


done_event = threading.Event()
running_rfsoc = False

GRFSoC = None
GLaser = None
GCaylar = None
GmercuryITC = None


def start_experiment(request):
    """
    The `start_experiment` function starts an experiment by connecting to selected devices, creating a
    directory for the experiment, and writing information about the experiment to a file.

    @param request The `request` parameter is an object that represents the HTTP request made by the
    client. It contains information such as the HTTP method (GET, POST, etc.), headers, and data sent by
    the client.

    @return a JSON response with a message indicating whether the experiment started successfully or
    not.
    """
    # All devices are online, continue with starting the experiment
    combinedXML = {}
    if (request.POST.getlist('selected_devices[]') != None):
        choosed_device = request.POST.getlist('selected_devices[]')
    else:
        choosed_device = request.POST.getlist('selected_devices')
    off_device = ["Laser", "RFSoC", "Mercury", "Caylar"]
    on_device = []
    RFSoC, Laser, Caylar, mercuryITC, SX = construct_object()
    rfsoc_status = "OFF"
    if RFSoC.try_connect() and "RFSoC" in choosed_device:
        on_device.append(RFSoC)
        off_device.remove("RFSoC")
        combinedXML["RFSoC_Host"] = xml_config_to_dict("staticfiles/xilinx_host.xml")
        combinedXML["RFSoC"] = xml_config_to_dict("staticfiles/xilinx.xml")
        # Create a thread to run the function
        global done_event
        global running_rfsoc
        running_rfsoc = True
        thread = threading.Thread(target=start_rfsoc_experiment, args=(done_event,))

        # Start the thread
        thread.start()

    if Laser.try_connect() and "Laser" in choosed_device:
        on_device.append(Laser)
        off_device.remove("Laser")
        combinedXML["toptica"] = xml_config_to_dict("staticfiles/toptica.xml")
    if mercuryITC.try_connect() and "Mercury" in choosed_device:
        on_device.append(mercuryITC)
        off_device.remove("Mercury")
        combinedXML["mercury"] = xml_config_to_dict("staticfiles/mercuryITC.xml")
    if Caylar.try_connect() and "Caylar" in choosed_device:
        on_device.append(Caylar)
        off_device.remove("Caylar")
        combinedXML["caylar"] = xml_config_to_dict("staticfiles/caylar.xml")
    common_off_devices = set(off_device).intersection(choosed_device)
    if common_off_devices:
        off_device_names = ", ".join(common_off_devices)
        message = f"Experiment cannot be started because {off_device_names} are offline."
        for i in on_device:
            i.disconnect()
        return JsonResponse({'message': message}, status=400)

    try:
        os.makedirs(request.POST['file_name'], exist_ok=True)
        print("Directory '%s' created successfully" % request.POST['file_name'])
        # Create and write the information.txt file
        file_path = os.path.join(request.POST['file_name'], 'information.txt')
        with open(file_path, 'w') as file:
            file.write(f"Experiment Name: {request.POST['experiment_name']}\n")
            file.write(f"Description: {request.POST['description']}\n")
            file.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if request.POST['startLogging'] or bool(request.POST['startLogging']) == True:
            dict_to_xml_file(combinedXML, os.path.join(request.POST['file_name'], 'configurations.xml'))
    except OSError as error:
        print("Directory '%s' can not be created" % request.POST['file_name'])
        message = ("Directory '%s' can not be created" % request.POST['file_name'])
        return JsonResponse({'message': message}, status=400)
    message = 'Experiment started successfully.'
    return JsonResponse({'message': message, 'file_name': request.POST['file_name']})


def stop_experiment(request):
    """
    The function `stop_experiment` disconnects various devices and sets their variables to `None`, and
    then returns a JSON response with a success message.

    @param request The `request` parameter is an object that represents the HTTP request made by the
    client. It contains information such as the request method, headers, and body. In this case, it is
    not used in the function, so you can ignore it.

    @return a JSON response with a message indicating that the experiment has been stopped successfully.
    """
    global GRFSoC
    global GLaser
    global GCaylar
    global GmercuryITC
    if GRFSoC != None:
        GRFSoC.disconnect()
    if GLaser != None:
        GLaser.disconnect()
    if GCaylar != None:
        GCaylar.disconnect()
    if GmercuryITC != None:
        GmercuryITC.disconnect()
    GRFSoC = None
    GLaser = None
    GCaylar = None
    GmercuryITC = None
    message = 'Experiment stopped successfully.'
    return JsonResponse({'message': message})


def create_folder_if_not_exists(folder_path):
    """
    The function creates a folder at the specified path if it does not already exist.
    @param folder_path - The folder path is the path to the folder that you want to create if it does
    not already exist.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


import json
import csv
from datetime import datetime


def append_to_csv(file_path, data, column_headers):
    """
    The function appends data to a CSV file, creating the file and adding column headers if it doesn't
    exist.

    @param file_path The file path is the location of the CSV file where you want to append the data. It
    should be a string that specifies the file path, including the file name and extension.
    @param data The "data" parameter is a list of values that you want to append to the CSV file. Each
    value in the list represents a column in the CSV file.
    @param column_headers The column_headers parameter is a list of strings that represents the headers
    for each column in the CSV file. For example, if you have a CSV file with columns "Name", "Age", and
    "Gender", the column_headers parameter would be ['Name', 'Age', 'Gender'].
    """
    folder_path = os.path.dirname(file_path)
    create_folder_if_not_exists(folder_path)

    file_exists = os.path.isfile(file_path)
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(column_headers)
        writer.writerow(data)


@login_required(login_url="/login/")
def index(request):
    """
    This is a view function in a Django web application that renders the index.html template with a form
    and a flag indicating that a script has been executed.

    @param request The `request` parameter is an object that represents the HTTP request made by the
    client. It contains information about the request, such as the HTTP method (GET, POST, etc.),
    headers, user session, and more.

    @return the rendered HTML template 'home/index.html' along with the form and a boolean value 'run'
    set to True.
    """
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
    """
    The function `update_live_plot` retrieves data from various sensors and returns it as a JSON
    response.

    @param request The `request` parameter is the HTTP request object that contains information about
    the current request made to the server. It includes details such as the request method, headers, and
    any data sent with the request. In this code, the `request` parameter is not used, so it can be
    removed if

    @return a JSON response containing the data collected from various sensors and devices.
    """
    global ULaser
    global UCaylar
    global UmercuryITC
    global done_event
    global running_rfsoc
    data = {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if done_event.is_set() and running_rfsoc:
        data["message"] = "The RFSoC has finished its execution."
        done_event.clear()
        running_rfsoc = False
    elif running_rfsoc:
        data["message"] = "The RFSoC is still running or not started yet."
    if ULaser != None:
        data['laser_status'] = "ON"
        try:
            laser_scan_end = round(ULaser.report_scan_end(), 4)
            laser_scan_start = round(ULaser.report_scan_start(), 4)
            laser_scan_frequency = two_decimal(ULaser.report_scan_frequency())
            laser_wavelength = round(ULaser.report_ctl_wavelength_act(), 4)
            laser_current = two_decimal(ULaser.report_current_act())
            laser_voltage = round(ULaser.report_voltage_act(), 4)
            laser_emission = ULaser.report_emission()
            laser_system_health = ULaser.report_system_health()
            laser_column_headers = ['timestamp', 'scan frequency (Hz)', 'wavelength (nm)', 'current (mA)',
                                    'voltage (V)', 'emission', 'system health']
            laser_data_row = [timestamp, laser_scan_frequency, laser_wavelength, laser_current, laser_voltage,
                              laser_emission, laser_system_health]
            laser_csv_file_path = 'logging/' + datetime.now().strftime("%Y%m%d/") + 'laser.csv'
            append_to_csv(laser_csv_file_path, laser_data_row, laser_column_headers)
            data['laser_scan_end'] = laser_scan_end,
            data['laser_scan_start'] = laser_scan_start,
            data['laser_scan_frequency'] = laser_scan_frequency,
            if (request.POST['changePage'] == "true"):
                data['laser_wavelength'] = find_csv(laser_csv_file_path, 'wavelength (nm)'),
                data['laser_current'] = find_csv(laser_csv_file_path, 'current (mA)'),
                data['laser_voltage'] = find_csv(laser_csv_file_path, 'voltage (V)'),
                data['laser_wavelength1'] = laser_wavelength,
                data['laser_current1'] = laser_current,
                data['laser_voltage1'] = laser_voltage,
                data['timestampT'] = find_csv(laser_csv_file_path, 'timestamp'),
            else:
                data['laser_wavelength'] = laser_wavelength,
                data['laser_current'] = laser_current,
                data['laser_voltage'] = laser_voltage,
                data['laser_wavelength1'] = laser_wavelength,
                data['laser_current1'] = laser_current,
                data['laser_voltage1'] = laser_voltage,
                data['timestampT'] = timestamp,
            data['laser_emission'] = laser_emission,
            data['laser_system_health'] = laser_system_health,
        except Exception as e:
            print(e)
    if UCaylar != None:
        data['caylar_status'] = "ON"
        caylar_current = two_decimal(UCaylar.current)
        caylar_voltage = two_decimal(UCaylar.voltage)
        caylar_field = two_decimal(UCaylar.field)
        caylar_ADCDAC_temp = two_decimal(UCaylar.ADCDAC_temp)
        caylar_box_temp = two_decimal(UCaylar.box_temp)
        caylar_rack_temp = two_decimal(UCaylar.rack_temp)
        caylar_water_temp = two_decimal(UCaylar.water_temp)
        caylar_water_flow = two_decimal(UCaylar.water_flow)
        caylar_column_headers = ['timestamp', 'current (A)', 'voltage (V)', 'field (G)', 'ADCDAC temp (Deg)',
                                 'box temp (Deg)', 'rack temp (Deg)', 'water temp (Deg)', 'water flow (L/Min)']
        caylar_data_row = [timestamp, caylar_current, caylar_voltage, caylar_field, caylar_ADCDAC_temp, caylar_box_temp,
                           caylar_rack_temp, caylar_water_temp, caylar_water_flow]
        caylar_csv_file_path = 'logging/' + datetime.now().strftime("%Y%m%d/") + 'caylar.csv'
        append_to_csv(caylar_csv_file_path, caylar_data_row, caylar_column_headers)
        if not (request.POST['changePage'] == "true"):
            data['caylar_current'] = caylar_current,
            data['caylar_voltage'] = caylar_voltage,
            data['caylar_field'] = caylar_field,
            data['caylar_ADCDAC_temp'] = caylar_ADCDAC_temp,
            data['caylar_box_temp'] = caylar_box_temp,
            data['caylar_rack_temp'] = caylar_rack_temp,
            data['caylar_water_temp'] = caylar_water_temp,
            data['caylar_water_flow'] = caylar_water_flow,
            data['caylar_current1'] = caylar_current,
            data['caylar_voltage1'] = caylar_voltage,
            data['caylar_field1'] = caylar_field,
            data['caylar_ADCDAC_temp1'] = caylar_ADCDAC_temp,
            data['caylar_box_temp1'] = caylar_box_temp,
            data['caylar_rack_temp1'] = caylar_rack_temp,
            data['caylar_water_temp1'] = caylar_water_temp,
            data['caylar_water_flow1'] = caylar_water_flow,
            data['timestampC'] = timestamp,
        else:
            data['caylar_current'] = find_csv(caylar_csv_file_path, 'current (A)'),
            data['caylar_voltage'] = find_csv(caylar_csv_file_path, 'voltage (V)'),
            data['caylar_field'] = find_csv(caylar_csv_file_path, 'field (G)'),
            data['caylar_ADCDAC_temp'] = find_csv(caylar_csv_file_path, 'ADCDAC temp (Deg)'),
            data['caylar_box_temp'] = find_csv(caylar_csv_file_path, 'box temp (Deg)'),
            data['caylar_rack_temp'] = find_csv(caylar_csv_file_path, 'rack temp (Deg)'),
            data['caylar_water_temp'] = find_csv(caylar_csv_file_path, 'water temp (Deg)'),
            data['caylar_water_flow'] = find_csv(caylar_csv_file_path, 'water flow (L/Min)'),
            data['caylar_current1'] = caylar_current,
            data['caylar_voltage1'] = caylar_voltage,
            data['caylar_field1'] = caylar_field,
            data['caylar_ADCDAC_temp1'] = caylar_ADCDAC_temp,
            data['caylar_box_temp1'] = caylar_box_temp,
            data['caylar_rack_temp1'] = caylar_rack_temp,
            data['caylar_water_temp1'] = caylar_water_temp,
            data['caylar_water_flow1'] = caylar_water_flow,
            data['timestampC'] = find_csv(caylar_csv_file_path, 'timestamp'),
    if UmercuryITC != None:
        data['mercury_status'] = "ON"
        itc_heater_power = UmercuryITC.report_heater_power()
        itc_temperature = two_decimal(UmercuryITC.report_temperature())
        itc_data_row = [timestamp, itc_heater_power, itc_temperature]
        itc_column_headers = ['timestamp', 'Heater Power', 'temperature (K)']
        itc_csv_file_path = 'logging/' + datetime.now().strftime("%Y%m%d/") + 'itc.csv'
        append_to_csv(itc_csv_file_path, itc_data_row, itc_column_headers)
        if not (request.POST['changePage'] == "true"):
            data['itc_heater_power'] = itc_heater_power,
            data['itc_temperature'] = itc_temperature,
            data['itc_heater_power1'] = itc_heater_power,
            data['itc_temperature1'] = itc_temperature,
            data['timestampM'] = timestamp,
        else:
            data['itc_heater_power'] = find_csv(itc_csv_file_path, 'Heater Power'),
            data['itc_temperature'] = find_csv(itc_csv_file_path, 'temperature (K)'),
            data['itc_heater_power1'] = itc_heater_power,
            data['itc_temperature1'] = itc_temperature,
            data['timestampM'] = find_csv(itc_csv_file_path, 'timestamp'),

    return JsonResponse(data)


Drfsoc_status = None
Dlaser_status = None
Dmercury_status = None
Dcaylar_status = None
Dsx_status = None
Dtime = None


def status(request):
    """
    The function "status" returns a JSON response containing the status of various components and the
    current time.

    @param request The `request` parameter is an object that represents the HTTP request made by the
    client. It contains information such as the request method, headers, and body.

    @return a JSON response containing the status of various variables and their values.
    """
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
    """
    The function `statusLaser` checks the status of a laser and returns a JSON response with the laser
    status.

    @param request The `request` parameter is an object that represents the HTTP request made to the
    server. It contains information about the request, such as the headers, body, and query parameters.
    In this code snippet, the `request` parameter is not used, so it can be removed if it is not needed

    @return a JSON response containing the status of the laser.
    """
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
    """
    The function `statusRFSoC` checks the connection status of an RFSoC device and returns a JSON
    response with the status.

    @param request The `request` parameter is an object that represents the HTTP request made by the
    client. It contains information such as the request method, headers, and body. In this code snippet,
    the `request` parameter is not used, so it can be removed if it is not needed elsewhere in the code

    @return a JSON response containing the status of the RFSoC.
    """
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
    """
    The function `statusMercury` checks the status of a Mercury ITC device and returns a JSON response
    with the status.

    @param request The `request` parameter is an object that represents the HTTP request made by the
    client. It contains information such as the request method, headers, and body. In this case, it is
    used to handle the request and return a JSON response.

    @return a JSON response containing the status of the Mercury device.
    """
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
    """
    The function `statusCaylar` checks the status of the Caylar device and returns a JSON response with
    the status.

    @param request The `request` parameter is an object that represents the HTTP request made by the
    client. It contains information such as the request method, headers, and body. In this case, it is
    used to handle the incoming request and generate a response.

    @return a JSON response containing the status of the "caylar" object.
    """
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
    """
    The `pages` function in Python is responsible for rendering different HTML templates based on the
    URL path provided in the request, and handling any errors that may occur during the rendering
    process.

    @param request The `request` parameter is an object that represents the HTTP request made by the
    client. It contains information about the request, such as the URL, headers, and any data sent with
    the request. In this code, the `request` object is used to determine the URL path and to render the

    @return The function `pages` returns an `HttpResponse` object.
    """
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
