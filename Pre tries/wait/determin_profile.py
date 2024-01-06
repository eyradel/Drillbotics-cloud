import math

def get_well_profile(targets):
    # Calculate the distances between each pair of target coordinates in each axis.
    x_distances = [abs(targets[0][0] - targets[1][0]), abs(targets[1][0] - targets[2][0]), abs(targets[2][0] - targets[3][0])]
    y_distances = [abs(targets[0][1] - targets[1][1]), abs(targets[1][1] - targets[2][1]), abs(targets[2][1] - targets[3][1])]
    z_distances = [abs(targets[0][2] - targets[1][2]), abs(targets[1][2] - targets[2][2]), abs(targets[2][2] - targets[3][2])]

    # Sort the distances in each axis in ascending order.
    x_distances.sort()
    y_distances.sort()
    z_distances.sort()

    # Calculate the angle between the three axes.
    x_angle = math.atan2(z_distances[0], y_distances[0])
    y_angle = math.atan2(z_distances[0], x_distances[0])
    z_angle = math.atan2(y_distances[0], x_distances[0])

    # Determine the type of profile based on the distances and angle.
    if x_distances[0] == x_distances[1] == x_distances[2] and y_distances[0] == y_distances[1] == y_distances[2] and z_distances[0] == z_distances[1] == z_distances[2]:
        return "Straight"
    elif x_distances[0] == x_distances[1] < x_distances[2] and y_distances[0] < y_distances[1] == y_distances[2] and z_distances[0] < z_distances[1] == z_distances[2] and x_angle > math.pi/2 and y_angle > math.pi/2:
        return "J"
    elif x_distances[0] < x_distances[1] == x_distances[2] and y_distances[0] < y_distances[1] == y_distances[2] < z_distances[0] == z_distances[1] == z_distances[2] and y_angle > math.pi/2 and z_angle > math.pi/2:
        return "S"
    elif x_distances[0] < x_distances[1] == x_distances[2] and y_distances[0] < y_distances[1] == y_distances[2] and z_distances[0] < z_distances[1] < z_distances[2] and y_angle > math.pi/2 and z_angle > math.pi/2:
        return "L"
    else:
        return "Unknown"


targets = [(1284.59, 741.66, 1677.21), (238.21, 137.53, 1164.06), (337.47, 194.84, 1223.73), (759.59, 438.55, 1327.21)]
profile = get_well_profile(targets);
print(profile)