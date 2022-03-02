import re

from homie.device_base import Device_Base
from homie.node.node_base import Node_Base
from homie.node.property.property_base import Property_Base
from homie.node.property.property_boolean import Property_Boolean
from homie.node.property.property_enum import Property_Enum
from homie.node.property.property_float import Property_Float
from homie.node.property.property_integer import Property_Integer
from homie.node.property.property_string import Property_String


def create_homie_id(group_name: str) -> str:
    normalized = group_name \
        .lower() \
        .replace('ł', 'l') \
        .replace('ę', 'e') \
        .replace('ó', 'o') \
        .replace('ą', 'a') \
        .replace('ś', 's') \
        .replace('ł', 'l') \
        .replace('ż', 'z') \
        .replace('ź', 'z') \
        .replace('ć', 'c') \
        .replace('ń', 'n')
    return re.sub(r'[^a-z0-9]', '-', normalized).lstrip('-')


def _init(device: Device_Base,
          property_id: str,
          property_name: str,
          parent_node_id: str,
          parent_node_name: str):
    property_name = property_id.capitalize().replace('-', " ") if property_name is None else property_name
    if device.get_node(parent_node_id) is None:
        parent_node_name = parent_node_id.capitalize() if parent_node_name is None else parent_node_name
        node = Node_Base(device, parent_node_id, parent_node_name, parent_node_id)
        device.add_node(node)
    node: Node_Base = device.get_node(parent_node_id)
    return property_name, node


def to_homie_meta(meta: dict) -> dict:
    result = {}
    for key in meta:
        value = meta[key]
        result[create_homie_id(key)] = {
            'name': key,
            'value': value
        }
    return result


def add_property_int(device: Device_Base,
                     property_id: str,
                     property_name: str = None,
                     parent_node_id: str = "status",
                     parent_node_name: str = None,
                     set_handler=None,
                     unit=None,
                     min_value: int = None,
                     max_value: int = None) -> Property_Base:
    property_name, node = _init(device, property_id, property_name, parent_node_id, parent_node_name)
    settable = set_handler is not None
    data_format = "%s:%s" % (min_value, max_value) if min_value is not None and max_value is not None else None
    prop = Property_Integer(node,
                            id=property_id,
                            name=property_name,
                            settable=settable,
                            unit=unit,
                            data_format=data_format,
                            set_value=set_handler)
    node.add_property(prop)
    return prop


def add_property_float(device: Device_Base,
                       property_id: str,
                       property_name: str = None,
                       parent_node_id: str = "status",
                       parent_node_name: str = None,
                       set_handler=None,
                       unit=None,
                       min_value: int = None,
                       max_value: int = None,
                       meta: dict = {}) -> Property_Base:
    property_name, node = _init(device, property_id, property_name, parent_node_id, parent_node_name)
    settable = set_handler is not None
    data_format = "%s:%s" % (min_value, max_value) if min_value is not None and max_value is not None else None
    prop = Property_Float(node,
                          id=property_id,
                          name=property_name,
                          settable=settable,
                          unit=unit,
                          data_format=data_format,
                          set_value=set_handler,
                          meta=to_homie_meta(meta))
    node.add_property(prop)
    return prop


def add_property_boolean(device: Device_Base,
                         property_id: str,
                         property_name: str = None,
                         parent_node_id: str = "status",
                         parent_node_name: str = None,
                         set_handler=None,
                         retained: bool = True,
                         unit=None) -> Property_Base:
    property_name, node = _init(device, property_id, property_name, parent_node_id, parent_node_name)
    settable = set_handler is not None
    prop = Property_Boolean(node,
                            id=property_id,
                            name=property_name,
                            settable=settable,
                            unit=unit,
                            retained=retained,
                            set_value=set_handler)
    node.add_property(prop)
    return prop


def add_property_enum(device: Device_Base,
                      property_id: str,
                      property_name: str = None,
                      parent_node_id: str = "status",
                      parent_node_name: str = None,
                      set_handler=None,
                      unit=None,
                      values: list = []) -> Property_Base:
    property_name, node = _init(device, property_id, property_name, parent_node_id, parent_node_name)
    settable = set_handler is not None
    prop = Property_Enum(node,
                         id=property_id,
                         name=property_name,
                         settable=settable,
                         unit=unit,
                         data_format=",".join(values),
                         set_value=set_handler)
    node.add_property(prop)
    return prop


def add_property_string(device: Device_Base,
                        property_id: str,
                        property_name: str = None,
                        parent_node_id: str = "status",
                        parent_node_name: str = None,
                        retained: bool = True,
                        unit: str = None,
                        data_format: str = None,
                        set_handler=None) -> Property_Base:
    property_name, node = _init(device, property_id, property_name, parent_node_id, parent_node_name)
    settable = set_handler is not None
    prop = Property_String(node,
                           id=property_id,
                           name=property_name,
                           settable=settable,
                           retained=retained,
                           unit=unit,
                           data_format=data_format,
                           set_value=set_handler)
    node.add_property(prop)
    return prop
