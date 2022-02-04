from apscheduler.schedulers.base import BaseScheduler
from homie.device_base import Device_Base
from homie.node.node_base import Node_Base
from homie.node.property.property_humidity import Property_Humidity
from homie.node.property.property_speed import Property_Speed
from homie.node.property.property_temperature import Property_Temperature
from miio import AirHumidifierMiot
from miio.airhumidifier_miot import OperationMode

from custom_properties import Property_WaterLevel


class XiaomiAirHumidifier(Device_Base):
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        super().__init__(device_id=device_id, name="Xiaomi Smart Humidifier", mqtt_settings=mqtt_settings)
        self.device = AirHumidifierMiot(
            ip=config['ip'],
            token=config['token']
        )
        status = Node_Base(self, "status", "Status", "status")
        self.add_node(status)
        self.property_temperature = Property_Temperature(status)
        self.property_humidity = Property_Humidity(status)
        self.property_water = Property_WaterLevel(status)
        status.add_property(self.property_temperature)
        status.add_property(self.property_humidity)
        status.add_property(self.property_water)
        speed = Node_Base(self, "speed", "Speed", "speed")
        self.add_node(speed)
        self.property_speed = Property_Speed(speed,
                                             data_format="off,low,mid,high,auto",
                                             set_value=self.set_speed)
        speed.add_property(self.property_speed)
        self.start()
        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])

    def refresh(self):
        status = self.device.status()
        speed = self._create_speed(status.is_on, status.mode)
        self.property_temperature.value = status.temperature
        self.property_humidity.value = status.humidity
        self.property_water.value = status.water_level
        self.property_speed.value = speed

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
