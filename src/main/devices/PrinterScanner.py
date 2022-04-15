import logging
from datetime import datetime

import requests
from apscheduler.schedulers.base import BaseScheduler
from homie_helpers import Homie, Node, IntProperty, BooleanProperty, State


class PrinterScanner:
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        self.url = config['url']

        self.homie = Homie(mqtt_settings, device_id, "HP PhotoSmart B209a-m", nodes=[
            Node("ink", properties=[
                IntProperty("cyan", unit="%", min_value=0, max_value=100),
                IntProperty("magenta", unit="%", min_value=0, max_value=100),
                IntProperty("yellow", unit="%", min_value=0, max_value=100),
                IntProperty("black", unit="%", min_value=0, max_value=100),
            ]),
            Node("status", properties=[
                IntProperty("pages", name="Printed pages"),
            ]),
            Node("scanner", properties=[
                BooleanProperty("scan", retained=False, set_handler=self.scan)
            ])
        ])

        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'],
                          next_run_time=datetime.now())

    def refresh(self):
        try:
            response = requests.get('%s/print/info' % self.url)
            response.raise_for_status()
            status = response.json()
            self.homie['cyan'] = int(status['cyan'])
            self.homie['magenta'] = int(status['magenta'])
            self.homie['yellow'] = int(status['yellow'])
            self.homie['black'] = int(status['black'])
            self.homie['pages'] = int(status['total_pages'])
            self.homie.state = State.READY
        except Exception as e:
            logging.getLogger('HPPrinterScanner').warning("Device unreachable: %s" % str(e))
            self.homie.state = State.ALERT

    def scan(self, value):
        if value:
            requests.post('%s/scan' % self.url)
