import logging
from datetime import datetime

import requests
from apscheduler.schedulers.base import BaseScheduler
from homie.device_base import Device_Base
from miio import DeviceException

from homie_helpers import add_property_int, add_property_boolean


class PrinterScanner(Device_Base):
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        super().__init__(device_id=device_id, name="HP PhotoSmart B209a-m", mqtt_settings=mqtt_settings)

        self.url = config['url']

        self.property_c = add_property_int(self, "cyan", property_name="Cyan", parent_node_id="ink", unit="%", min_value=0, max_value=100)
        self.property_m = add_property_int(self, "magenta", property_name="Magenta", parent_node_id="ink", unit="%", min_value=0, max_value=100)
        self.property_y = add_property_int(self, "yellow", property_name="Yellow", parent_node_id="ink", unit="%", min_value=0, max_value=100)
        self.property_k = add_property_int(self, "black", property_name="Black", parent_node_id="ink", unit="%", min_value=0, max_value=100)
        self.property_pages = add_property_int(self, "pages", property_name="Printed pages", parent_node_id="status", unit="")

        add_property_boolean(self, "scan", parent_node_id='scanner', retained=False, set_handler=self.scan)

        self.start()
        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'], next_run_time=datetime.now())

    def refresh(self):
        try:
            response = requests.get('%s/print/info' % self.url)
            response.raise_for_status()
            status = response.json()
            self.property_c.value = int(status['cyan'])
            self.property_m.value = int(status['magenta'])
            self.property_y.value = int(status['yellow'])
            self.property_k.value = int(status['black'])
            self.property_pages.value = int(status['total_pages'])
            self.state = "ready"
        except Exception as e:
            logging.getLogger('HPPrinterScanner').warning("Device unreachable: %s" % str(e))
            self.state = "alert"

    def scan(self, value):
        if value:
            requests.post('%s/scan' % self.url)
