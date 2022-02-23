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
        self.properties_ct = {}
        self.capabilities = {}
        self.first_run = True

        self.bridge = Bridge(config['host'], username=config['app-key'])

        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])

    def refresh(self):
        status = self.bridge.get_api()
        if self.first_run:
            self.collect_capabilities(status)
        for group_id in status['groups']:
            name: str = status['groups'][group_id]['name']
            is_on = status['groups'][group_id]['action']['on']
            bri = status['groups'][group_id]['action'].get('bri', None)
            ct = status['groups'][group_id]['action'].get('ct', None)
            lights = status['groups'][group_id]['lights']

            homie_group_id = to_node_key(name)
            if self.get_node(homie_group_id) is None:
                self.add_node_for_group(group_name=name,
                                        group_id=group_id,
                                        homie_group_id=homie_group_id,
                                        lights=lights,
                                        has_bri=bri is not None,
                                        has_ct=ct is not None)

            self.properties_ison[group_id].value = is_on
            if bri is not None:
                self.properties_bri[group_id].value = to_percent(bri)
            if ct is not None:
                self.properties_ct[group_id].value = to_kelvin(ct)

        if self.first_run:
            self.start()
            self.first_run = False
            self.logger.info('Philips Hue integration started!')

    def collect_capabilities(self, status):
        # print(json.dumps(status, indent=4))
        for light_id in status['lights']:
            capabilities = status['lights'][light_id]['capabilities']
            self.capabilities[light_id] = {
                'maxlumen': capabilities.get('control', {}).get('maxlumen', None),
                'min-ct': to_kelvin(capabilities.get('control', {}).get('ct', {}).get('max', None)),
                'max-ct': to_kelvin(capabilities.get('control', {}).get('ct', {}).get('min', None)),
            }

    def add_node_for_group(self, group_name,
                           group_id,
                           homie_group_id,
                           lights: list,
                           has_bri: bool,
                           has_ct: bool):
        node = Node_Base(self, homie_group_id, group_name, 'group')
        self.add_node(node)
        add_property_string(self, 'id', property_name="Internal ID", parent_node_id=homie_group_id).value = group_id
        add_property_int(self, 'lights-count',
                         property_name="Number of lights",
                         parent_node_id=homie_group_id).value = len(lights)
        lumens = [self.capabilities[light_id]['maxlumen'] for light_id in lights]
        add_property_string(self, 'lights-max-brightness',
                            property_name="Max lights brightness",
                            unit="lm",
                            parent_node_id=homie_group_id
                            ).value = str(lumens)

        if node.get_property('ison') is None:
            handler = lambda value, gid=group_id: self.set_group_ison(gid, value)
            property_ison = add_property_boolean(self, 'ison',
                                                 property_name="Turned on",
                                                 parent_node_id=homie_group_id,
                                                 set_handler=handler)
            self.properties_ison[group_id] = property_ison
        if has_bri and node.get_property('brightness') is None:
            handler = lambda value, gid=group_id: self.set_group_bri(gid, value)
            property_bri = add_property_int(self, 'brightness',
                                            min_value=1,
                                            max_value=100,
                                            unit='%',
                                            parent_node_id=homie_group_id,
                                            set_handler=handler)
            self.properties_bri[group_id] = property_bri
            add_property_string(self, 'brightness-transition',
                                property_name="Brightness - start transition",
                                parent_node_id=homie_group_id,
                                retained=False,
                                set_handler=handler)
        if has_ct and node.get_property('color-temperature') is None:
            min_cts = min([self.capabilities[light_id]['min-ct'] for light_id in lights
                           if self.capabilities[light_id]['min-ct'] is not None])
            max_cts = max([self.capabilities[light_id]['max-ct'] for light_id in lights
                           if self.capabilities[light_id]['max-ct'] is not None])

            handler = lambda value, gid=group_id: self.set_group_ct(gid, value)
            property_ct = add_property_int(self, 'color-temperature',
                                           min_value=min_cts,
                                           max_value=max_cts,
                                           parent_node_id=homie_group_id,
                                           set_handler=handler)
            self.properties_ct[group_id] = property_ct
            add_property_string(self, 'color-temperature-transition',
                                property_name="Color Temperature - start transition",
                                parent_node_id=homie_group_id,
                                retained=False,
                                set_handler=handler)

    def set_group_ison(self, group_id, value):
        if value and self.properties_bri[group_id] is not None:
            bri = self.properties_bri[group_id].value
            self.logger.info("Setting group %s ison to %s and setting bri to %s" % (group_id, value, bri))
            data = {'on': True, 'bri': to_254(bri)}
            self.bridge.set_group(int(group_id), data, transitiontime=5)
        else:
            self.logger.info("Setting group %s ison to %s" % (group_id, value))
            self.bridge.set_group(int(group_id), 'on', value, transitiontime=5)

    def set_group_bri(self, group_id, value):
        if isinstance(value, int):
            self.logger.info("Setting group %s bri to %s" % (group_id, value))
            self.bridge.set_group(int(group_id), 'bri', to_254(value), transitiontime=5)
        elif ',' not in value:
            bri = int(value)
            self.logger.info("Setting group %s bri to %s" % (group_id, bri))
            self.bridge.set_group(int(group_id), 'bri', to_254(bri), transitiontime=5)
        else:
            bri = int(value.split(",")[0])
            time = int(value.split(",")[1])
            self.logger.info("Setting group %s bri to %s during %s" % (group_id, bri, time))
            self.bridge.set_group(int(group_id), 'bri', to_254(bri), transitiontime=time)

    def set_group_ct(self, group_id, value):
        if isinstance(value, int):
            self.logger.info("Setting group %s ct to %s" % (group_id, value))
            self.bridge.set_group(int(group_id), 'ct', to_mired(value), transitiontime=5)
        elif ',' not in value:
            ct = int(value)
            self.logger.info("Setting group %s ct to %s" % (group_id, ct))
            self.bridge.set_group(int(group_id), 'ct', to_mired(ct), transitiontime=5)
        else:
            ct = int(value.split(",")[0])
            time = int(value.split(",")[1])
            self.logger.info("Setting group %s ct to %s" % (group_id, ct))
            self.bridge.set_group(int(group_id), 'ct', to_mired(ct), transitiontime=time)


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


def to_percent(value: int):
    if value is None:
        return None
    return int(round(100.0 * float(value) / 254.0))


def to_254(value: int):
    if value is None:
        return None
    return int(round(float(value) * 2.54))


def to_kelvin(mired: int):
    if mired is None:
        return None
    return int(round(1e6 / mired))


def to_mired(kelvin: int):
    if kelvin is None:
        return None
    return int(round(1e6 / kelvin))
