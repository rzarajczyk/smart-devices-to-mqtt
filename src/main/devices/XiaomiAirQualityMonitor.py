import logging

from apscheduler.schedulers.base import BaseScheduler
from homie.device_base import Device_Base
from homie.node.node_base import Node_Base
from homie.node.property.property_battery import Property_Battery
from miio import AirQualityMonitor, DeviceException

from custom_properties import Property_PM25, Property_IsOn


class XiaomiAirQualityMonitor(Device_Base):
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        super().__init__(device_id=device_id, name="Xiaomi AirQuality Monitor", mqtt_settings=mqtt_settings)
        self.device = AirQualityMonitor(
            ip=config['ip'],
            token=config['token']
        )
        status = Node_Base(self, "status", "Status", "status")
        self.add_node(status)
        self.property_pm25 = Property_PM25(status)
        self.property_battery = Property_Battery(status)
        self.property_ison = Property_IsOn(status)
        status.add_property(self.property_pm25)
        status.add_property(self.property_battery)
        status.add_property(self.property_ison)
        self.start()
        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])

    def refresh(self):
        try:
            status = self.device.status()
            self.property_ison.value = status.is_on
            self.property_pm25.value = status.aqi
            self.property_battery.value = status.battery
        except DeviceException as e:
            logging.getLogger('XiaomiAirQualityMonitor').warning("Device unreachable: %s" % str(e))
