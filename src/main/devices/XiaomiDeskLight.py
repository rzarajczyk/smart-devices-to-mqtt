import logging

from apscheduler.schedulers.base import BaseScheduler
from homie_helpers import IntProperty, BooleanProperty, Homie, Node, State
from miio import DeviceException, Yeelight


class XiaomiDeskLight:
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        self.ip = config['ip']
        self.token = config['token']

        self.device: Yeelight = None

        self.property_ison = BooleanProperty('ison', name="Turned on", set_handler=self.set_ison)
        self.property_bri = IntProperty('brightness', min_value=1, max_value=100, unit='%', set_handler=self.set_bri)
        self.property_ct = IntProperty('color-temperature', min_value=2700, max_value=6500, unit="K", set_handler=self.set_ct)
        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])
        self.homie = Homie(mqtt_settings, device_id, "Xiaomi MI LED Desk Light", nodes=[
            Node("state", properties=[self.property_ct, self.property_ison, self.property_bri])
        ])

    def refresh(self):
        try:
            if self.device is None:
                self.device = Yeelight(
                    ip=self.ip,
                    token=self.token
                )
            status = self.device.status()
            self.property_ison.value = status.is_on
            self.property_bri.value = status.brightness
            self.property_ct.value = status.color_temp
            self.homie.state = State.READY
        except DeviceException as e:
            logging.getLogger('XiaomiDeskLight').warning("Device unreachable: %s" % str(e))
            self.homie.state = State.ALERT

    def set_ison(self, value):
        if value:
            logging.getLogger('XiaomiDeskLight').info('Turning on')
            self.device.on()
        else:
            logging.getLogger('XiaomiDeskLight').info('Turning off')
            self.device.off()

    def set_bri(self, value):
        logging.getLogger('XiaomiDeskLight').info('Setting brightness to %s' % value)
        self.device.set_brightness(value)

    def set_ct(self, value):
        logging.getLogger('XiaomiDeskLight').info('Setting color temperature to %s' % value)
        self.device.set_color_temp(value)
