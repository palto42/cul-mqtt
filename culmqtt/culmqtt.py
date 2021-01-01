import logging
import time
import threading
from culmqtt.app_status import AppStatus


class CULMQTT(object):
    def __init__(
        self,
        cul,
        mqtt,
        sub_topic=None,
        delay_send=0.05,
        log_level=logging.ERROR,
    ):
        super(CULMQTT, self).__init__()
        self._cul = cul
        self._mqtt = mqtt
        self._sub_topic = sub_topic
        self._delay_send = delay_send
        self._log_level = log_level
        self._run = False
        self._logger = logging.getLogger("cul-mqtt.MQTT")
        self._logger.setLevel(log_level)
        app_status = AppStatus()
        app_status.add_app(self)

    def start(self):
        self._run = True
        self._mqtt.subscribe(self._sub_topic)
        self._thread = threading.Thread(target=self.run)
        self._thread.start()

    def run(self):
        # handle incoming RF transmission
        while self._run:
            time.sleep(0.05)
            rf_msg = self._cul.recv()
            if rf_msg:
                rf_msg = rf_msg.decode("ascii").strip()
                self._mqtt.publish(rf_msg, sub_topic=self._sub_topic)
                self._logger.debug("Published message: %s.", rf_msg)
                continue
            # send a message from the send queue
            if self._mqtt.has_message(sub_topic=self._sub_topic):
                mqtt_msg = self._mqtt.get_message(sub_topic=self._sub_topic)
                self._logger.debug("Send MQTT message '%s' to CUL", mqtt_msg)
                self._cul.send(mqtt_msg)
                time.sleep(self._delay_send)
        self._run = False

    def stop(self):
        timeout = 1.0
        self._logger.debug("Stop culmqtt thread")
        self._run = False
        self._thread.join(timeout)
        if self._thread.is_alive():
            self._logger.error(
                "Failed to stop CULmqtt thread within %s seconds", timeout
            )
            return False
        else:
            self._logger.info("Stopped CULmqtt thread")
            return True

    def status(self):
        return self._thread.is_alive()
