
This is a set of utilities to inspect and debug the CAN bus. Via a graphical user
interface you can gain insight into what is happening.

Screenshot: TODO

# Usage

    $ python explorer.py vcan0

Or for some more low level utilities, such as candump and cansend:

    $ python cansend.py vcan0 88 deadbeef

    $ python candump.py vcan0

# Testing

Setup a virtual can bus:

    $ sudo ip link add dev vcan0 type vcan
    $ sudo ip link set up vcan0

