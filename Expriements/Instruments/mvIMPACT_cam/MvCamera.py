'''
Current bugs:
    when trigger is not sent the software can't communicate with the camera anymore and the driver must be re-installed.
'''

from __future__ import print_function
import sys

# import all the stuff from mvIMPACT Acquire into the current scope
from mvIMPACT import acquire

# import all the mvIMPACT Acquire related helper function such as 'conditionalSetProperty' into the current scope
# If you want to use this module in your code feel free to do so but make sure the 'Common' folder resides in a sub-folder of your project then
from mvIMPACT.Common import exampleHelper
# from PyQt5.QtGui import QPixmap, QImage

# For systems with NO mvDisplay library support
import ctypes
from PIL import Image
import numpy
import os
import glob
from datetime import date, datetime
import cv2
from os.path import isfile, join
import numpy as np
import matplotlib.pyplot as mtl
import pylab as plt
import scipy.optimize as opt


class MvCamera:
    '''
    This module controls the matrix vision camera. It handles taking pictures, subtracting background, create a movie, fit to gaussian and measure
    temprature.
    '''
    # Input:
    #   DisplayImages   - a boolean parameter that defines if the image should be displayed (might be problematic on pycharm, try on powershell/other platform)
    #   SaveImages      - a boolean parameter that defines if the image should be saved
    # def __init__(self, DisplayImages = True, SaveImages = True):
    #     # aquire control on the device from the device manager with the "aquire" function
    #     # Display&save setting
    #     self.DisplaySetting()
    #     self.DisplayImages = DisplayImages
    #     self.SaveImages = SaveImages

    # =======================================================================
    # Capture Image -
    # Input:
    #   TimeOut_ms      - time in ms for which the function waits for image on the camera.  If timeout_ms is '-1', the function's timeout interval never elapses.
    #   NumberOfFrames  - defines the number of frames the capture image function grabs.
    #   DeviceNr - device number in the MvDeviceConfigure (for managing multipule devices)
    def __init__(self, DeviceNr=0):
        '''

        :param DeviceNr:
                the device number connected. For managing multiple device. the number can be found at MvConfig.exe
        '''
        #acquire connection to the camera - must be deleted at the end of use , if not the access to the camera is denied
        self.devMgr = acquire.DeviceManager()
        self.pDev = self.devMgr.getDevice(DeviceNr)
        if self.pDev == None:
            exampleHelper.requestENTERFromUser()
            sys.exit(-1)
        self.pDev.open()

        #pixel formatting
        id = acquire.ImageDestination(self.pDev)
        id.pixelFormat.writeS("BGR888Packed")

        print("CameraFamily:", self.pDev.family.readS())
        print("InterfaceLayout:", self.pDev.interfaceLayout.readS())

        # attribute that defines the Image processing, AcquisitionControl and analog control Parameters
        self.imgProc = acquire.ImageProcessing(self.pDev)
        self.genIcamAcqCtrl = acquire.AcquisitionControl(self.pDev)
        self.genIcamAlgCtrl = acquire.AnalogControl(self.pDev)

        self.SetPictureParameters(K=0.5, expusure_time=20000,Gain=25.000, black_level=10.00)
        self.set_trigger()
        # =======================================================================

    def capture_image(self, TimeOut_ms=10000, NumberOfFrames=1):
        """ this function grabs an image from the mv camera, with options to display it and save it into a png in given directory

        :param TimeOut_ms: timeout of the request of image. After it, if the camera didn't return image the software raise error
        :param NumberOfFrames: number of frames to capture
        :return: img - array of array of images. can be saved with save img. the img format is BGR888Packed.
        """
        # open function interface to the device which enabales acquisition of images
        self.fi = acquire.FunctionInterface(self.pDev)
        #acquire statistics for the device
        self.statistics = acquire.Statistics(self.pDev)

        if NumberOfFrames < 1:
            print("Invalid input! Please capture at least one image")
            sys.exit(-1)

        # the driver acquires images from the camera into buffer.
        while self.fi.imageRequestSingle() == acquire.DMR_NO_ERROR:
            # print("Buffer queued")
            pass
        pPreviousRequest = None

        #start acquisition
        exampleHelper.manuallyStartAcquisitionIfNeeded(self.pDev, self.fi)
        img = [None] * NumberOfFrames
        for i in range(NumberOfFrames):

            requestNr = self.fi.imageRequestWaitFor(TimeOut_ms)

            if self.fi.isRequestNrValid(requestNr):
                pRequest = self.fi.getRequest(requestNr)
                if pRequest.isOK:
                    # Display Statistics
                    if i % 10 == 0:
                        self.save_statistics(pRequest)

                    # For systems with NO mvDisplay library support
                    cbuf = (ctypes.c_char * pRequest.imageSize.read()).from_address(int(pRequest.imageData.read()))
                    channelType = numpy.uint16 if pRequest.imageChannelBitDepth.read() > 8 else numpy.uint8
                    arr = numpy.fromstring(cbuf, dtype=channelType)

                    # Get the PIL Image - BGR888Packed
                    if pRequest.imagePixelFormat.readS() == "BGR888Packed":
                        arr.shape = (pRequest.imageHeight.read(), pRequest.imageWidth.read(), 3)
                        img[i] = Image.fromarray(arr, 'RGB')

                if pPreviousRequest != None:
                    pPreviousRequest.unlock()

                pPreviousRequest = -pRequest

                self.fi.imageRequestSingle()
            else:
                '''Please note that slow systems or interface technologies in combination with high resolution sensors
                might need more time to transmit an image than the timeout value which has been passed to imageRequestWaitFor().
                If this is the case simply wait multiple times OR increase the timeout(not recommended as usually not necessary
                and potentially makes the capture thread less responsive) and rebuild this application.
                Once the device is configured for triggered image acquisition and the timeout elapsed before
                the device has been triggered this might happen as well.
                The return code would be -2119(DEV_WAIT_FOR_REQUEST_FAILED) in that case, the documentation will provide
                additional information under TDMR_ERROR in the interface reference.
                If waiting with an infinite timeout(-1) it will be necessary to call 'imageRequestReset' from another thread
                to force 'imageRequestWaitFor' to return when no data is coming from the device/can be captured.
                '''
                print("imageRequestWaitFor failed (" + str(
                    requestNr) + ", " + acquire.ImpactAcquireException.getErrorCodeAsString(requestNr) + ")")
        exampleHelper.manuallyStopAcquisitionIfNeeded(self.pDev, self.fi)
        rc = self.fi.requestCount()
        for i in range(rc):
            self.fi.imageRequestUnlock(i)
        return img

    def clear_images_folder(self, pathIn = '.\Images'):
        """delete all files in the images directory
        :param pathIn:  the directory to be deleted
        :return:
        """
        files = glob.glob(pathIn+'\*.png')
        for f in files:
            os.remove(f)

    #saves the image
    def save_image(self,img,fname_t, background=False, format='.png'):
        """Save image to the PC in a specific format. the name includes the date and time

        :param img:the image array
        :param fname_t:the time image was taken in time flow of the expriment
        :param background: indicates if it's a backround image to save under backround name
        :return:
        """
        #
        now = datetime.now()
        today = date.today()
        Img_Name = '.\\Images\\' + today.strftime("%b_%d_%Y_") + now.strftime(
            "%H_%M_%S")
        if not background:
            Img_Name +=  't=' + fname_t + format
        else :
            Img_Name += "background" + format
        if format == '.png':
            img.save(Img_Name, 'PNG')
        elif format == '.jpg':
            img.save(Img_Name, 'JPEG')

    # creates a movie at pathOut from the picture at PathIn in fps - frames per second
    def FramesToMovie(self,fps=1):
        """
        creates a movie at pathOut from the picture at PathIn
        :param fps: frames per second
        :return:
        """
        pathIn = '.\\Images'
        pathOut = '.\\Video\\video.avi'
        FramesPerSecond = fps
        frame_array = []
        files = [f for f in os.listdir(pathIn) if isfile(join(pathIn, f))]
        # for sorting the file names properly
        files.sort(key=lambda x: x[5:-4])
        for i in range(len(files)):
            filename = pathIn + '/' + files[i]
            # reading each files
            img = cv2.imread(filename)
            height, width, layers = img.shape
            size = (width, height)

            # inserting the frames into an image array
            frame_array.append(img)
        out = cv2.VideoWriter(pathOut, cv2.VideoWriter_fourcc(*'DIVX'), FramesPerSecond, size)
        for i in range(len(frame_array)):
            # writing to a image array
            out.write(frame_array[i])
        out.release()
        os.startfile('.\\Video\\video.avi')

    #subtract all the images from background and saves them to SubtractedImages folder
    def subtract_background(self, Background_path='.\\Images\\Background', Images_path='.\\Images\\OriginalImages', Subtractpath='.\\Images\\SubtractedImages'):
        """
        subtraction of background from image
        :param Images_path: the path of images to be subtracted
        :param Background_path: the path of background
        :param Subtractpath: the path of subtracted image to be saved
        :return:
        """
        BckgrndImg = cv2.imread(Background_path)
        files = [f for f in os.listdir(Images_path) if isfile(join(Images_path, f))]
        # for sorting the file names properly
        files.sort(key=lambda x: x[5:-4])
        for i in range(len(files)):
            filename = Images_path + '/' + files[i]
            # reading each files
            orig_img = cv2.imread(filename)
            subtracted_img = cv2.absdiff(BckgrndImg, orig_img)
            Img_Name =Subtractpath+'SubtractedImage'+str(i)+'.png'
            cv2.imwrite(Img_Name, subtracted_img)

    #fit a gaussian to subtracted images
    # INPUT:
    #   Y_PIXEL_LEN - number of vertical pixels
    #   X_PIXEL_LEN - number of horizontal pixels
    #   the name of the file for fit with png termination
    #   CROP_IMG_SIZE - the size of image in each dimension after cropping is 2*CROP_IMG_SIZE
    def gaussian_fit(self, file_for_fit_path,CROP_IMG_SIZE =180 ,PLOT_IMG=False, PLOT_SLICE =False):
        """

        :param file_for_fit_path: the full path of the image for fitting
        :param CROP_IMG_SIZE: the size of image in each dimension after cropping is 2*CROP_IMG_SIZE
        :param PLOT_IMG:
        :param PLOT_SLICE:
        :return:
        """
        ImgToFit = cv2.imread(file_for_fit_path, 0)
        img_max_index = [np.argmax(np.sum(ImgToFit, axis=1)), np.argmax(np.sum(ImgToFit, axis=0))]
        # Parameters
        X_UPPER_BOUND = int(img_max_index[0] + CROP_IMG_SIZE)
        X_LOWER_BOUND = int(img_max_index[0] - CROP_IMG_SIZE)
        EFFECTIVE_X_PIXEL_LEN = X_UPPER_BOUND - X_LOWER_BOUND

        Y_UPPER_BOUND = int(img_max_index[1] + CROP_IMG_SIZE)
        Y_LOWER_BOUND = int(img_max_index[1] - CROP_IMG_SIZE)
        EFFECTIVE_Y_PIXEL_LEN = Y_UPPER_BOUND - Y_LOWER_BOUND

        # Create x and y indices
        x = np.linspace(0, EFFECTIVE_Y_PIXEL_LEN - 1, EFFECTIVE_Y_PIXEL_LEN)
        y = np.linspace(0, EFFECTIVE_X_PIXEL_LEN - 1, EFFECTIVE_X_PIXEL_LEN)
        x, y = np.meshgrid(x, y)
        # crop an effective image
        EffectiveImg = ImgToFit[X_LOWER_BOUND:X_UPPER_BOUND, Y_LOWER_BOUND:Y_UPPER_BOUND]
        data_noisy = EffectiveImg.ravel()

        # fit the data
        img_max_index = [np.argmax(np.sum(EffectiveImg, axis=1)), np.argmax(np.sum(EffectiveImg, axis=0))]
        initial_guess = (ImgToFit[img_max_index], img_max_index[0], img_max_index[1], EFFECTIVE_X_PIXEL_LEN, EFFECTIVE_Y_PIXEL_LEN, 0, 10)
        popt, pcov = opt.curve_fit(self.twoD_Gaussian, (x, y), data_noisy, p0=initial_guess)

        # plot the results
        data_fitted = self.twoD_Gaussian((x, y), *popt)
        sigma = [popt[3], popt[4]]
        if PLOT_IMG:
            fig, ax = plt.subplots(1, 1)

            plt.text(0.88, 0.95, '\u03C3_x =' + '%.2f' % sigma[0] + '\n' + '\u03C3_y = ' + '%.2f' % sigma[1], color='white',
                     fontsize=16, style='italic', weight='bold', horizontalalignment='center', verticalalignment='center',
                     transform=ax.transAxes, bbox=dict(facecolor='gray', alpha=0.5))
            ax.imshow(data_noisy.reshape(EFFECTIVE_X_PIXEL_LEN, EFFECTIVE_Y_PIXEL_LEN), cmap=plt.cm.jet, origin='bottom',
                      extent=(x.min(), x.max(), y.min(), y.max()))
            ax.contour(x, y, data_fitted.reshape(EFFECTIVE_X_PIXEL_LEN, EFFECTIVE_Y_PIXEL_LEN), 8, colors='w')

            plt.show()

        if PLOT_SLICE:
            # plot slice
            mtl.figure()
            data_noisy_mat = data_noisy.reshape(EFFECTIVE_X_PIXEL_LEN, EFFECTIVE_Y_PIXEL_LEN)
            Slice = data_noisy_mat[int(EFFECTIVE_X_PIXEL_LEN / 2) - 10]
            mtl.plot(Slice)
            mtl.plot(data_fitted.reshape(EFFECTIVE_X_PIXEL_LEN, EFFECTIVE_Y_PIXEL_LEN)[int(EFFECTIVE_X_PIXEL_LEN / 2) - 10])
            plt.show()
        return popt

    # define model function and pass independant variables x and y as a list
    def twoD_gaussian(self, x_y, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
        x, y = x_y
        xo = float(xo)
        yo = float(yo)
        a = (np.cos(theta) ** 2) / (2 * sigma_x ** 2) + (np.sin(theta) ** 2) / (2 * sigma_y ** 2)
        b = -(np.sin(2 * theta)) / (4 * sigma_x ** 2) + (np.sin(2 * theta)) / (4 * sigma_y ** 2)
        c = (np.sin(theta) ** 2) / (2 * sigma_x ** 2) + (np.cos(theta) ** 2) / (2 * sigma_y ** 2)
        g = offset + amplitude * np.exp(- (a * ((x - xo) ** 2) + 2 * b * (x - xo) * (y - yo)
                                           + c * ((y - yo) ** 2)))
        return g.ravel()

    #set parameters
    def set_picture_parameters(self, K=0.5, expusure_time=20000, Gain=25.000, black_level=10.00):
        '''
        :param K: Set Saturation
                    K is the saturation factor
                    K > 1 increases saturation
                    K = 1 means no change
                    0 < K < 1 decreases saturation
                    K = 0 produces B&W
                    K < 0 inverts color
        :param expusure_time:
                Sets the exposure time (in microseconds)
        :param Gain:
                sets the gain of the camera
        :param black_level:
                sets the black level of the camera
        :return:
        '''
        self.set_saturation(K)
        self.set_exposure(expusure_time)
        self.set_gain(Gain)
        self.set_balck_level(black_level)
        self.setTrigger

    def set_saturation(self,K):
        self.imgProc.colorTwistEnable.write(True)
        self.imgProc.setSaturation(K)

    def set_exposure(self,expusure_time):
        self.genIcamAcqCtrl.exposureTime.write(expusure_time)
        print("Exposure:", self.genIcamAcqCtrl.exposureTime.read())

    def set_gain(self,Gain):
        self.genIcamAlgCtrl.gain.write(Gain)
        print("Gain:", self.genIcamAlgCtrl.gain.read())

    def set_balck_level(self, black_level):
        # Write the Black Level Settings to the Camera
        self.genIcamAlgCtrl.blackLevelSelector.writeS("All")
        self.genIcamAlgCtrl.blackLevel.write(10.00)
        # Read the Black Level Settings in the Camera
        print("BlackLevel:", self.genIcamAlgCtrl.blackLevel.read())

    def set_trigger(self,trigger_mode="On", trigger_source="Line4", trigger_activation="RisingEdge", trigger_delay=0.000):
        # Set the Trigger Mode Option for Camera
        self.genIcamAcqCtrl.triggerSelector.writeS("FrameStart")
        self.genIcamAcqCtrl.triggerMode.writeS(trigger_mode)  # On; Off
        self.genIcamAcqCtrl.triggerSource.writeS(trigger_source)  # Line4; Software
        if self.genIcamAcqCtrl.triggerSource.readS() == "Line4":
            self.genIcamAcqCtrl.triggerActivation.writeS(trigger_activation)
        self.genIcamAcqCtrl.triggerDelay.write(trigger_delay)

    def save_statistics(self, pRequest):
        print("Info from " + self.pDev.serial.read() +
              ": " + self.statistics.framesPerSecond.name() + ": " + self.statistics.framesPerSecond.readS() +
              ", " + self.statistics.errorCount.name() + ": " + self.statistics.errorCount.readS() +
              ", " + "Width" + ": " + pRequest.imageWidth.readS() +
              ", " + "Height" + ": " + pRequest.imageHeight.readS() +
              ", " + "Channels" + ": " + pRequest.imageChannelCount.readS())
# =======================================================================


if __name__ == '__main__':
    cam=MvCamera()
    while True:
        cam.CaptureImage()
    del cam
    cam.FramesToMovie()



# =================================
#   other camera parameters
# =================================
# Write the Balance Ratio Settings to the Camera
# genIcamAlgCtrl.balanceRatioSelector.writeS("Red")
# genIcamAlgCtrl.balanceRatio.write(1.963)  # Valid Values - 0.063 to 16.000
# genIcamAlgCtrl.balanceRatioSelector.writeS("Blue")
# genIcamAlgCtrl.balanceRatio.write(1.723)  # Valid Values - 0.063 to 16.000

# Read the Balance Ratio Settings in the Camera
# genIcamAlgCtrl.balanceRatioSelector.writeS("Red")
# print("BalanceRatio(Red):", genIcamAlgCtrl.balanceRatio.read())
# genIcamAlgCtrl.balanceRatioSelector.writeS("Blue")
# print("BalanceRatio(Blue):", genIcamAlgCtrl.balanceRatio.read())
