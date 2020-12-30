# cul-mqtt

Connect a CUL device running [culfw](http://culfw.de) via [MQTT](http://mqtt.org/).
Requires Python 3 and paho-mqtt.
Intended for use with openhab.
Tested on Linux and with openhab2.

## Installation

Use the setup script to install:

    python setup.py install
  
## Usage

The setup script installs the `cul-mqtt` command line program.

```txt
usage: cul-mqtt [-h] [-d DEVICE] [-b BROKER] [-P PORT] [-t TOPIC] [-i CLIENTID] [-u USERNAME] [-p PASSWORD] [-c CA_CERTS] [--insecure] [-D DELAYMS] [-v]

CUL to MQTT bridge.

optional arguments:
  -h, --help            show this help message and exit
  -d DEVICE, --device DEVICE
                        Port to of the CUL device
  -b BROKER, --broker BROKER
                        IP address of the MQTT broker
  -P PORT, --port PORT  TCP port of the MQTT broker
  -t TOPIC, --topic TOPIC
                        MQTT topic for this CULT device
  -i CLIENTID, --clientid CLIENTID
                        MQTT client ID
  -u USERNAME, --username USERNAME
                        MQTT broker user name (optional)
  -p PASSWORD, --password PASSWORD
                        MQTT broker password name (optional)
  -c CA_CERTS, --ca-certs CA_CERTS
                        Path to TLS certificates for MQTT broker connection
  --insecure            Allow insecure connection (no CA certificate validation)
  -D DELAYMS, --delayms DELAYMS
                        Delay after sending a message via CUL
  -v, --verbose         Verbose or extra verbose (2x) logging
```

All parameters are optional.
Example:

    cul-mqtt --device /dev/ttyUSB0 --broker localhost

The default client id ist "cul", the default topic "cul". Received RF messages will be published with topic `<mqtt_topic>/recv`.
The program listens to MQTT messages with topic `<mqtt_topic>/send`. All data received this way will be sent to the CUL.

**Important**: messages are not interpreted or preprocessed in any way by `cul-mqtt`.
This has be done separately, e.g. in an openhab rule.

## TODO

* Add signal handler for graceful termination
* Implement YAML configuration file
* Systemd service unit example
