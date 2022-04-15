import logging
import urllib
import urllib.request

import pychromecast
from apscheduler.schedulers.base import BaseScheduler
from bravia_tv import BraviaRC
from homie_helpers import Homie, Node, StringProperty, State, IntProperty, BooleanProperty
from pychromecast import CastBrowser
from pychromecast.controllers.media import MediaController


# remote codes
# https://github.com/FricoRico/Homey.SonyBraviaAndroidTV/blob/develop/definitions/remote-control-codes.js

class SonyBravia:
    def __init__(self, device_id, config, mqtt_settings, scheduler: BaseScheduler):
        self.logger = logging.getLogger('SonyBravia')

        self.device = BraviaRC(config['ip'], mac=config['mac'])

        self.chromecast_ip = config['ip']
        self.chromecast_browser: CastBrowser = None
        self.chromecast: pychromecast.Chromecast = None
        self.media_controller: MediaController = None

        self.property_volume = IntProperty("volume-level",
                                           min_value=0,
                                           max_value=80,
                                           set_handler=self.set_volume)
        self.property_ison = BooleanProperty("ison", name="Turned on", set_handler=self.set_ison)

        self.property_player_app = StringProperty("player-app")
        self.property_player_state = StringProperty("player-state")
        self.property_player_url = StringProperty("player-content-url")
        self.property_player_type = StringProperty("player-content-type")

        self.homie = Homie(mqtt_settings, device_id, "Sony Bravia Android TV", nodes=[
            Node("volume", properties=[self.property_volume]),
            Node("power", properties=[self.property_ison]),
            Node("power", properties=[
                BooleanProperty("reboot", retained=False, set_handler=self.reboot),
                BooleanProperty("turn-on", retained=False, set_handler=self.turn_on),
                BooleanProperty("turn-off", retained=False, set_handler=self.turn_off)
            ]),
            Node("controller", properties=[
                BooleanProperty("play", retained=False, set_handler=self.play),
                BooleanProperty("pause", retained=False, set_handler=self.pause),
                BooleanProperty("next", retained=False, set_handler=self.next),
                BooleanProperty("previous", retained=False, set_handler=self.previous),
                BooleanProperty("up", retained=False, set_handler=self.up),
                BooleanProperty("down", retained=False, set_handler=self.down),
                BooleanProperty("left", retained=False, set_handler=self.left),
                BooleanProperty("right", retained=False, set_handler=self.right),
                BooleanProperty("confirm", retained=False, set_handler=self.confirm),
                BooleanProperty("back", retained=False, set_handler=self.back),
                BooleanProperty("home", retained=False, set_handler=self.home),
                BooleanProperty("input", retained=False, set_handler=self.input)
            ]),
            Node("player", properties=[
                self.property_player_app,
                self.property_player_url,
                self.property_player_state,
                self.property_player_type,
                StringProperty("cast", retained=False, set_handler=self.play_url)
            ])
        ])

        self.pin: str = config['pin']
        self.id: str = config['unique-id']

        scheduler.add_job(self.refresh, 'interval', seconds=config['fetch-interval-seconds'])

    def chromecast_connect(self):
        chromecasts, browser = pychromecast.discovery.discover_chromecasts(known_hosts=[self.chromecast_ip])
        pychromecast.discovery.stop_discovery(browser)
        uuids = []
        for chromecast in chromecasts:
            if chromecast.host == self.chromecast_ip:
                uuids.append(chromecast.uuid)

        chromecasts, browser = pychromecast.get_listed_chromecasts(uuids=uuids, known_hosts=[self.chromecast_ip])
        self.chromecast_browser = browser
        if len(chromecasts) != 1:
            raise Exception('Found %s chromecast devices with UUIDs %s' % (len(chromecasts), str(uuids)))
        self.chromecast = chromecasts[0]
        self.chromecast.wait()
        self.media_controller = self.chromecast.media_controller

    def refresh(self):
        ok = True
        try:
            if not self.device.is_connected():
                self.device.connect(self.pin, self.id, self.id)
            power = self.device.get_power_status()
            if power == 'off':
                self.logger.warning("Sony Bravia is disconnected: %s")
                ok = False
            else:
                volume = self.device.get_volume_info()
                self.property_volume.value = volume['volume'] if 'volume' in volume else -1
                self.homie['ison'] = power == 'active'
        except Exception as e:
            self.logger.warning("Sony Bravia unreachable: %s" % str(e))
            ok = False
        try:
            if self.chromecast is None:
                self.chromecast_connect()
            self.property_player_app.value = self.chromecast.app_display_name
            self.property_player_state.value = self.media_controller.status.player_state
            self.property_player_url.value = self.media_controller.status.content_id
            self.property_player_type.value = self.media_controller.status.content_type
        except Exception as e:
            self.logger.warning("Sony Bravia - Chromecast unreachable: %s" % str(e))
            ok = False
        self.homie.state = State.READY if ok else State.ALERT

    def set_volume(self, volume):
        self.logger.info("Setting volume to: %s" % str(volume))
        self.device.set_volume_level(float(volume) / 100.0)

    def reboot(self, value):
        if value:
            self.logger.info('Rebooting')
            self.device.bravia_req_json("system", self.device._jdata_build("requestReboot", None))

    def set_ison(self, value):
        if value:
            self.turn_on(True)
        else:
            self.turn_off(True)

    def turn_on(self, value):
        if value:
            self.logger.info('Turning on')
            self.device.turn_on()

    def turn_off(self, value):
        if value:
            self.logger.info('Turning off')
            self.device.turn_off()

    def play(self, value):
        if value:
            self.logger.info('Play')
            self.device.media_play()

    def pause(self, value):
        if value:
            self.logger.info('Pause')
            self.device.media_pause()

    def next(self, value):
        if value:
            self.logger.info('Next')
            self.device.media_next_track()

    def previous(self, value):
        if value:
            self.logger.info('Previous')
            self.device.media_previous_track()

    def up(self, value):
        if value:
            self.logger.info('Up')
            self.device.send_req_ircc('AAAAAQAAAAEAAAB0Aw==')

    def down(self, value):
        if value:
            self.logger.info('Down')
            self.device.send_req_ircc('AAAAAQAAAAEAAAB1Aw==')

    def right(self, value):
        if value:
            self.logger.info('Right')
            self.device.send_req_ircc('AAAAAQAAAAEAAAAzAw==')

    def left(self, value):
        if value:
            self.logger.info('Left')
            self.device.send_req_ircc('AAAAAQAAAAEAAAA0Aw==')

    def confirm(self, value):
        if value:
            self.logger.info('Confirm')
            self.device.send_req_ircc('AAAAAQAAAAEAAABlAw==')

    def back(self, value):
        if value:
            self.logger.info('Back')
            self.device.send_req_ircc('AAAAAQAAAAEAAABjAw==')

    def home(self, value):
        if value:
            self.logger.info('Home')
            self.device.send_req_ircc('AAAAAQAAAAEAAABgAw==')

    def input(self, value):
        if value:
            self.logger.info("Select input")
            self.device.send_req_ircc('AAAAAQAAAAEAAAAlAw==')

    def play_url(self, url):
        self.logger.info("Playing URL %s" % url)
        with urllib.request.urlopen(url) as response:
            info = response.info()
            content_type = info.get_content_type()
        self.logger.info("Content type is %s" % content_type)
        self.media_controller.play_media(url, content_type)
        self.media_controller.block_until_active()
