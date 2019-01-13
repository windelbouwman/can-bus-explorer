""" Socket can error handling defines / routines.

See also: /usr/include/linux/can/error.h

"""


def message_to_errors(message):
    """ Given a CAN message, create the proper errors from it.
    """
    if message.id & socket.CAN_ERR_FLAG == 0:
        raise ValueError("Not an error CAN message")

    if message.id & CAN_ERR_ACK:
        errors.append(AckError())

    if message.id & CAN_ERR_BUSOFF:
        errors.append(BusOffError())

    if message.id & CAN_ERR_BUSERROR:
        errors.append(BusError())

    return errors


# Exception hierarchy:
class CanException(Exception):
    pass


class AckError(CanException):
    pass


class BusOffError(CanException):
    pass


class BusError(CanException):
    pass


CAN_ERR_TX_TIMEOUT = 0x1
CAN_ERR_LOSTARB = 0x2
CAN_ERR_CTRL = 0x4
CAN_ERR_PROT = 0x8
CAN_ERR_TRX = 0x10
CAN_ERR_ACK = 0x20
CAN_ERR_BUSOFF = 0x40
CAN_ERR_BUSERROR = 0x80
