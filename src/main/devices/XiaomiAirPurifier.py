import logging

from apscheduler.schedulers.base import BaseScheduler
from homie_helpers import FloatProperty, EnumProperty, Homie, Node, State
from miio import DeviceException
from miio.airpurifier import AirPurifier
from miio.airpurifier import OperationMode


class XiaomiAirPurifier:
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        self.device = AirPurifier(
            ip=config['ip'],
            token=config['token']
        )

        self.property_temperature = FloatProperty("temperature", unit="°C")
        self.property_humidity = FloatProperty("humidity", unit="%", min_value=0, max_value=100)
        self.property_speed = EnumProperty("speed",
                                           values=["off", "silent", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "auto"],
                                           set_handler=self.set_speed)

        self.homie = Homie(mqtt_settings, device_id, "Xiaomi Air Purifier 2", nodes=[
            Node("status", properties=[self.property_temperature, self.property_humidity]),
            Node("speed", properties=[self.property_speed])
        ])
        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])

    def refresh(self):
        try:
            status = self.device.status()
            speed = self._create_speed(is_on=status.is_on, mode=status.mode, favorite_level=status.favorite_level)
            self.property_temperature.value = status.temperature
            self.property_humidity.value = status.humidity
            self.property_speed.value = speed
            self.homie.state = State.READY
        except DeviceException as e:
            logging.getLogger('XiaomiAirPurifier').warning("Device unreachable: %s" % str(e))
            self.homie.state = State.ALERT

    @staticmethod
    def _create_speed(is_on, mode: OperationMode, favorite_level: int):
        if not is_on:
            return 'off'
        if mode != OperationMode.Favorite:
            return str(mode.value).lower()
        return str(favorite_level)

    def set_speed(self, speed):
        print("Setting speed to %s" % speed)
        if type(speed) == int or speed.isnumeric():
            self.device.set_favorite_level(int(speed))
            self.device.set_mode(OperationMode.Favorite)
        elif speed == 'off':
            self.device.off()
        elif speed == 'auto':
            self.device.set_mode(OperationMode.Auto)
        elif speed == 'silent':
            self.device.set_mode(OperationMode.Silent)
        else:
            raise Exception("Unsupported speed: %s" % speed)
