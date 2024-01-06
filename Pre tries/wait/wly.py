import welly
import numpy as np

# Define the target coordinates
targets = [(100, 200, 0), (300, 400, -500)]

# Create a well trajectory
wt = welly.WellTops(targets)

# Add constraints to the well trajectory
wt.add_deviation_angle_constraint(0, 90)
wt.add_deviation_angle_constraint(500, 90)
wt.add_deviation_angle_constraint(1000, 90)

wt.add_minimum_curvature_constraint(0, 500)
wt.add_minimum_curvature_constraint(500, 500)

wt.add_tangential_velocity_constraint(0, 60)
wt.add_tangential_velocity_constraint(500, 60)

# Generate the well trajectory
wt.generate()

# Print the well trajectory
print(wt.deviation_survey())
