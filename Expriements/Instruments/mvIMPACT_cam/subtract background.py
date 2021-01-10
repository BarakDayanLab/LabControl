import cv2
import pylab
import os

img1 = cv2.imread(
    'Expriements/Instruments/mvIMPACT_cam/Images/OriginalImages/MVcam_photo_Dec_10_2020_13_12_08t=10.00.png')
img2 = cv2.imread(
    'Expriements/Instruments/mvIMPACT_cam/Images/OriginalImages/MVcam_photo_Dec_10_2020_13_14_32_background.png')
image3 = cv2.absdiff(img1, img2)

# Save image to the PC - cv2
Img_Name = './Images/SubtractedImage.png'
cv2.imwrite(Img_Name, image3)

# rgb = cv2.imread('./Images/SubtractedImage.png')
# grey_scale = cv2.imread('./Images/SubtractedImage.png',0)
# row = grey_scale[:,0]
# pylab.plot(grey_scale[:,800:900])
# os.system("pause")
# cv2.imshow('grey scale', grey_scale)
# cv2.imshow('rgb', rgb)
# cv2.waitKey(0)


