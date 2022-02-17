import logging

from apscheduler.schedulers.base import BaseScheduler
from homie.device_base import Device_Base
from miio import AirHumidifierMiot, DeviceException
from miio.airhumidifier_miot import OperationMode

from homie_helpers import add_property_float, add_property_enum, add_property_int


class XiaomiAirHumidifier(Device_Base):
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        super().__init__(device_id=device_id, name="Xiaomi Smart Humidifier", mqtt_settings=mqtt_settings)
        self.device = AirHumidifierMiot(
            ip=config['ip'],
            token=config['token']
        )
        self.property_temperature = add_property_float(self, "temperature", unit="°C")
        self.property_humidity = add_property_float(self, "humidity", unit="%", min_value=0, max_value=100)
        self.property_water = add_property_int(self, "water", property_name="Water level")
        self.property_speed = add_property_enum(self, "speed",
                                                values=["off", "low", "mid", "high", "auto"],
                                                set_handler=self.set_speed,
                                                parent_node_id="speed")
        self.start()
        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])

    def refresh(self):
        try:
            status = self.device.status()
            speed = self._create_speed(status.is_on, status.mode)
            self.property_temperature.value = status.temperature
            self.property_humidity.value = status.humidity
            self.property_water.value = status.water_level
            self.property_speed.value = speed
        except DeviceException as e:
            logging.getLogger('XiaomiAirHumidifier').warning("Device unreachable: %s" % str(e))
            self.property_temperature.value = -1
            self.property_humidity.value = 0
            self.property_water.value = -1
            self.property_speed.value = 'off'

    @staticmethod
    def _create_speed(is_on, mode: OperationMode):
        if not is_on:
            return 'off'
        return str(mode.value).lower()

    def set_speed(self, speed):
        if speed == 'off':
            self.device.off()
        elif speed == 'auto':
            self.device.on()
            self.device.set_mode(OperationMode.Auto)
        elif speed == 'low':
            self.device.on()
            self.device.set_mode(OperationMode.Low)
        elif speed == 'mid':
            self.device.on()
            self.device.set_mode(OperationMode.Mid)
        elif speed == 'high':
            self.device.on()
            self.device.set_mode(OperationMode.High)
        else:
            raise Exception("Unsupported Humidifier speed: %s" % speed)
