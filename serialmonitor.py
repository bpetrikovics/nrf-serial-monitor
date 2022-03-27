#!/usr/bin/env python3

import os
import time
import argparse
import json

# iot/raw/nrf24/47 h=321,t=261,p=10044,v=3290
# iot/data/sensor47/temperature 26.1
# iot/data/sensor47/humidity 32.1
# iot/data/sensor47/pressure 1004.4
# iot/data/sensor47/vcc 3290

# TODO: discovery: https://www.home-assistant.io/docs/mqtt/discovery/

def activate(basedir: str):
    """ Look for and activate a virtualenv within the given base directory """

    print(f'activate({basedir})')

    for dir in [f.path for f in os.scandir(basedir) if f.is_dir()]:
        print(f'Checking directory ({dir})')
        activate = os.path.join(basedir, dir, 'bin', 'activate_this.py')
        if os.path.isfile(activate):
            print('Found virtualenv in {}, activating'.format(dir))
            try:
                exec(open(activate).read(), {'__file__': activate})
            except Exception as exc:
                print('Could not run activate script. Module imports will most likely fail.', exc)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serial monitor to capture NRF24 radio data via Arduino modem and publish to MQTT")

    parser.add_argument('--port',
        required=False,
        default="/dev/ttyUSB0",
        help="Serial (USB) port to listen on")

    parser.add_argument('--baudrate',
        required=False,
        default=9600,
        help='Set baud rate on serial connection')

    parser.add_argument('--mqtt',
        required=True,
        help='Mosquitto server to connect to')

    return parser.parse_args()

def serial_init(args: argparse.Namespace):
    return serial.Serial(port=args.port, timeout=2, baudrate=args.baudrate, bytesize=8, stopbits=serial.STOPBITS_ONE)

# Not using home-assistant status data yet for anything
def on_connect(client, userdata, flags, rc):
    print("MQTT connected")
    client.subscribe("homeassistant/status")

def on_message(client, userdata, msg):
    if msg.payload == b"online":
        print("Home-assistant restart detected")

def debug_print(msg: str):
    print(f"{time.ctime()} | {msg}")


def main(args: argparse.Namespace):
    print("NRF24 serial monitor starting")

    port = serial_init(args)
    print(f"Serial connected via {port}")

    pid = os.getpid()
    client = mqtt.Client(client_id = f"serialmonitor_{pid}")
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"MQTT connecting to {args.mqtt}")
    client.connect(args.mqtt, 1883, 60)
    client.loop_start()

    lastmsg = dict()

    while (1):
        if(port.in_waiting > 0):
            try:
                buffer = port.readline().decode("ASCII").strip()
            except UnicodeDecodeError as exc:
                print(f"Cannot decode data: {exc}")
                print(f"Input was: '{buffer}'")
                continue

            if not buffer.startswith("R "):
                debug_print(buffer)
                continue

            try:
                # limit number of splits to 2 in case of any short values e.g. 'p= 9999'
                (_, datalen, payload) = buffer.split(' ', 2)
            except ValueError as exc:
                print(f"Cannot extract data: {exc}")
                print(f"Data was: {buffer}")
                continue

            if int(datalen) > 32:
                print("Possible data corruption - NRF24 max payload size exceeded")
                continue

            try:
              (address, measurement) = payload.split(':')
              (network,channel,nodeid) = address.split(',')
            except Exception as exc:
              print(f'Error processing input: {exc}')
              print(payload)
              continue

            now = time.time()
            timedelta = now - lastmsg[address] if lastmsg.get(address) else -1
            lastmsg[address] = time.time()

            debug_print(f"{buffer} | {timedelta:.2f}")

            try: 
                # Publishing the raw data
                client.publish('iot/raw/nrf24/{}.{}/{}'.format(network, channel, nodeid), measurement)

                data = {item[0]: item[1] for item in [chunk.split('=')
                                        for chunk in measurement.split(',')]}

                client.publish('iot/data/sensor{}/temperature'.format(nodeid), int(data['t'])/10)
                client.publish('iot/data/sensor{}/humidity'.format(nodeid), int(data['h'])/10)
                client.publish('iot/data/sensor{}/pressure'.format(nodeid), int(data['p'])/10)
                client.publish('iot/data/sensor{}/vcc'.format(nodeid), data['v'])
                client.publish('iot/data/sensor{}/timedelta'.format(nodeid), timedelta)

            except Exception as exc:
                print(f"Failed to process message: {exc}")
                print(f"Data line was {payload}")

        time.sleep(0.1)

if __name__ == '__main__':

    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    activate(BASEDIR)

    import serial
    import paho.mqtt.client as mqtt

    args = parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        print("Ctrl-C pressed, exiting")

