import logging

from apscheduler.schedulers.base import BaseScheduler
from homie.device_base import Device_Base
from homie.node.node_base import Node_Base
from homie.node.property.property_humidity import Property_Humidity
from homie.node.property.property_speed import Property_Speed
from homie.node.property.property_temperature import Property_Temperature
from miio import DeviceException
from miio.airpurifier import AirPurifier
from miio.airpurifier import OperationMode


class XiaomiAirPurifier(Device_Base):
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        super().__init__(device_id=device_id, name="Xiaomi Air Purifier 2", mqtt_settings=mqtt_settings)
        self.device = AirPurifier(
            ip=config['ip'],
            token=config['token']
        )
        status = Node_Base(self, "status", "Status", "status")
        self.add_node(status)
        self.property_temperature = Property_Temperature(status)
        self.property_humidity = Property_Humidity(status)
        status.add_property(self.property_temperature)
        status.add_property(self.property_humidity)
        speed = Node_Base(self, "speed", "Speed", "speed")
        self.add_node(speed)
        self.property_speed = Property_Speed(speed,
                                             data_format="off,silent,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,auto",
                                             set_value=self.set_speed)
        speed.add_property(self.property_speed)
        self.start()
        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])

    def refresh(self):
        try:
            status = self.device.status()
            speed = self._create_speed(is_on=status.is_on, mode=status.mode, favorite_level=status.favorite_level)
            self.property_temperature.value = status.temperature
            self.property_humidity.value = status.humidity
            self.property_speed.value = speed
        except DeviceException as e:
            logging.getLogger('XiaomiAirPurifier').warning("Device unreachable: %s" % str(e))

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
