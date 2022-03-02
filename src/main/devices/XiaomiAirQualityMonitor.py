import logging

from apscheduler.schedulers.base import BaseScheduler
from homie.device_base import Device_Base
from miio import AirQualityMonitor, DeviceException

from homie_helpers import add_property_int, add_property_float, add_property_boolean


class XiaomiAirQualityMonitor(Device_Base):
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        super().__init__(device_id=device_id, name="Xiaomi AirQuality Monitor", mqtt_settings=mqtt_settings)
        self.device = AirQualityMonitor(
            ip=config['ip'],
            token=config['token']
        )
        self.property_pm25 = add_property_float(self, "pm25", property_name="PM 2.5", unit="μg/m³")
        self.property_battery = add_property_int(self, "battery", unit="%", min_value=0, max_value=100)
        self.property_ison = add_property_boolean(self, "ison", property_name="Is on")

        self.start()
        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])

    def refresh(self):
        try:
            status = self.device.status()
            self.property_ison.value = status.is_on
            self.property_pm25.value = status.aqi
            self.property_battery.value = status.battery
            self.state = "ready"
        except DeviceException as e:
            logging.getLogger('XiaomiAirQualityMonitor').warning("Device unreachable: %s" % str(e))
            self.state = "alert"
