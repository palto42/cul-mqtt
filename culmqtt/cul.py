import logging
import os
import time
import sys
from serial import Serial


class CUL(object):
    def __init__(
        self, serial_port, serial_speed=38400, log_level=logging.ERROR
    ):
        super(CUL, self).__init__()
        self._logger = logging.getLogger("cul-mqtt.CUL")
        self._logger.setLevel(log_level)
        self._port = serial_port
        try:
            self._ser = Serial(self._port, serial_speed, timeout=0.1)
        except IOError as e:
            self._logger.error("Can't access device %s : %s", self._port, e)
            sys.exit(1)
        # initialize
        self._ser.write(b"V\n")
        time.sleep(0.1)
        response = self.recv()
        if not response or b"CUL" not in response:  # retry
            self._ser.write(b"V\n")
            time.sleep(1)
            response = self.recv()
        if response and b"CUL" in response:
            self._logger.info(
                "CUL configured and ready: %s", response.strip().decode()
            )
            self._logger.debug("Using serial port %s.", serial_port)
        else:
            self._logger.error(
                "Connection to CUL on port %s failed. Received response: '%s'",
                serial_port,
                response.strip() if response else "",
            )
            sys.exit(1)

    def __del__(self):
        if hasattr(self, "_fd"):
            os.close(self._fd)

    def send(self, msg):
        if type(msg) == bytes:
            msg = msg.decode("ascii")
        if not msg.endswith("\n"):
            msg += "\n"
        self._ser.write(msg.encode("ascii"))
        self._logger.debug("Message transmitted: '%s'.", msg.strip())

    def recv(self):
        if self._ser.in_waiting > 0:
            msg = self._ser.read_until("\n", 100)
            self._logger.debug("Message received: '%s'.", msg.strip())
            return msg
        return None
