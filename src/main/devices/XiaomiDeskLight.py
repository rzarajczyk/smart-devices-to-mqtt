import logging

from apscheduler.schedulers.base import BaseScheduler
from homie.device_base import Device_Base
from miio import DeviceException, Yeelight

from homie_helpers import add_property_int, add_property_boolean


class XiaomiDeskLight(Device_Base):
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        super().__init__(device_id=device_id, name="Xiaomi MI LED Desk Light", mqtt_settings=mqtt_settings)
        self.ip = config['ip']
        self.token = config['token']

        self.device: Yeelight = None

        self.property_ison = add_property_boolean(self, 'ison', property_name="Turned on", parent_node_id="state", set_handler=self.set_ison)
        self.property_bri = add_property_int(self, 'brightness', min_value=1, max_value=100, unit='%', parent_node_id="state", set_handler=self.set_bri)
        self.property_ct = add_property_int(self, 'color-temperature', min_value=2700, max_value=6500, unit="K", parent_node_id="state", set_handler=self.set_ct)
        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])
        self.start()

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
            self.state = "ready"
        except DeviceException as e:
            logging.getLogger('XiaomiDeskLight').warning("Device unreachable: %s" % str(e))
            self.state = "alert"

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
