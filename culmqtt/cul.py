import logging
import os
import select
import time
import sys


def read_from_fd(fd):
    result = b""
    while not result.endswith(b"\n"):
        result += os.read(fd, 1)
    return result


class CUL(object):
    def __init__(self, serial_port, log_level=logging.ERROR):
        super(CUL, self).__init__()
        self._logger = logging.getLogger("cul-mqtt.CUL")
        self._logger.setLevel(log_level)
        self._port = serial_port
        try:
            self._fd = os.open(self._port, os.O_RDWR)
        except FileNotFoundError:
            self._logger.error("Device %s not available.", self._port)
            sys.exit(1)
        # initialize
        os.write(self._fd, b"V\n")
        time.sleep(0.1)
        response = self.recv()
        if not response or b"CUL" not in response:  # retry
            os.write(self._fd, b"V\n")
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
                response.strip(),
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
        os.set_blocking(self._fd, True)
        os.write(self._fd, msg.encode("ascii"))
        self._logger.debug("Message transmitted: '%s'.", msg.strip())

    def recv(self):
        rin, _, _ = select.select([self._fd], [], [], 0)
        if rin:
            fd = rin[0]
            msg = read_from_fd(fd)
            self._logger.debug("Message received: '%s'.", msg.strip())
            return msg
        return None
