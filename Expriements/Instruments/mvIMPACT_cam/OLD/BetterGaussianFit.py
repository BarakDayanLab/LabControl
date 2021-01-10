import numpy, scipy, matplotlib
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.optimize import differential_evolution
import warnings
import numpy as np

#Parameters
X_PIXEL_LEN = 1544
Y_PIXEL_LEN = 2064

# Create x and y indices
x = np.linspace(0, X_PIXEL_LEN-1, X_PIXEL_LEN)
y = np.linspace(0, Y_PIXEL_LEN-1, Y_PIXEL_LEN)
x, y = np.meshgrid(x, y)

# exponential equation + offset
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

data = twoD_Gaussian((x, y), 3, 100, 100, 20, 40, 0, 10)

# function for genetic algorithm to minimize (sum of squared error)
def sumOfSquaredError(parameterTuple):
    warnings.filterwarnings("ignore") # do not print warnings by genetic algorithm
    val = twoD_Gaussian((x, y), *parameterTuple)
    return numpy.sum((data - val) ** 2.0)


def generate_Initial_Parameters():
    minY = min(data)
    maxY = max(x, y)

    parameterBounds = []
    parameterBounds.append([0.0, 5.0]) # search bounds for a
    parameterBounds.append([5.0, 15.0]) # search bounds for b
    parameterBounds.append([minY, maxY]) # search bounds for offset

    # "seed" the numpy random number generator for repeatable results
    result = differential_evolution(sumOfSquaredError, parameterBounds, seed=3)
    return result.x

# by default, differential_evolution completes by calling curve_fit() using parameter bounds
geneticParameters = generate_Initial_Parameters()

# now call curve_fit without passing bounds from the genetic algorithm,
# just in case the best fit parameters are aoutside those bounds
fittedParameters, pcov = curve_fit(twoD_Gaussian, (x,y), data, geneticParameters)
print('Fitted parameters:', fittedParameters)
print()

modelPredictions = twoD_Gaussian( (x,y), *fittedParameters)

absError = modelPredictions - data

SE = numpy.square(absError) # squared errors
MSE = numpy.mean(SE) # mean squared errors
RMSE = numpy.sqrt(MSE) # Root Mean Squared Error, RMSE
Rsquared = 1.0 - (numpy.var(absError) / numpy.var(data))

print()
print('RMSE:', RMSE)
print('R-squared:', Rsquared)

print()


##########################################################
# graphics output section
def ModelAndScatterPlot(graphWidth, graphHeight):
    f = plt.figure(figsize=(graphWidth/100.0, graphHeight/100.0), dpi=100)
    axes = f.add_subplot(111)

    # first the raw data as a scatter plot
    axes.plot((x,y), data,  'D')

    # create data for the fitted equation plot
    xModel = numpy.linspace(min(x,y), max(x,y))
    yModel = twoD_Gaussian(xModel, *fittedParameters)

    # now the model as a line plot
    axes.plot(xModel, yModel)

    axes.set_xlabel('X Data') # X axis data label
    axes.set_ylabel('Y Data') # Y axis data label

    plt.show()
    plt.close('all') # clean up after using pyplot

graphWidth = 800
graphHeight = 600
ModelAndScatterPlot(graphWidth, graphHeight)