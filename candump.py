""" Simple can dump utility. """

import argparse
from can_link import make_can_link


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("interface")
    args = parser.parse_args()
    can_link = make_can_link(args.interface)
    can_link.connect()

    while True:
        message = can_link.recv()
        print(message)

    can_link.disconnect()


if __name__ == "__main__":
    main()
