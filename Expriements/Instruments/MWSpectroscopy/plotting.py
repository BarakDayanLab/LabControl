import numpy as np
import matplotlib.pyplot as plt

offsets = np.loadtxt('offsets_log.csv', delimiter=',', skiprows=1)
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(offsets[:, 0], offsets[:,1], offsets[:, 2])

corrections = np.loadtxt('correction_log.csv', delimiter=',', skiprows=1)
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(corrections[:, 0], corrections[:, 1], corrections[:, 2])
plt.show()
