import xml.etree.ElementTree as ET

# Create XML config file
def create_xml_file(filename):
    """
    The function creates an XML file with a root element named "config".
    @param filename - The filename parameter is a string that specifies the name of the XML file that
    will be created.
    """
    # Create the root element
    root = ET.Element("config")

    # Create the tree and write it to the file
    tree = ET.ElementTree(root)
    tree.write(filename)

def read_xml_config(filename):
    """
    The function `read_xml_config` reads an XML file and prints the tag and value of each element in the
    file.
    @param filename - The `filename` parameter is a string that represents the name or path of the XML
    file that you want to read and parse.
    """
    tree = ET.parse(filename)
    root = tree.getroot()

    # Iterate over all elements in the XML tree
    for element in root.iter():
        # Extract the element tag and value
        tag = element.tag
        value = element.text

        # Skip elements with no value
        if value is None:
            continue

        # Print the tag and value
        print(f"{tag}: {value}")

import ast

def xml_to_dict(element):
    """
    The function `xml_to_dict` converts an XML element into a dictionary representation.
    @param element - The parameter "element" is an XML element that you want to convert to a dictionary.
    @returns The function `xml_to_dict` returns a dictionary representation of the XML element passed as
    an argument.
    """
    result = {}
    result.update(element.attrib)

    for child in element:
        child_dict = xml_to_dict(child)
        if child.tag in result:
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_dict)
        else:
            if isinstance(child_dict, str) and child_dict.isdigit():
                result[child.tag] = int(child_dict)
            elif isinstance(child_dict, str) and is_float(child_dict):
                result[child.tag] = float(child_dict)
            elif isinstance(child_dict, str) and is_list(child_dict):
                result[child.tag] = ast.literal_eval(child_dict)
            elif isinstance(child_dict, list):
                result[child.tag] = child_dict
            else:
                result[child.tag] = child_dict

    # Process text content
    if element.text and element.text.strip():
        text_content = element.text.strip()
        if text_content.isdigit():
            result = int(text_content)
        elif is_float(text_content):
            result = float(text_content)
        else:
            result = text_content

    # Convert key to int if possible
    if isinstance(result, dict):
        for key, value in list(result.items()):
            if isinstance(key, str) and key.isdigit():
                result[int(key)] = result.pop(key)

    return result

def is_float(value):
    """
    The function `is_float` checks if a given value can be converted to a float.
    @param value - The parameter "value" is the input that we want to check if it can be converted to a
    float.
    @returns The function is_float returns a boolean value. It returns True if the input value can be
    converted to a float, and False if it cannot be converted.
    """
    try:
        float(value)
        return True
    except ValueError:
        return False

def is_list(value):
    """
    The function checks if a given value is a valid Python list.
    @param value - The parameter `value` is the input that we want to check if it is a list or not.
    @returns The function is_list returns a boolean value indicating whether the input value is a list
    or not.
    """
    try:
        ast.literal_eval(value)
        return isinstance(ast.literal_eval(value), list)
    except (SyntaxError, ValueError):
        return False


def xml_config_to_dict(filename):
    """
    The function `xml_config_to_dict` takes an XML file as input, parses it, and returns a dictionary
    representation of the XML data.
    @param filename - The filename parameter is the name of the XML file that you want to convert to a
    dictionary.
    @returns a dictionary representation of the XML configuration file.
    """
    tree = ET.parse(filename)
    root = tree.getroot()
    return xml_to_dict(root)

def add_value_to_xml(filename, parent_element, element_name, value=None,nested_element=None):
    """
    The function `add_value_to_xml` adds a new element with a value to an XML file, optionally nested
    within another element.
    @param filename - The name of the XML file you want to modify or create.
    @param parent_element - The parent element is the name of the element under which the new element
    will be added. For example, if the parent element is "person", the new element will be added under
    the "person" element in the XML file.
    @param element_name - The name of the element that you want to add or update in the XML file.
    @param value - The value parameter is the value that will be added to the XML element. It can be any
    data type that can be converted to a string, such as a string, integer, float, etc.
    @param nested_element - The parameter "nested_element" is an optional parameter that specifies the
    name of a nested element within the new element. If provided, the value will be added as the text of
    the nested element. If not provided, the value will be added as the text of the new element itself.
    """
    tree = ET.parse(filename)
    root = tree.getroot()

    # Find the parent element where the new value will be added
    parent = root.find(parent_element)

    # If parent element doesn't exist, create it
    if parent is None:
        parent = ET.SubElement(root, parent_element)

    # Create and append the new element with its value
    new_element = parent.find(element_name)
    if new_element is None:
        new_element = ET.SubElement(parent, element_name)
    if nested_element == None:
        new_element.text = str(value)

    if nested_element != None:
        nested_child = new_element.find(nested_element)
        if nested_child == None:
            nested_child = ET.SubElement(new_element, nested_element)
        nested_child.text = str(value)

    # Write the updated tree to the file
    tree.write(filename)

def dict_to_xml(dictionary, parent):
    """
    The function `dict_to_xml` converts a dictionary into an XML structure.
    @param dictionary - The `dictionary` parameter is a Python dictionary that contains the data you
    want to convert to XML. Each key-value pair in the dictionary represents an element in the XML
    structure.
    @param parent - The "parent" parameter is the parent XML element to which the dictionary elements
    will be added as child elements.
    """
    for key, value in dictionary.items():
        if isinstance(value, dict):
            element = ET.SubElement(parent, key)
            dict_to_xml(value, element)
        else:
            element = ET.SubElement(parent, key)
            element.text = str(value)

def dict_to_xml_string(dictionary, root_element_name):
    """
    The function takes a dictionary and a root element name as input, and converts the dictionary into
    an XML string.
    @param dictionary - The `dictionary` parameter is a Python dictionary that contains the data you
    want to convert to XML format. Each key-value pair in the dictionary represents an element in the
    XML structure, where the key is the element name and the value is the element value.
    @param root_element_name - The `root_element_name` parameter is a string that specifies the name of
    the root element in the XML structure.
    @returns an XML string representation of the given dictionary, with the specified root element name.
    """
    root = ET.Element(root_element_name)
    dict_to_xml(dictionary, root)
    xml_string = ET.tostring(root, encoding='utf-8', method='xml')
    return xml_string

def dict_to_xml_file(dictionary, file_name):
    """
    The function takes a dictionary and a file name as input, converts the dictionary to an XML string,
    and saves the XML string to a file with the given name.
    @param dictionary - The dictionary parameter is a Python dictionary object that contains the data
    you want to convert to XML format. Each key-value pair in the dictionary will be converted to an XML
    element.
    @param file_name - The name of the file where the XML data will be saved.
    """
    xml_string = dict_to_xml_string(dictionary, 'data')

    # Save the XML to a file
    with open(file_name, 'wb') as f:
        f.write(xml_string)