import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
from typing import Union
import math

def build_and_hold(sc: str, tc: str, tvd_target: float, tvd_kop: float,
                    bur: float) -> Union[dict, tuple]:
    """    
    sc:             surface_coodinates(x: northing, x: easting)
    tc:             target_coodinates(x: northing, x: easting)
    tvd_target:     true vertical dept to target
    tvd_kop:        true vertical dept to kickoff point
    bur:            buildup rate in degree per 100ft    
    max_angle:      maximum inclination angle
    tvd_end_b       true vertical dept till end of build
    build_up_l      build up length
    hd_end_build    horizontal displacement at the end of build up
    t_length        tangent's true length
    t_dept          total true dept of profile
    v_kop_end_build vertical dept from kop to end of buildup
    v_tangent       vertical dept of tangent

    Calculates other neccessary parameters and coordinates for ploting the build and hold profile
    Returns neccessary calculated parameters and the ploting cordinates as a turple of lists
    """

    parameters = dict()
    y_cordinates = [] # Vertical depth
    h_cordinates = [] # Eastings
    z_cordinates = [] # Northenings

    # radius of curvature in degree per 100 meters
    R = ((180/math.pi) * 100) / bur

    target_northing = float(tc.split(",")[0])
    target_easting = float(tc.split(",")[1])
    surface_northing = float(sc.split(",")[0])
    surface_easting = float(sc.split(",")[1])
    
    # H - Horizontal displacement of target
    H = math.sqrt(((target_northing-surface_northing)**2) + ((target_easting-surface_easting)**2))
    # B - target bearing
    B = math.atan((target_easting-surface_easting)/(target_northing-surface_northing))
    
    x = math.atan((H-R)/(tvd_target-tvd_kop))
    try:
        y = math.asin((R*math.cos(x)) / (tvd_target-tvd_kop))
    except ValueError:
        print("Invalid build up rate for the provided paramenters")
        exit(1)
    max_angle = x + y  
        
    v_kop_end_build = R*math.sin(max_angle)
    tvd_end_b = tvd_kop + v_kop_end_build
    hd_end_build = R - (R*math.cos(max_angle))
    v_tangent = tvd_target - tvd_end_b
    build_up_l = (max_angle*100) / bur
    t_length = (v_tangent) / math.cos(max_angle)
    t_dept = tvd_kop + build_up_l + t_length

    # At the surface
    y_cordinates.append(0)
    h_cordinates.append(surface_easting)
    z_cordinates.append(surface_northing)

    # At kickoff point
    y_cordinates.append(tvd_kop)
    h_cordinates.append(surface_easting)
    z_cordinates.append(surface_northing)

    # At the build
    for i in np.arange(tvd_kop, tvd_end_b, 10.0):
        y_cordinates.append(i)
        h_shift = (R - math.sqrt((R**2)-((i-tvd_kop)**2)))
        h_cordinates.append(h_shift)
 
    # At end of build to target
    # Evenly space coordinates with a step of 10 as during the build to ensure
    # z_coordinates are even from kop to target
    count = 0
    for i in np.arange(tvd_end_b, tvd_target, 10.0):
        count += 1
        y_cordinates.append(i)
    for i in np.linspace(hd_end_build, target_easting, count):
        h_cordinates.append(i)

    build_target_z = np.linspace(surface_northing, target_northing, len(h_cordinates)-2)
    z_cordinates += list(build_target_z)

    plot_coordinates = (h_cordinates, y_cordinates, z_cordinates)

    parameters["Horizontal displacement"] = H
    parameters["Target bearing"] = f"N {B} E"
    parameters["Radius of curvature"] = R
    parameters["Max inclination angle"] = max_angle
    parameters["Total length of profile"] = t_dept
    
    return(plot_coordinates, parameters)


sc = input("Input surface coordinates measured in feet as northings, easting [e.g, 14.0,4.9 ]: ")
tc = input("Input target coordinates measured in feet as northings, easting [e.g, 1555,4500 ]: ")
tvd_target = float(input("Input true vertical dept of target: "))
tvd_kop = float(input("Input true vertical dept to kickoff point: "))
bur = float(input("Input buildup rate: "))

plot_coordinates, parameters = build_and_hold(sc, tc, tvd_target, tvd_kop, bur)

fig = plt.figure()
ax = plt.axes(projection='3d')
plt.gca().invert_zaxis()
ax.plot3D(plot_coordinates[0], plot_coordinates[2], plot_coordinates[1], "blue")
ax.set_xlabel("Eastings")
ax.set_ylabel("Northenings")
ax.set_zlabel("Vertical Depth")
ax.view_init(elev=50, azim=(-42))
ax.set_title("Build and hold profile")

plt.show()