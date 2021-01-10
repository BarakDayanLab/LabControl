"Bindings for NI-IMAQ"


from ctypes import (
    cdll,
    c_uint32,
    c_int32,
    c_int8,
    POINTER,
    c_void_p,
    c_char_p
)
from IMAQ_NI._utils import (
    c_word,
    c_dword,
    bind
)



lib = cdll.LoadLibrary("C:\Windows\System32\imaq.dll")


#  INTERFACE_ID
INTERFACE_ID = c_uint32
SESSION_ID = c_uint32

IMAQ_Image_Interface_Reset = bind(lib,"imgInterfaceReset",[c_uint32],c_int32)
IMAQ_Image_Show_Error = bind(lib,"imgShowError",[c_int32, c_char_p],c_int32)


IMAQ_Interface_Query_Names = bind(lib,"imgInterfaceQueryNames",[c_uint32, c_char_p],c_int32)
IMAQ_Interface_Open = bind(lib, "imgInterfaceOpen", [c_char_p, POINTER(c_uint32)], c_int32)
IMAQ_Session_Open = bind(lib, "imgSessionOpen", [INTERFACE_ID, POINTER(SESSION_ID)], c_int32)
IMAQ_Snap = bind(lib, "imgSnap", [SESSION_ID, POINTER(c_void_p)], c_int32)
IMAQ_Close = bind(lib, "imgClose", [c_uint32, c_uint32], c_int32)
