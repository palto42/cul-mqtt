import logging
import paho.mqtt.client as paho
import time
from .cul import CUL
import ssl
import sys
import socket


class CULMQTT(object):
    def __init__(
        self,
        cul_port,
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
        delay_send=0.05,
        log_level=logging.ERROR,
    ):
        super(CULMQTT, self).__init__()
        self._cul_port = cul_port
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
        self._delay_send = delay_send
        self._log_level = log_level
        self._send_queue = []
        self._run = False
        self._logger = logging.getLogger("cul-mqtt.MQTT")
        self._logger.setLevel(log_level)

    def on_mqtt_recv(self, client, data, msg):
        mqtt_msg = msg.payload
        self._send_queue.append(mqtt_msg)
        self._logger.debug("Queued received message: %s.", mqtt_msg)
        self._logger.debug("Queue length: %s.", len(self._send_queue))

    def on_mqtt_connect(self, client, data, flags, rc):
        if rc == 0:
            client.subscribe(self._mqtt_topic + "/send")

    def start(self):
        self._run = True
        # configure CUL
        self._cul = CUL(self._cul_port, log_level=self._log_level)
        self._cul.send("X01")
        # set up MQTT client
        self._client = paho.Client(client_id=self._mqtt_client_id)
        if self._password != "" and self._username != "":
            self._client.username_pw_set(self._username, self._password)
        self._client.on_message = self.on_mqtt_recv
        self._client.on_connect = self.on_mqtt_connect
        if self._tls:
            if self._tls_insecure:
                cert_reqs = ssl.CERT_NONE
                self._logger.warning("Will connect to MQTT broker without SSL certificate validation!")
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
            self._logger.error("MQTT connection to port %s refused.", self._mqtt_port)
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
            "Listening for messages with topic '%s/send'.",
            self._mqtt_topic
        )
        self._logger.debug(
            "Incoming messages will be published to '%s/recv'.",
            self._mqtt_topic
        )
        # handle incoming RF transmission
        while self._run:
            time.sleep(0.05)
            rf_msg = self._cul.recv()
            if rf_msg:
                rf_msg = rf_msg.decode("ascii").strip()
                self._client.publish(self._mqtt_topic + "/recv", rf_msg)
                self._logger.debug("Published message: %s.", rf_msg)
                continue
            # send a message from the send queue
            if self._send_queue:
                mqtt_msg = self._send_queue.pop(0)
                self._cul.send(mqtt_msg)
                self._logger.debug(
                    "Queue length: %s.", len(self._send_queue)
                )
                time.sleep(self._delay_send)

    def stop(self):
        self._run = False
        self._logger.info("Stopping CULmqtt")
