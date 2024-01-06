import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
import math

targets = [(0, 0, 0), (1284.59, 741.66, 1677.21), (238.21, 137.53, 1164.06), (337.47, 194.84, 1223.73), (759.59, 438.55, 1327.21)]
targets = sorted(targets, key=lambda x: x[2])

fig = plt.figure()
ax = plt.axes(projection='3d')
plt.gca().invert_zaxis()
ax.plot3D([x[0] for x in targets], [x[1] for x in targets], [x[2] for x in targets], "blue")
ax.scatter([x[0] for x in targets[1:]], [x[1] for x in targets[1:]], [x[2] for x in targets[1:]], c='r')
ax.set_xlabel("Eastings")
ax.set_ylabel("Northenings")
ax.set_zlabel("Vertical Depth")
ax.view_init(elev=50, azim=(-42))
ax.set_title("Build and hold profile")

plt.show()