from typing import Union

import math
import numpy as np
import matplotlib.pyplot as plt


def build_and_hold(sc: str, tc: str, tvd_target: float, tvd_kop: float, bur: float) -> Union[dict, tuple]:
    """
    R:              radius of curvature in degree per 100 meters
    sc:             surface_coodinates(x: northing, x: easting)
    tc:             target_coodinates(x: northing, x: easting)
    tvd_target:     true vertical dept to target
    tvd_kop:        true vertical dept to kickoff point
    bur:            buildup rate in degree per 100ft
    H:              Horizontal displacement of target
    B:              target bearing
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
    
    parameters = dict()                                                            # Code written at Virtual world
    h_cordinates = []                                                              # BB: Vadmin
    y_cordinates = []
    
    R = ((180/math.pi) * 100) / bur

    tc = tc.split(",")
    sc = sc.split(",")
    target_northing = float(tc[0])
    target_easting = float(tc[1])
    surface_northing = float(sc[0])
    surface_easting = float(sc[1])
    
    H = math.sqrt(((target_northing-surface_northing)**2) + ((target_easting-surface_easting)**2))
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
    v_tangent = tvd_target-tvd_end_b
    build_up_l = (max_angle*100)/bur
    t_length = (v_tangent) / math.cos(max_angle)
    t_dept = tvd_kop + build_up_l + t_length

    h_cordinates.append(0)
    y_cordinates.append(0)
    h_cordinates.append(0)
    y_cordinates.append(tvd_kop)
    for i in np.arange(tvd_kop, tvd_end_b, 10.0):
        h_cordinates.append(R-math.sqrt((R**2)-((i-tvd_kop)**2)))
        y_cordinates.append(i)
    h_cordinates.append(hd_end_build)
    y_cordinates.append(tvd_end_b)
    h_cordinates.append(H)
    y_cordinates.append(tvd_target)
    plot_coordinates = (h_cordinates, y_cordinates)

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

print("\n"*2)
for key, val in parameters.items():
    print(key, val)

plt.figure(figsize=(4, 6))
plt.plot(plot_coordinates[0], plot_coordinates[1])
plt.gca().invert_yaxis()
plt.title("Build and hold profile")
plt.xlabel("Horizontal distance")
plt.ylabel("Vertical distace")
plt.show()
