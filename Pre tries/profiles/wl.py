import welly
import numpy as np
import inspect

# create a list of target coordinates
targets = [{"top": 0, "bottom": 1000, "latitude": 29.7604, "longitude": -95.3698},
           {"top": 0, "bottom": 1200, "latitude": 29.7604, "longitude": -95.3698},
           {"top": 0, "bottom": 1400, "latitude": 29.7604, "longitude": -95.3698}]

# extract the x, y, and z coordinates from the targets
x = np.array([target["longitude"] for target in targets])
y = np.array([target["latitude"] for target in targets])
z = np.array([target["top"] for target in targets])

# fit a polynomial curve to the target coordinates
p = np.polyfit(x, y, deg=2)

# generate a range of x values for the curve
x_range = np.linspace(np.min(x), np.max(x), num=100)

# calculate the corresponding y values for the curve
y_range = np.polyval(p, x_range)

# create a new Location object
location = welly.Location({"latitude": np.mean(y_range), "longitude": np.mean(x_range), "elevation": 0, "deviation": [[0, 0, 0]]})

# add a deviation survey to the location
md = z[0]
inc = 0
azi = 0
print(inspect.getsource(location.add_deviation))
location.add_deviation(inc, azi, md)

for i in range(len(x_range)):
    md = z[i]
    inc = 0
    azi = 0
    location.add_deviation([inc, azi, md])

# create a new Well object
well = welly.Well()

# set the location of the well
well.location = location

# plot the well trajectory
well.plot()
