import logging

from apscheduler.schedulers.base import BaseScheduler
from homie_helpers import Homie, FloatProperty, EnumProperty, IntProperty, Node, State
from miio import AirHumidifierMiot, DeviceException
from miio.airhumidifier_miot import OperationMode


class XiaomiAirHumidifier:
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        self.device = AirHumidifierMiot(
            ip=config['ip'],
            token=config['token']
        )
        self.homie = Homie(mqtt_settings, device_id, "Xiaomi Smart Humidifier", nodes=[
            Node("status", properties=[
                FloatProperty("temperature", unit="°C"),
                FloatProperty("humidity", unit="%", min_value=0, max_value=100),
                IntProperty("water", name="Water level"),
            ]),
            Node("speed", properties=[
                EnumProperty("speed", values=["off", "low", "mid", "high", "auto"], set_handler=self.set_speed)
            ])
        ])
        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])

    def refresh(self):
        try:
            status = self.device.status()
            speed = self._create_speed(status.is_on, status.mode)
            self.homie['temperature'] = status.temperature
            self.homie['humidity'] = status.temperature
            self.homie['water'] = status.water_level
            self.homie['speed'] = speed
            self.homie.state = State.READY
        except DeviceException as e:
            logging.getLogger('XiaomiAirHumidifier').warning("Device unreachable: %s" % str(e))
            self.homie.state = State.ALERT

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
