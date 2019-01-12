""" Script to pack a sinewave into can.
"""

import argparse
from can_link import SocketCanLink, CanMessage
import struct
import time
import math


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("interface")
    args = parser.parse_args()

    can_link = SocketCanLink(args.interface)
    can_link.connect()

    can_id = 1337
    t = 0.0
    f = 1  # Sine wave frequency.
    dt = 0.1
    while True:
        value = 180 * math.sin(t * f * 2 * math.pi)
        data = struct.pack("d", value)
        message = CanMessage(can_id, data)
        can_link.send(message)
        time.sleep(dt)
        t += dt

    can_link.disconnect()


if __name__ == "__main__":
    main()
