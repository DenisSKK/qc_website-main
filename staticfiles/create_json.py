import json
import numpy as np

def create_json(config):
        # Write the configuration to a JSON file
        with open('config.json', 'w') as config_file:
                json.dump(config, config_file)
def import_json_file(file_path):
    """
    The function `import_json_file` reads and returns the contents of a JSON file.
    @param file_path - The file path is the location of the JSON file that you want to import. It should
    be a string that specifies the path to the file, including the file name and extension. For example,
    "C:/Users/username/Documents/data.json" or "/home/username/data.json".
    @returns the data loaded from the JSON file.
    """
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def save_list_to_json_file(list_data, file_path):
    """
    The function saves a list of data to a JSON file.
    @param list_data - The data that you want to save to the JSON file. It can be a list or a numpy
    array.
    @param file_path - The file path is the location where you want to save the JSON file. It should
    include the file name and extension. For example, "data.json" or "C:/path/to/file.json".
    """
    if isinstance(list_data, np.ndarray):
        list_data = list_data.tolist()
    with open(file_path, 'w') as file:
        json.dump(list_data, file)
