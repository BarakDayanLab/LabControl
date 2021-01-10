import scipy.optimize as opt
import numpy as np
import pylab as plt
import math

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
x = np.linspace(0, 200, 201)
y = np.linspace(0, 200, 201)
x, y = np.meshgrid(x, y)
#create data
data = twoD_Gaussian((x, y), 3, 100, 100, 20, 40, 0, 10)

# plot twoD_Gaussian data generated above
plt.figure()
plt.imshow(data.reshape(201, 201))
plt.colorbar()



# add some noise to the data and try to fit the data generated beforehand
initial_guess = (3,100,100,20,40,0,10)

data_noisy = data + 0.2*np.random.normal(size=data.shape)

popt, pcov = opt.curve_fit(twoD_Gaussian, (x, y), data_noisy, p0=initial_guess)

# plot the results
data_fitted = twoD_Gaussian((x, y), *popt)
sigma = [popt[3],popt[4]]
fig, ax = plt.subplots(1, 1)

plt.text(0.88, 0.95, '\u03C3_x =' + '%.2f' %sigma[0] + '\n'+'\u03C3_y = ' + '%.2f' %sigma[1], color='white', fontsize=16, style='italic',weight ='bold', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, bbox=dict(facecolor='gray', alpha=0.5))
ax.imshow(data_noisy.reshape(201, 201), cmap=plt.cm.jet, origin='bottom',
    extent=(x.min(), x.max(), y.min(), y.max()))
ax.contour(x, y, data_fitted.reshape(201, 201), 8, colors='w')
plt.show()