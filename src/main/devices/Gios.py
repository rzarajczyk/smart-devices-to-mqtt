import logging
from datetime import datetime

import requests
from apscheduler.schedulers.base import BaseScheduler
from homie.device_base import Device_Base

from homie_helpers import add_property_float


class Gios(Device_Base):
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        super().__init__(device_id=device_id, name="GIOS AirQuality data", mqtt_settings=mqtt_settings)

        self.NORMS = {
            'NO2': [40, 100, 150, 230, 400],
            'PM10': [20, 50, 80, 110, 150],
            'PM2.5': [13, 35, 55, 75, 110]
        }
        self.NORMS_READABLE = ['Bardzo dobry', 'Dobry', 'Umiarkowany', 'Dostateczny', 'Zły', 'Bardzo zły']

        self.station_id = config['station-id']

        self.properties = {
            "C6H6": add_property_float(self, 'c6h5', property_name="Benzen (C6H6)", unit="μg/m3", parent_node_id="measurements", meta={'Measurement date': '0', 'Description': ''}),
            "CO": add_property_float(self, 'co', property_name="Tlenek węgla (CO)", parent_node_id="measurements", unit="μg/m3", meta={'Measurement date': '1', 'Description': ''}),
            "NO2": add_property_float(self, 'no2', property_name="Dwutlenek azotu (NO2)", parent_node_id="measurements", unit="μg/m3", meta={'Measurement date': '2', 'Description': ''}),
            "PM10": add_property_float(self, 'pm10', property_name="Pył zawieszony PM 10", parent_node_id="measurements", unit="μg/m3", meta={'Measurement date': '3', 'Description': ''}),
            "PM2.5": add_property_float(self, 'pm25', property_name="Pył zawieszony PM 2.5", parent_node_id="measurements", unit="μg/m3", meta={'Measurement date': '4', 'Description': ''}),
        }

        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'], next_run_time=datetime.now())

        self.start()

    def refresh(self):
        try:
            station_id = self.station_id
            sensors = requests.get('http://api.gios.gov.pl/pjp-api/rest/station/sensors/%s' % station_id).json()
            for sensor in sensors:
                sensor_id = sensor['id']
                sensor_code = sensor['param']['paramCode']
                data = requests.get('http://api.gios.gov.pl/pjp-api/rest/data/getData/%s' % sensor_id).json()
                last_value = data['values'][0]['value']
                last_date = data['values'][0]['date']
                property = self.properties[sensor_code]
                property.value = last_value
                property.meta = {'Measurement date': last_date, 'Description': ''}
            self.state = "ready"
        except Exception as e:
            logging.getLogger('Gios').warning("Service unreachable: %s" % str(e))
            self.state = "alert"


def describe(self, code, value):
    if code not in self.NORMS:
        # return -1, ''
        return ''
    i = 0
    norms = self.NORMS[code]
    while i < len(norms):
        l = norms[i - 1] if i > 0 else -1
        r = norms[i]
        if l <= value < r:
            # return i, self.NORMS_READABLE[i]
            return self.NORMS_READABLE[i]
        i += 1
    # return len(norms), self.NORMS_READABLE[len(norms)]
    return self.NORMS_READABLE[len(norms)]
