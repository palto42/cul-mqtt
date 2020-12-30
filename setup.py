from setuptools import setup
from culmqtt import __version__ as ver


setup(
    name="culmqtt",
    version=ver,
    description="CUL to MQTT bridge.",
    author="Sven Festersen",
    author_email="sven@sven-festersen.de",
    # url='http://',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        # "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "License :: Public Domain",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Home Automation",
    ],
    python_requires=">=3.6",
    packages=["culmqtt"],
    install_requires=["paho.mqtt"],
    scripts=["cli/cul-mqtt", "cli/start-cul-mqtt"],
)
