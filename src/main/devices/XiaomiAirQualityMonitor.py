import logging

from apscheduler.schedulers.base import BaseScheduler
from homie_helpers import IntProperty, FloatProperty, BooleanProperty, Homie, Node, State
from miio import AirQualityMonitor, DeviceException


class XiaomiAirQualityMonitor:
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        self.device = AirQualityMonitor(
            ip=config['ip'],
            token=config['token']
        )
        self.property_pm25 = FloatProperty("pm25", name="PM 2.5", unit="μg/m³")
        self.property_battery = IntProperty("battery", unit="%", min_value=0, max_value=100)
        self.property_ison = BooleanProperty("ison", name="Is on")

        self.homie = Homie(mqtt_settings, device_id, "Xiaomi AirQuality Monitor", nodes=[
            Node("status", properties=[self.property_pm25, self.property_battery, self.property_ison])
        ])
        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])

    def refresh(self):
        try:
            status = self.device.status()
            self.property_ison.value = status.is_on
            self.property_pm25.value = status.aqi
            self.property_battery.value = status.battery
            self.homie.state = State.READY
        except DeviceException as e:
            logging.getLogger('XiaomiAirQualityMonitor').warning("Device unreachable: %s" % str(e))
            self.homie.state = State.ALERT
