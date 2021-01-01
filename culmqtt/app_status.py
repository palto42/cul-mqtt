import logging
import signal


class AppStatus(object):
    """Singleton class to manage program termination."""

    _instance = None
    _apps = []

    def __new__(cls, *args, **kwargs):
        """Set this class up as a singleton."""

        if not cls._instance:
            cls._instance = super(AppStatus, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, apps=[], timeout=10):
        self.run = True
        self._logger = logging.getLogger("cul-mqtt.STATUS")
        self._timeout = int(timeout)
        self.run = True
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def add_app(self, app_instance):
        self._logger.debug("Register app %s", app_instance)
        self._apps += [app_instance]

    def exit_gracefully(self, sig_num, frame):
        self._logger.warning(
            "The program was interrupted by signal '%s'",
            signal.Signals(sig_num).name,
        )
        terminated = True
        for app in reversed(self._apps):
            self._logger.debug("Stop app %s", app)
            terminated &= app.stop()
        if terminated:
            self._logger.warning("The program has been stopped, bye...")
        else:
            self._logger.error(
                "Program apps hasn't terminated within timeout, exit anyway"
            )
