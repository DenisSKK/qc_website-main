import os
import csv
from devices import DeviceManager
from datetime import datetime


def create_folder_if_not_exists(folder_path):
    """
    The function creates a folder at the specified path if it does not already exist.
    @param folder_path - The folder path is the path to the folder that you want to create if it does
    not already exist.
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


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


class Logger:
    def __init__(self, device_manager=DeviceManager):
        self.device_manager = device_manager

    def log_all_devices(self):
        for device_name in self.device_manager.list_connected_devices():
            self.log_device_by_name(device_name)

    def log_device_by_name(self, name):
        device = self.device_manager.get_device(name)
        if device:
            data, header = device.read_device_data()
            device_csv_file_path = f'logging/{datetime.now().strftime("%Y%m%d/")}{name}.csv'
            append_to_csv(device_csv_file_path, data, header)
            return f"Logged data for {name} in {device_csv_file_path}"
        else:
            return f"Device {name} not found or not connected"


if __name__ == "__main__":
    logger = Logger()
