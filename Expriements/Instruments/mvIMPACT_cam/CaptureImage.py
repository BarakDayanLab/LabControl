from __future__ import print_function
import os
import platform
import string
import sys
# import all the stuff from mvIMPACT Acquire into the current scope
from mvIMPACT import acquire
# import all the mvIMPACT Acquire related helper function such as 'conditionalSetProperty' into the current scope
# If you want to use this module in your code feel free to do so but make sure the 'Common' folder resides in a sub-folder of your project then
from mvIMPACT.Common import exampleHelper

# For systems with NO mvDisplay library support
import ctypes
from PIL import Image
import numpy
import os
import glob


# from PyQt5.QtGui import QPixmap, QImage

devMgr = acquire.DeviceManager()
pDev = exampleHelper.getDeviceFromUserInput(devMgr)
if pDev == None:
    exampleHelper.requestENTERFromUser()
    sys.exit(-1)
pDev.open()

print("Please enter the number of buffers to capture followed by [ENTER]: ", end='')
framesToCapture = exampleHelper.getNumberFromUser()
if framesToCapture < 1:
    print("Invalid input! Please capture at least one image")
    sys.exit(-1)

# The mvDisplay library is only available on Windows systems for now
isDisplayModuleAvailable = platform.system() == "Windows"
if isDisplayModuleAvailable:
    display = acquire.ImageDisplayWindow("A window created from Python")
else:
    print(
        "The mvIMPACT Acquire display library is not available on this('" + platform.system() + "') system. Consider using the PIL(Python Image Library) and numpy(Numerical Python) packages instead. Have a look at the source code of this application to get an idea how.")

# Matrix Vision Display the Image Fit to Window
display.GetImageDisplay().SetDisplayMode(0)

fi = acquire.FunctionInterface(pDev)
statistics = acquire.Statistics(pDev)
id = acquire.ImageDestination(pDev)
id.pixelFormat.writeS("BGR888Packed")

print("CameraFamily:", pDev.family.readS())
print("InterfaceLayout:", pDev.interfaceLayout.readS())

# =======================================================================
# Below statement is valid for All Devices (ImageProcessing)
# =======================================================================

# Define the AcquisitionControl Parameters
imgProc = acquire.ImageProcessing(pDev)

# Set Saturation
# K is the saturation factor
# K > 1 increases saturation
# K = 1 means no change
# 0 < K < 1 decreases saturation
# K = 0 produces B&W
# K < 0 inverts color
K = 0.500
imgProc.colorTwistEnable.write(True);
imgProc.setSaturation(K)  # Valid Values 0.000 to 1.000

# =======================================================================

# =======================================================================
# Below statement is valid only for mvVirtualDevice(Virtual) Cameras only
# =======================================================================
if pDev.family.readS() == "mvVirtualDevice":
    # Define the Camera Settings
    camSettingsVirtualDevice = acquire.CameraSettingsVirtualDevice(pDev)

    # Change the ROI to capture image
    camSettingsVirtualDevice.aoiStartX.write(0)
    camSettingsVirtualDevice.aoiStartY.write(0)
    camSettingsVirtualDevice.aoiWidth.write(1280)
    camSettingsVirtualDevice.aoiHeight.write(1024)

    # Test image
    camSettingsVirtualDevice.testMode.writeS("MovingRGBx888PackedImage")
# =======================================================================

# =======================================================================
# Below statement is valid only for mvBlueFOX(USB2.0) Cameras only
# =======================================================================
if pDev.family.readS() == "mvBlueFOX":
    # Define the Camera Settings
    camSettingsBlueFOX = acquire.CameraSettingsBlueFOX(pDev)

    # Change the ROI to capture image
    # camSettingsBlueFOX.aoiStartX.write(0)
    # camSettingsBlueFOX.aoiStartY.write(0)
    # camSettingsBlueFOX.aoiWidth.write(100)
    # camSettingsBlueFOX.aoiHeight.write(100)

    # Write the Exposure Settings to the Camera
    camSettingsBlueFOX.expose_us.write(1000)

    # Read the Exposure Settings in the Camera
    print("Exposure:", camSettingsBlueFOX.expose_us.read())

    # Write the Gain Settings to the Camera
    camSettingsBlueFOX.gain_dB.write(17.5)

    # Read the Gain Settings in the Camera
    print("Gain:", camSettingsBlueFOX.gain_dB.read())
# =======================================================================

# =======================================================================
# Below statement is valid only for mvBlueCOUGAR or mvBlueFOX3(GenICam) Cameras only
# =======================================================================
if pDev.family.readS() == "mvBlueFOX3" or pDev.family.readS() == "mvBlueCOUGAR":
    # Define the AcquisitionControl Parameters
    genIcamAcqCtrl = acquire.AcquisitionControl(pDev)

    # Write the Exposure Settings to the Camera
    genIcamAcqCtrl.exposureTime.write(10000)

    # Read the Exposure Settings in the Camera
    print("Exposure:", genIcamAcqCtrl.exposureTime.read())

    # Define the AnalogControl Parameters
    genIcamAlgCtrl = acquire.AnalogControl(pDev)

    # Write the Gain Settings to the Camera
    genIcamAlgCtrl.gain.write(25.000)

    # Read the Gain Settings in the Camera
    print("Gain:", genIcamAlgCtrl.gain.read())

    # Write the Black Level Settings to the Camera
    genIcamAlgCtrl.blackLevelSelector.writeS("All")
    genIcamAlgCtrl.blackLevel.write(10.00)

    # Read the Black Level Settings in the Camera
    print("BlackLevel:", genIcamAlgCtrl.blackLevel.read())

    # Write the Balance Ratio Settings to the Camera
    # genIcamAlgCtrl.balanceRatioSelector.writeS("Red")
    #genIcamAlgCtrl.balanceRatio.write(1.963)  # Valid Values - 0.063 to 16.000
    #genIcamAlgCtrl.balanceRatioSelector.writeS("Blue")
    #genIcamAlgCtrl.balanceRatio.write(1.723)  # Valid Values - 0.063 to 16.000

    # Read the Balance Ratio Settings in the Camera
    #genIcamAlgCtrl.balanceRatioSelector.writeS("Red")
    #print("BalanceRatio(Red):", genIcamAlgCtrl.balanceRatio.read())
    #genIcamAlgCtrl.balanceRatioSelector.writeS("Blue")
    #print("BalanceRatio(Blue):", genIcamAlgCtrl.balanceRatio.read())

    # Set the Trigger Mode Option for Camera
    genIcamAcqCtrl.triggerSelector.writeS("FrameStart")
    genIcamAcqCtrl.triggerMode.writeS("On")  # On; Off
    genIcamAcqCtrl.triggerSource.writeS("Line4")  # Line4; Software
    if genIcamAcqCtrl.triggerSource.readS() == "Line4":
         genIcamAcqCtrl.triggerActivation.writeS("RisingEdge")
    genIcamAcqCtrl.triggerDelay.write(0.000)

