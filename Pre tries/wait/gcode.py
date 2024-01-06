import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Define the surface coordinates
surface_x = 0
surface_y = 0
surface_z = 0

# Define the target coordinates
target_1_x = 100
target_1_y = 100
target_1_z = 100

target_2_x = 200
target_2_y = 200
target_2_z = 200

target_3_x = 300
target_3_y = 300
target_3_z = 300

# Define the well parameters
well_length = 5000
well_angle = np.deg2rad(60) # in radians

# Calculate the drop and hold profile
x = np.array([surface_x, target_1_x, target_2_x, target_3_x])
y = np.array([surface_y, target_1_y, target_2_y, target_3_y])
z = np.array([surface_z, target_1_z, target_2_z, target_3_z, target_3_z])

distance = np.sqrt((x[1:] - x[:-1])**2 + (y[1:] - y[:-1])**2 + (z[1:] - z[:-1])**2)

hold_distance = distance[:-1] * np.cos(well_angle)
hold_z = z[:-1] + hold_distance * np.tan(well_angle)

drop_z = z[1:]
drop_distance = distance[:-1] * np.sin(well_angle)

# Create the plot
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

ax.plot(x, y, z, '-o', label='Well Path')
ax.plot(x[:-1], y[:-1], hold_z, '--', label='Hold Profile')
ax.plot(x[:-1], y[:-1], drop_z, '--', label='Drop Profile')

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
ax.legend()

plt.show()
