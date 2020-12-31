import logging
import signal
from time import sleep


class AppStatus(object):
    """Singleton class to manage program termination."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Set this class up as a singleton."""

        if not cls._instance:
            cls._instance = super(AppStatus, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, apps=[], timeout=10):
        self.run = True
        self._logger = logging.getLogger("cul-mqtt.STATUS")
        self._apps = list(apps)
        self._timeout = int(timeout)
        self.run = True
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def add_app(self, app_instance):
        self._apps += [app_instance]

    def exit_gracefully(self, sig_num, frame):
        self._logger.warning(
            "The program was interrupted by signal '%s'",
            signal.Signals(sig_num).name,
        )
        self.run = False
        running = True
        while self._timeout > 0 and running:
            print("wait", self._timeout)
            running = False
            for app in self._apps:
                print("app", app.status())
                running |= app.status()
            sleep(1)
            self._timeout -= 1
        if running:
            self._logger.error(
                "Program apps hasn't terminated within %s seconds, exit anyway",
                self._timeout,
            )
        else:
            self._logger.warning("The program has been stopped, bye...")
        exit(sig_num)
