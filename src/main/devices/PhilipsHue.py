import logging
import re

from apscheduler.schedulers.base import BaseScheduler
from homie.device_base import Device_Base
from homie.node.node_base import Node_Base
from phue import Bridge

from homie_helpers import add_property_string, add_property_boolean, add_property_int


class PhilipsHue(Device_Base):
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        super().__init__(device_id=device_id, name="Philips Hue", mqtt_settings=mqtt_settings)
        self.logger = logging.getLogger('PhilipsHue')

        self.properties_ison = {}
        self.properties_bri = {}
        self.first_run = True

        self.bridge = Bridge(config['host'], username=config['app-key'])

        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])

    def refresh(self):
        status = self.bridge.get_api()
        for group_id in status['groups']:
            name: str = status['groups'][group_id]['name']
            is_on = status['groups'][group_id]['action']['on']
            brightness = status['groups'][group_id]['action'].get('bri', None)
            homie_group_id = to_node_key(name)
            if self.get_node(homie_group_id) is None:
                node = Node_Base(self, homie_group_id, name, 'group')
                self.add_node(node)
                add_property_string(self, 'id', property_name="Internal ID", parent_node_id=homie_group_id).value = group_id

                if node.get_property('ison') is None:
                    property_ison = add_property_boolean(self, 'ison',
                                                         property_name="Turned on",
                                                         parent_node_id=homie_group_id,
                                                         set_handler=lambda value, name=name: self.set_group_ison(name, value))
                    self.properties_ison[group_id] = property_ison
                if node.get_property('brightness') is None and brightness is not None:
                    property_bri = add_property_int(self, 'brightness',
                                                    min_value=0,
                                                    max_value=254,
                                                    parent_node_id=homie_group_id,
                                                    set_handler=lambda value, name=name: self.set_group_bri(name, value))
                    self.properties_bri[group_id] = property_bri

            self.properties_ison[group_id].value = is_on
            if brightness is not None:
                self.properties_bri[group_id].value = brightness

        if self.first_run:
            self.start()
            self.first_run = False

    def set_group_ison(self, group_id, value):
        self.logger.info("Setting group %s ison to %s" % (group_id, value))
        self.bridge.set_group(group_id, 'on', value, transitiontime=5)

    def set_group_bri(self, group_id, value):
        self.logger.info("Setting group %s bri to %s" % (group_id, value))
        self.bridge.set_group(group_id, 'bri', value, transitiontime=5)


def to_node_key(group_name: str) -> str:
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
