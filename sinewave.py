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
    parser.add_argument("--can_id", default=1337, type=int)
    parser.add_argument("--freq", default=10, type=float)
    args = parser.parse_args()

    can_link = SocketCanLink(args.interface)
    can_link.connect()

    can_id = args.can_id
    t = 0.0
    f = 1  # Sine wave frequency.
    dt = 1 / args.freq
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
