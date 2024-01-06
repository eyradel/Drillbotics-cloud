# from drillpy import Trajectory, Target

# Define surface coordinates and initial trajectory
surface_coord = (0, 0, 0)
init_traj = Trajectory(surface_coord, 0, 0)

# Define four target coordinates
target1 = Target((100, 0, 100), 0, 0)
target2 = Target((200, 100, 200), 0, 0)
target3 = Target((300, 200, 300), 0, 0)
target4 = Target((400, 300, 400), 0, 0)

# Add targets to trajectory
init_traj.add_target(target1)
init_traj.add_target(target2)
init_traj.add_target(target3)
init_traj.add_target(target4)

# Define wellbore parameters
well_radius = 6.125
DLS = 2.0

# Calculate wellbore trajectory using minimum curvature method
traj = init_traj.minimum_curvature(well_radius, DLS)

# Plot wellbore trajectory
traj.plot()
