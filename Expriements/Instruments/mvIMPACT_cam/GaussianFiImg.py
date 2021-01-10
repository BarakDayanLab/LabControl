import scipy.optimize as opt
import numpy as np
import pylab as plt
import math
import cv2
import matplotlib.pyplot as mtl

ImgToFit = cv2.imread('./Images/SubtractedImage.png',0)
img_max_index = [np.argmax(np.sum(ImgToFit,axis=1)),np.argmax(np.sum(ImgToFit,axis=0))]

# Parameters
X_PIXEL_LEN=1544
Y_PIXEL_LEN=2064
CROP_IMG_SIZE =200

X_UPPER_BOUND = int(img_max_index[0] + CROP_IMG_SIZE)
X_LOWER_BOUND = int(img_max_index[0] - CROP_IMG_SIZE)
EFFECTIVE_X_PIXEL_LEN = X_UPPER_BOUND-X_LOWER_BOUND

Y_UPPER_BOUND = int(img_max_index[1] + CROP_IMG_SIZE)
Y_LOWER_BOUND = int(img_max_index[1] - CROP_IMG_SIZE)
EFFECTIVE_Y_PIXEL_LEN = Y_UPPER_BOUND - Y_LOWER_BOUND


#define model function and pass independant variables x and y as a list
def twoD_Gaussian(x_y , amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
    x,y = x_y
    xo = float(xo)
    yo = float(yo)
    a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
    b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
    c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
    g = offset + amplitude*np.exp( - (a*((x-xo)**2) + 2*b*(x-xo)*(y-yo)
                            + c*((y-yo)**2)))
    return g.ravel()

# Create x and y indices
x = np.linspace(0, EFFECTIVE_Y_PIXEL_LEN-1, EFFECTIVE_Y_PIXEL_LEN)
y = np.linspace(0, EFFECTIVE_X_PIXEL_LEN-1, EFFECTIVE_X_PIXEL_LEN)
x, y = np.meshgrid(x, y)

#create data
# data = twoD_Gaussian((x, y), 3, 750, 1000, 100, 200, 0, 10)
#
# # plot twoD_Gaussian data generated above
# plt.figure()
# plt.imshow(data.reshape(X_PIXEL_LEN, Y_PIXEL_LEN))
# plt.colorbar()




# data_noisy = data + 0.2*np.random.normal(size=data.shape)

EffectiveImg = ImgToFit[X_LOWER_BOUND:X_UPPER_BOUND,Y_LOWER_BOUND:Y_UPPER_BOUND]
data_noisy = EffectiveImg.ravel()

# add some noise to the data and try to fit the data generated beforehand
img_max_index = [np.argmax(np.sum(EffectiveImg,axis=1)),np.argmax(np.sum(EffectiveImg,axis=0))]
# initial_guess = (160,290,370,48,55,0,10)
initial_guess = (EffectiveImg[img_max_index[0],img_max_index[1]],img_max_index[0], img_max_index[1], EFFECTIVE_X_PIXEL_LEN/3, EFFECTIVE_Y_PIXEL_LEN/3,0,10)

popt, pcov = opt.curve_fit(twoD_Gaussian, (x, y), data_noisy, p0=initial_guess)

# plot the results
data_fitted = twoD_Gaussian((x, y), *popt)
sigma = [popt[3],popt[4]]
fig, ax = plt.subplots(1, 1)

plt.text(0.88, 0.95, '\u03C3_x =' + '%.2f' %sigma[0] + '\n'+'\u03C3_y = ' + '%.2f' %sigma[1], color='white', fontsize=16, style='italic',weight ='bold', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, bbox=dict(facecolor='gray', alpha=0.5))
ax.imshow(data_noisy.reshape(EFFECTIVE_X_PIXEL_LEN, EFFECTIVE_Y_PIXEL_LEN), cmap=plt.cm.jet, origin='bottom',
    extent=(x.min(), x.max(), y.min(), y.max()))
ax.contour(x, y, data_fitted.reshape(EFFECTIVE_X_PIXEL_LEN, EFFECTIVE_Y_PIXEL_LEN), 8, colors='w')

plt.show()

#plot slice
mtl.figure()
data_noisy_mat = data_noisy.reshape(EFFECTIVE_X_PIXEL_LEN, EFFECTIVE_Y_PIXEL_LEN)
Slice = data_noisy_mat[int(EFFECTIVE_X_PIXEL_LEN/2)-10]
mtl.plot(Slice)
mtl.plot(data_fitted.reshape(EFFECTIVE_X_PIXEL_LEN, EFFECTIVE_Y_PIXEL_LEN)[int(EFFECTIVE_X_PIXEL_LEN/2)-10])

plt.show()
