# NRF Serial Monitor

[![CodeQL](https://github.com/bpetrikovics/nrf-serial-monitor/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/bpetrikovics/nrf-serial-monitor/actions/workflows/codeql-analysis.yml)

[![Docker](https://github.com/bpetrikovics/nrf-serial-monitor/actions/workflows/docker-image.yml/badge.svg)](https://github.com/bpetrikovics/nrf-serial-monitor/actions/workflows/cdocker-image.yml)


A small tool I use to receive data from my self-built IOT sensors. Probably not really useful to
anyone else besides me. One day I might create a proper PCB design and publish that as well, along
with the (rather simplistic) arduino code.

Until then - data is received through an NRF24L01 SPI radio board by a small hub, built on a 8Mhz, 3.3V
Arduino Pro Mini clone. The receiver is outputting the data through its UART, connected to a computer
via a CP210x USB/serial dongle, and read by this serial monitor script.  Data is pushed to an MQTT
server and then used by Home Assistant.

# Usage

I use docker for simplicity, also to avoid writing init scripts or systemd unit files; but the script
of course just runs fine on its own as well.

Create an .env file along witht he docker-compose.yaml, and specify the MQTT server address in it, e.g.:

MQTT_IP=1.2.3.4

Then simply bring up the container with docker-compose up -d
