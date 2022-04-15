import logging
from datetime import datetime

import requests
from apscheduler.schedulers.base import BaseScheduler
from homie_helpers import Homie, Node, FloatProperty, create_homie_id, State


class Gios:
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        self.NORMS = {
            'NO2': [40, 100, 150, 230, 400],
            'PM10': [20, 50, 80, 110, 150],
            'PM2.5': [13, 35, 55, 75, 110]
        }
        self.NORMS_READABLE = ['Bardzo dobry', 'Dobry', 'Umiarkowany', 'Dostateczny', 'Zły', 'Bardzo zły']

        self.station_id = config['station-id']

        self.properties = {
            "C6H6": FloatProperty('c6h5', name="Benzen (C6H6)", unit="μg/m3", meta={'Measurement date': '0', 'Description': ''}),
            "CO": FloatProperty('co', name="Tlenek węgla (CO)", unit="μg/m3", meta={'Measurement date': '1', 'Description': ''}),
            "NO2": FloatProperty('no2', name="Dwutlenek azotu (NO2)", unit="μg/m3", meta={'Measurement date': '2', 'Description': ''}),
            "PM10": FloatProperty('pm10', name="Pył zawieszony PM 10", unit="μg/m3", meta={'Measurement date': '3', 'Description': ''}),
            "PM2.5": FloatProperty('pm25', name="Pył zawieszony PM 2.5", unit="μg/m3", meta={'Measurement date': '4', 'Description': ''}),
        }

        self.homie = Homie(mqtt_settings, device_id, "GIOS AirQuality data", nodes=[
            Node("measurements", properties=self.properties.values())
        ])

        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'], next_run_time=datetime.now())

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

                # self.homie[create_homie_id(sensor_code)] = last_value
                # self.homie.meta[create_homie_id(sensor_code)] = {'Measurement date': last_date, 'Description': 'TODO'}
            self.homie.state = State.READY
        except Exception as e:
            logging.getLogger('Gios').warning("Service unreachable: %s" % str(e))
            self.homie.state = State.ALERT


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
