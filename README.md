
This is a CAN bus utility to inspect the CAN bus.

Screenshot: TODO

# Usage

    $ python explorer.py

Or for some more low level utilities, such as candump and cansend:

    $ python cansend.py vcan0 88 deadbeef

    $ python candump.py vcan0

# Testing

Setup a virtual can bus:

    $ sudo ip link add dev vcan0 type vcan
    $ sudo ip link set up vcan0

