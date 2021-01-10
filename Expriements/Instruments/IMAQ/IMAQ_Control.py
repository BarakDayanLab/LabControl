# This script controls the frame grabber (IMAQ)
from ctypes import (
    c_int8,
    c_uint32,
    c_void_p,
    byref,
    c_char_p,
    pointer,
    string_at,
    create_string_buffer
)

from IMAQ_NI import IMAQCppBindings as imq
import nivision

# Parameters
x = c_char_p('000000000000'.encode('utf-8'))
err = c_char_p('00000000000000000'.encode('utf-8'))

a = imq.IMAQ_Interface_Query_Names(c_uint32(0),x)

INTERFACE_NAME = c_char_p('img0.iid'.encode('utf-8'))# c_int8(10)  # the interface name
IFID = c_uint32(15)  # the interface ID
SID = c_uint32(1)  # the session ID
IMAQ_BUFFER = c_void_p(17) # 17 is just any integer
#MY_IMAQ_BUFFER = IMAQ_BUFFER(None)

# Open an interface and a session

response = imq.IMAQ_Interface_Open(x, byref(IFID))
#imq.IMAQ_Image_Show_Error(response, err)
response = imq.IMAQ_Session_Open(IFID, byref(SID))


#print("b: %d, %s"%(b, string_at(err)))
#b = imq.IMAQ_Img_Create_Buffer(SID, c_uint32(0), c_uint32(320000), byref(IMAQ_BUFFER))
#imq.IMAQ_Image_Show_Error(b,err)
# TODO WARNING!!@
img1 = nivision.imaqEasyAcquire(INTERFACE_NAME)
img = nivision.imaqCreateImage(nivision.IMAQ_IMAGE_RGB) # This actually returns Image*
c = nivision.imaqSetImageSize(img,100,100)

x = nivision.imaqSnap(SID, img, nivision.IMAQ_NO_RECT)
nivision.imaqDisplayImage(x,0,True)

# snap a picture : ImaqBuffer is NULL, memory will be allocated by
# NI-IMAQ
print(imq.IMAQ_Snap(SID, byref(MY_IMAQ_BUFFER)))

# Close the interface and the session
if SID:
    imq.IMAQ_Close(SID, True)
if IFID:
    imq.IMAQ_Close(IFID, True)
