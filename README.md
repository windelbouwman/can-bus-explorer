
This is a set of utilities to inspect and debug the CAN bus. Via a graphical user
interface you can gain insight into what is happening.

Screenshot: TODO

# Usage

    $ python explorer.py socketcan:vcan0

Or for some more low level utilities, such as candump and cansend:

    $ python cansend.py socketcan:vcan0 88 deadbeef

    $ python candump.py socketcan:vcan0

For the purpose of pure bus traffic, a sine wave generator script was made.
Caution: this creates pretty random bus traffic!

    $ python sinewave.py --freq 10 socketcan:vcan0

# Testing

Setup a virtual can bus:

    $ sudo ip link add dev vcan0 type vcan
    $ sudo ip link set up vcan0

