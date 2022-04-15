import logging

from apscheduler.schedulers.base import BaseScheduler
from homie_helpers import create_homie_id, Homie, Node, StringProperty, IntProperty, BooleanProperty, State
from phue import Bridge

DEFAULT_TRANSITION_TIME_DS = 5


class PhilipsHue:
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        self.logger = logging.getLogger('PhilipsHue')

        self.properties_ison = {}
        self.properties_bri = {}
        self.properties_ct = {}
        self.capabilities = {}

        self.bridge = Bridge(config['host'], username=config['app-key'])

        self.homie = self.initialize_homie(mqtt_settings, device_id)

        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])

    def initialize_homie(self, mqtt_settings, device_id):
        status = self.bridge.get_api()
        self.collect_capabilities(status)
        nodes = []
        for group_id in status['groups']:
            name: str = status['groups'][group_id]['name']
            homie_group_id: str = create_homie_id(name)
            is_on = status['groups'][group_id]['action']['on']
            bri = status['groups'][group_id]['action'].get('bri', None)
            ct = status['groups'][group_id]['action'].get('ct', None)
            lights = status['groups'][group_id]['lights']

            properties = [
                StringProperty(self, 'id', name="Internal ID", initial_value=group_id),
                IntProperty('lights-count', name="Number of lights", initial_value=len(lights)),
                StringProperty('bulbs', name="Bulbs", initial_value=self.create_bulbs_descriprtion(lights)),
            ]

            handler_ison = lambda value, gid=group_id: self.set_group_ison(gid, value)
            property_ison = BooleanProperty('ison', name="Turned on", set_handler=handler_ison, initial_value=is_on)
            properties.append(property_ison)
            self.properties_ison[group_id] = property_ison

            if bri is not None:
                handler_bri = lambda value, gid=group_id: self.set_group_bri(gid, value)
                property_bri = IntProperty('brightness',
                                           min_value=1,
                                           max_value=100,
                                           unit='%',
                                           set_handler=handler_bri,
                                           initial_value=to_percent(bri))
                properties.append(property_bri)
                properties.append(StringProperty('brightness-transition',
                                                 name="Change Brightness",
                                                 retained=False,
                                                 data_format="$brightness-transition",
                                                 set_handler=handler_bri))
                self.properties_bri[group_id] = property_bri

            if ct is not None:
                min_cts = min([self.capabilities[light_id]['min-ct'] for light_id in lights
                               if self.capabilities[light_id]['min-ct'] is not None])
                max_cts = max([self.capabilities[light_id]['max-ct'] for light_id in lights
                               if self.capabilities[light_id]['max-ct'] is not None])

                handler_ct = lambda value, gid=group_id: self.set_group_ct(gid, value)
                property_ct = IntProperty('color-temperature',
                                          min_value=min_cts,
                                          max_value=max_cts,
                                          unit="K",
                                          set_handler=handler_ct,
                                          initial_value=to_kelvin(ct))
                properties.append(property_ct)
                properties.append(StringProperty('color-temperature-transition',
                                                 name="Change Color Temp",
                                                 retained=False,
                                                 data_format="$color-temperature-transition",
                                                 set_handler=handler_ct))
                self.properties_ct[group_id] = property_ct

            node = Node(homie_group_id, name=name, type='group', properties=properties)
            nodes.append(node)
        return Homie(mqtt_settings, device_id, "Philips Hue", nodes=nodes)

    def refresh(self):
        try:
            status = self.bridge.get_api()
            for group_id in status['groups']:
                is_on = status['groups'][group_id]['action']['on']
                bri = status['groups'][group_id]['action'].get('bri', None)
                ct = status['groups'][group_id]['action'].get('ct', None)

                self.properties_ison[group_id].value = is_on
                if bri is not None:
                    self.properties_bri[group_id].value = to_percent(bri)
                if ct is not None:
                    self.properties_ct[group_id].value = to_kelvin(ct)
            self.homie.state = State.READY

        except Exception as e:
            self.logger.warning("Hue bridge unreachable: %s" % str(e))
            self.homie.state = State.ALERT

    def collect_capabilities(self, status):
        # print(json.dumps(status, indent=4))
        for light_id in status['lights']:
            capabilities = status['lights'][light_id]['capabilities']
            self.capabilities[light_id] = {
                'maxlumen': capabilities.get('control', {}).get('maxlumen', None),
                'min-ct': to_kelvin(capabilities.get('control', {}).get('ct', {}).get('max', None)),
                'max-ct': to_kelvin(capabilities.get('control', {}).get('ct', {}).get('min', None)),
            }

    def create_bulbs_descriprtion(self, lights):
        bulbs = []
        for light_id in lights:
            maxlumen = self.capabilities[light_id]['maxlumen']
            if maxlumen is None:
                bulbs.append('Plug')
            else:
                name = "Ambiance" if self.capabilities[light_id]['max-ct'] else "White"
                bulbs.append('%s %s lm' % (name, maxlumen))
        return str(bulbs)

    def set_group_ison(self, group_id, value):
        if value and group_id in self.properties_bri:
            bri = self.properties_bri[group_id].value
            self.logger.info("Setting group %s ison to %s and setting bri to %s" % (group_id, value, bri))
            data = {'on': True, 'bri': to_254(bri)}
            self.bridge.set_group(int(group_id), data, transitiontime=DEFAULT_TRANSITION_TIME_DS)
        else:
            self.logger.info("Setting group %s ison to %s" % (group_id, value))
            self.bridge.set_group(int(group_id), 'on', value, transitiontime=DEFAULT_TRANSITION_TIME_DS)

    def set_group_bri(self, group_id, value):
        if isinstance(value, int):
            self.logger.info("Setting group %s bri to %s" % (group_id, value))
            self.bridge.set_group(int(group_id), 'bri', to_254(value), transitiontime=DEFAULT_TRANSITION_TIME_DS)
        elif ',' not in value:
            bri = int(value)
            self.logger.info("Setting group %s bri to %s" % (group_id, bri))
            self.bridge.set_group(int(group_id), 'bri', to_254(bri), transitiontime=DEFAULT_TRANSITION_TIME_DS)
        else:
            bri = int(value.split(",")[0])
            time = int(value.split(",")[1])
            self.logger.info("Setting group %s bri to %s during %s" % (group_id, bri, time))
            self.bridge.set_group(int(group_id), 'bri', to_254(bri), transitiontime=to_ds(time))

    def set_group_ct(self, group_id, value):
        if isinstance(value, int):
            self.logger.info("Setting group %s ct to %s" % (group_id, value))
            self.bridge.set_group(int(group_id), 'ct', to_mired(value), transitiontime=DEFAULT_TRANSITION_TIME_DS)
        elif ',' not in value:
            ct = int(value)
            self.logger.info("Setting group %s ct to %s" % (group_id, ct))
            self.bridge.set_group(int(group_id), 'ct', to_mired(ct), transitiontime=DEFAULT_TRANSITION_TIME_DS)
        else:
            ct = int(value.split(",")[0])
            time = int(value.split(",")[1])
            self.logger.info("Setting group %s ct to %s" % (group_id, ct))
            self.bridge.set_group(int(group_id), 'ct', to_mired(ct), transitiontime=to_ds(time))


def to_ds(value: float):
    if value is None:
        return None
    return int(round(10 * value))


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
