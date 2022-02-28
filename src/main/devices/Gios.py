from datetime import datetime

import requests
from apscheduler.schedulers.base import BaseScheduler
from homie.device_base import Device_Base

from homie_helpers import add_property_float, add_property_string, add_property_boolean


class Gios(Device_Base):
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        super().__init__(device_id=device_id, name="GIOS AirQuality data", mqtt_settings=mqtt_settings)

        self.station_id = config['station-id']

        self.properties = {
            "C6H6": add_property_float(self, 'c6h5-value', property_name="Benzen (C6H6)", parent_node_id="data", unit=None),
            "CO": add_property_float(self, 'co-value', property_name="Tlenek węgla (CO)", parent_node_id="data", unit=None),
            "NO2": add_property_float(self, 'no2-value', property_name="Dwutlenek azotu (NO2)", parent_node_id="data", unit=None),
            "PM10": add_property_float(self, 'pm10-value', property_name="Pył zawieszony PM 10", parent_node_id="data", unit=None),
            "PM2.5": add_property_float(self, 'pm25-value', property_name="Pył zawieszony PM 2.5", parent_node_id="data", unit=None),
            "date_C6H6": add_property_string(self, 'c6h5-date', property_name="Benzen (C6H6) - data pomiaru", parent_node_id="data", unit=None),
            "date_CO": add_property_string(self, 'co-date', property_name="Tlenek węgla (CO) - data pomiaru", parent_node_id="data", unit=None),
            "date_NO2": add_property_string(self, 'no2-date', property_name="Dwutlenek azotu (NO2) - data pomiaru", parent_node_id="data", unit=None),
            "date_PM10": add_property_string(self, 'pm10-date', property_name="Pył zawieszony PM 10 - data pomiaru", parent_node_id="data", unit=None),
            "date_PM2.5": add_property_string(self, 'pm25-date', property_name="Pył zawieszony PM 2.5 - data pomiaru", parent_node_id="data", unit=None),
        }

        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'], next_run_time=datetime.now())

        self.start()

    def refresh(self):
        station_id = self.station_id
        sensors = requests.get('http://api.gios.gov.pl/pjp-api/rest/station/sensors/%s' % station_id).json()
        for sensor in sensors:
            sensor_id = sensor['id']
            sensor_code = sensor['param']['paramCode']
            data = requests.get('http://api.gios.gov.pl/pjp-api/rest/data/getData/%s' % sensor_id).json()
            last_value = data['values'][0]['value']
            last_date = data['values'][0]['date']
            self.properties[sensor_code].value = last_value
            self.properties["date_%s" % sensor_code].value = last_date
