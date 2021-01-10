# code for move polarizer to another orientation
# Configuration Serial number paddle - which paddle 1/2/3 position - from 0 to 170 18.08.20 - assaf s. - converting
# the script to a function, adding a possibility to leave the paddles orientation as initial state

from ctypes import (
    c_int,
    c_char_p,
)
from time import sleep

from thorlabs_kinesis import polarizer as mpc


def set_one_polarizer(serial_no, paddle, position, milliseconds):
    # moving one paddle to a specific position
    mpc.MPC_StartPolling(serial_no, milliseconds)
    mpc.MPC_ClearMessageQueue(serial_no)
    sleep(0.2)
    if position in range(0, 171):
        mpc.MPC_MoveToPosition(serial_no, paddle, position)
        sleep(0.2)
        pos = int(mpc.MPC_GetPosition(serial_no, paddle))
        sleep(0.2)
        while pos not in range(position - 1, position + 2):
            sleep(0.2)
            pos = int(mpc.MPC_GetPosition(serial_no, paddle))
    else:
        raise NameError('polarizer input angle must be between 0 and 170 ')
    actual_position = pos
    mpc.MPC_StopPolling(serial_no)
    return actual_position


def set3polarizers(paddle1_pos_input, paddle2_pos_input, paddle3_pos_input, serial_type):
    if __name__ == "__main__":
        # INPUT:
        # paddle1_pos_input - the desirable paddle 1 orientation. it must be a number between 1 and 170.
        # paddle2_pos_input - the desirable paddle 2 orientation. it must be a number between 1 and 170.
        # paddle3_pos_input - the desirable paddle 3 orientation. it must be a number between 1 and 170.

        # serial_type - is an integer representing the real serial number.
        # 1 - 38137764
        # 2 - 38133904
        # 3 -
        # possible ERRORS:
        # FT_OK = 0x00, /// <OK - no error.
        # FT_InvalidHandle = 0x01, ///<Invalid handle.
        # FT_DeviceNotFound = 0x02, ///<Device not found.
        # FT_DeviceNotOpened = 0x03, ///<Device not opened.
        # FT_IOError = 0x04, ///<I/O error.
        # FT_InsufficientResources = 0x05, ///<Insufficient resources.
        # FT_InvalidParameter = 0x06, ///<Invalid parameter.
        # FT_DeviceNotPresent = 0x07, ///<Device not present.
        # FT_IncorrectDevice = 0x08 ///<Incorrect device.
        # device do not response - 33

        # PARAMETERS #
        # paddle num
        paddle1 = 1
        paddle2 = 2
        paddle3 = 3
        delay = c_int(100)

        # the serial number from the kinesis interface
        if serial_type == 1:
            serial_no = c_char_p(bytes("38137764", "utf-8"))
        elif serial_type == 2:
            serial_no = c_char_p(bytes("38133904", "utf-8"))
        else:
            raise NameError('serial type is incorrect. The serial type must match the serial number as defined in the '
                            'code ')
        if mpc.TLI_BuildDeviceList() == 0:
            err = mpc.MPC_Open(serial_no)
            sleep(0.2)
            if err == 0:
                # The polling loop requests regular status requests to the motor to
                # ensure the program keeps track of the device.
                paddle1_current_pos = set_one_polarizer(serial_no, paddle1, paddle1_pos_input, delay)
                paddle2_current_pos = set_one_polarizer(serial_no, paddle2, paddle2_pos_input, delay)
                paddle3_current_pos = set_one_polarizer(serial_no, paddle3, paddle3_pos_input, delay)
                mpc.MPC_Close(serial_no)
                return paddle1_current_pos, paddle2_current_pos, paddle3_current_pos
            else:
                mpc.MPC_Close(serial_no)
                raise NameError(
                    f"Can't open kinesis polarizer, make sure the Serial Number is OK and the device connection. You can check both on the kinesis program. Error number: {err}")


# [paddle1_pos, paddle2_pos, paddle3_pos] = set3polarizers(30, 20, 40, 1)
# print(paddle1_pos, paddle2_pos, paddle3_pos)
