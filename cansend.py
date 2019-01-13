""" Utility to send a can message. """


import argparse
from can_link import make_can_link, CanMessage


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("interface")
    parser.add_argument("can_id")
    parser.add_argument("data", help="data as hex text")
    args = parser.parse_args()

    can_link = make_can_link(args.interface)
    can_link.connect()

    can_id = int(args.can_id, 16)
    data = bytes.fromhex(args.data)

    message = CanMessage(can_id, data)
    can_link.send(message)

    can_link.disconnect()


if __name__ == "__main__":
    main()