# =======================================================================

while fi.imageRequestSingle() == acquire.DMR_NO_ERROR:
    print("Buffer queued")
pPreviousRequest = None


#delete all files in the images directory
files = glob.glob('./Images/*')
for f in files:
    os.remove(f)

exampleHelper.manuallyStartAcquisitionIfNeeded(pDev, fi)
for i in range(framesToCapture):
    requestNr = fi.imageRequestWaitFor(10000)
    if fi.isRequestNrValid(requestNr):
        pRequest = fi.getRequest(requestNr)
        if pRequest.isOK:

            # Display Statistics
            if i % 10 == 0:
                print("Info from " + pDev.serial.read() +
                      ": " + statistics.framesPerSecond.name() + ": " + statistics.framesPerSecond.readS() +
                      ", " + statistics.errorCount.name() + ": " + statistics.errorCount.readS() +
                      ", " + "Width" + ": " + pRequest.imageWidth.readS() +
                      ", " + "Height" + ": " + pRequest.imageHeight.readS() +
                      ", " + "Channels" + ": " + pRequest.imageChannelCount.readS())

            # Save image to the PC - pRequest
            pRequest.getImageBufferDesc().save("subtractedImg.jpg", 0)

            # Display Image
            if isDisplayModuleAvailable:
                display.GetImageDisplay().SetImage(pRequest)
                display.GetImageDisplay().Update()

            # For systems with NO mvDisplay library support
            cbuf = (ctypes.c_char * pRequest.imageSize.read()).from_address(int(pRequest.imageData.read()))
            channelType = numpy.uint16 if pRequest.imageChannelBitDepth.read() > 8 else numpy.uint8
            arr = numpy.fromstring(cbuf, dtype=channelType)

            # Get the PIL Image - Mono8
            if pRequest.imagePixelFormat.readS() == "Mono8":
                arr.shape = (pRequest.imageHeight.read(), pRequest.imageWidth.read())
                img = Image.fromarray(arr)

            # Get the PIL Image - BGR888Packed
            if pRequest.imagePixelFormat.readS() == "BGR888Packed":
                arr.shape = (pRequest.imageHeight.read(), pRequest.imageWidth.read(), 3)
                img = Image.fromarray(arr, 'RGB')

                # QtImage
                # Qtimg = QImage(( ctypes.c_char * pRequest.imageSize.read()).from_address(int(pRequest.imageData.read())),
                # pRequest.imageWidth.read(), pRequest.imageHeight.read(), pRequest.imageLinePitch.read(), QImage.Format_RGB888)
                # qt_pixmap=QtGui.QPixmap(Qtimg)
                # qt_image=QtGui.QImage((qt_pixmap))

            # Get the PIL Image - RGBx888Packed
            if pRequest.imagePixelFormat.readS() == "RGBx888Packed":
                arr.shape = (pRequest.imageHeight.read(), pRequest.imageWidth.read(), 4)
                img = Image.fromarray(arr, 'RGBX')

            # Save image to the PC - PIL
            Img_Name = 'C:\Pycharm\Expriements\Instruments\mvIMPACT_cam\Images\MVcam_photo_'+str(i)+'.jpg'
            img = img.save(Img_Name, 'JPEG')


        if pPreviousRequest != None:
            pPreviousRequest.unlock()

        pPreviousRequest = pRequest

        fi.imageRequestSingle()
    else:
        # Please note that slow systems or interface technologies in combination with high resolution sensors
        # might need more time to transmit an image than the timeout value which has been passed to imageRequestWaitFor().
        # If this is the case simply wait multiple times OR increase the timeout(not recommended as usually not necessary
        # and potentially makes the capture thread less responsive) and rebuild this application.
        # Once the device is configured for triggered image acquisition and the timeout elapsed before
        # the device has been triggered this might happen as well.
        # The return code would be -2119(DEV_WAIT_FOR_REQUEST_FAILED) in that case, the documentation will provide
        # additional information under TDMR_ERROR in the interface reference.
        # If waiting with an infinite timeout(-1) it will be necessary to call 'imageRequestReset' from another thread
        # to force 'imageRequestWaitFor' to return when no data is coming from the device/can be captured.
        print("imageRequestWaitFor failed (" + str(
            requestNr) + ", " + acquire.ImpactAcquireException.getErrorCodeAsString(requestNr) + ")")
exampleHelper.manuallyStopAcquisitionIfNeeded(pDev, fi)
exampleHelper.requestENTERFromUser()