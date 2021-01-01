import logging
import paho.mqtt.client as paho
import ssl
import sys
import socket
from time import sleep
from culmqtt.app_status import AppStatus


class MQTT(object):
    def __init__(
        self,
        mqtt_broker,
        mqtt_port=None,
        mqtt_client_id="cul",
        mqtt_topic="cul",
        username=None,
        password=None,
        tls=False,
        ca_certs=None,
        tls_version=ssl.PROTOCOL_TLSv1_2,
        tls_insecure=False,  # True = no CA check
        log_level=logging.ERROR,
    ):
        super(MQTT, self).__init__()
        self._mqtt_broker = mqtt_broker
        if mqtt_port:
            self._mqtt_port = int(mqtt_port)
        elif tls:
            self._mqtt_port = 8883
        else:
            self._mqtt_port = 1883
        self._mqtt_client_id = mqtt_client_id
        self._mqtt_topic = mqtt_topic
        self._username = username
        self._password = password
        self._tls = tls
        self._ca_certs = ca_certs
        self._tls_version = tls_version
        self._tls_insecure = tls_insecure
        self._log_level = log_level
        self._send_queue = {}
        self._connected = False
        self._logger = logging.getLogger("cul-mqtt.MQTT")
        self._logger.setLevel(log_level)
        app_status = AppStatus()
        app_status.add_app(self)

    def connect(self, timeout=10):
        # set up MQTT client
        self._client = paho.Client(client_id=self._mqtt_client_id)
        if self._password != "" and self._username != "":
            self._client.username_pw_set(self._username, self._password)
        self._client.on_message = self.on_mqtt_recv
        self._client.on_connect = self.on_mqtt_connect
        if self._tls:
            if self._tls_insecure:
                cert_reqs = ssl.CERT_NONE
                self._logger.warning(
                    "Will connect to MQTT broker without SSL certificate validation!"
                )
            else:
                cert_reqs = ssl.CERT_REQUIRED
            self._client.tls_set(
                ca_certs=self._ca_certs,
                certfile=None,
                keyfile=None,
                cert_reqs=cert_reqs,
                tls_version=self._tls_version,
                ciphers=None,
            )
            self._client.tls_insecure_set(self._tls_insecure)
        try:
            self._client.connect(self._mqtt_broker, self._mqtt_port)
        except ConnectionRefusedError:
            self._logger.error(
                "MQTT connection to port %s refused.", self._mqtt_port
            )
            sys.exit(1)
        except ConnectionResetError as e:
            self._logger.error(
                "MQTT connection to %s failed: %s", self._mqtt_broker, e.reason
            )
            sys.exit(1)
        except ssl.SSLCertVerificationError as e:
            self._logger.error(
                "TLS certificate for MQTT connection invalid: %s",
                e.verify_message,
            )
            sys.exit(1)
        except socket.gaierror:
            self._logger.error(
                "Name or service '%s' not known", self._mqtt_broker
            )
            sys.exit(1)
        self._client.loop_start()
        self._logger.info("MQTT transport configured.")
        self._logger.debug("Broker is '%s'.", self._mqtt_broker)
        self._logger.debug("Client id is '%s'.", self._mqtt_client_id)
        self._logger.debug(
            "Incoming messages will be published to '%s/recv'.",
            self._mqtt_topic,
        )
        while not self._connected and timeout > 0:
            timeout -= 1
            sleep(1)
        return self._connected

    def __del__(self):
        self.stop()

    def stop(self):
        self._logger.debug("Disconnect MQTT broker")
        self._client.disconnect()
        self._connected = False
        return True

    def on_mqtt_recv(self, client, data, msg):
        mqtt_msg = msg.payload
        if mqtt_msg:
            self._send_queue[msg.topic].append(mqtt_msg)
            self._logger.debug("MQTT received message: %s.", mqtt_msg)
            self._logger.debug("Queue length: %s.", len(self._send_queue))
        else:
            self._logger.debug("MQTT received empty message, ignored")

    def on_mqtt_connect(self, client, data, flags, rc):
        if rc == 0:
            self._connected = True
            self._logger.info("Connected to MQTT broker")
            # client.subscribe(self._mqtt_topic + "/send/#")
        else:
            self._logger.error("Connection to MQTT broker failed")

    def subscribe(self, sub_topic=None):
        if self._connected:
            topic = self._mqtt_topic + "/send"
            if sub_topic:
                topic += "/" + sub_topic
            self._send_queue[topic] = []
            self._client.subscribe(topic)
            self._logger.debug("Subscribed to topic %s", topic)
        else:
            self._logger.error("Not connected to MQTT broker")

    def get_message(self, sub_topic=None):
        # if sub_topic, find messages with that topic
        topic = self._mqtt_topic + "/send"
        if sub_topic:
            topic += "/" + sub_topic
        self._logger.debug("MQTT queue length for topic '%s': %s.", topic, len(self._send_queue[topic]))
        if self._send_queue[topic]:
            return self._send_queue[topic].pop(0)
        else:
            return None

    def has_message(self, sub_topic=None):
        # if sub_topic, find messages with that topic
        topic = self._mqtt_topic + "/send"
        if sub_topic:
            topic += "/" + sub_topic
        if topic in self._send_queue:
            return len(self._send_queue[topic]) > 0
        else:
            return False

    def publish(self, msg, sub_topic=None):
        topic = self._mqtt_topic + "/recv"
        if sub_topic:
            topic += "/" + sub_topic
        self._client.publish(topic, msg)

    def status(self):
        return self._connected
