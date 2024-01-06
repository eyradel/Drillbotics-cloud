from typing import Union

import math
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d


def build_hold_and_drop(sc: str, tc: np.array, tvd_kop: float, 
                        bur: float, drr: float, tvd_drop_end: float,
                        f_angle_target: float) -> Union[dict, tuple]:
    """
    R1:             radius of curvature in degree per 100 meters[buildup section]
    R2:             radius of curvature in degree per 100 meters[dropoff section]
    sc:             surface_coodinates(x: northing, x: easting)
    tc:             target_coodinates(x: northing, x: easting)
    tvd_kop:        true vertical dept to kickoff point
    bur:            buildup rate in degree per 100ft
    drr:            dropoff rate in degree per 100ft
    tvd_drop_end:   true vertical dept at the end of drop off
    f_angle_target: final angle of inclination through target in degrees
    max_angle:      maximum inclination angle at buildup
    H:              Horizontal displacement of target
    v_kop_end_build vertical dept from kop to end of buildup
    hd_end_build    horizontal displacement at the end of build up
    tvd_end_b       true vertical dept till end of build
    tvd_drop_start  true vertical dept till start of drop
    hd_drop_start   horizontal displacement to start of drop
    hd_drop_end     horizontal displacement at the end of drop
    B:              target bearing
    
    Calculates other neccessary parameters and coordinates for 
    ploting the build, hold and drop profile
    Returns neccessary calculated parameters and ploting cordinates
    as a turple of lists
    """
    
    f_angle_target = math.radians(f_angle_target) # Change angle to radians

    parameters = dict()                                                            # Code written at Virtual world
    easting_cordinates = []                                                        # BB: Vadmin
    v_cordinates = []
    northening_cordinates = []
    
    sorted_indices = np.argsort(tc[:, 2])
    tc = tc[sorted_indices]
    # Target with max dept == last target after the sort
    target_northing = tc[-1][0]
    target_easting = tc[-1][1]
    tvd_target = tc[-1][2]

    surface_northing = sc[0]
    surface_easting = sc[1]
    surface_dept = sc[2]
    
    B = math.atan((target_easting-surface_easting) \
        / (target_northing-surface_northing))
 
    H = math.sqrt(((target_northing-surface_northing)**2) \
        + ((target_easting-surface_easting)**2))  
    
    R1 = ((180/math.pi) * 100) / bur
    R2 = ((180/math.pi) * 100) / drr

    OQ = H - R1 - (R2*math.cos(f_angle_target)) \
        - (tvd_target-tvd_drop_end)*math.tan(f_angle_target)    

    OP = tvd_drop_end-tvd_kop+(R2*math.sin(f_angle_target))
    QS = R1 + R2
    PQ = math.sqrt((OP**2)+((abs(OQ)**2)))
    PS = math.sqrt((PQ**2)-(QS**2))
    
    max_angle = math.atan(OQ/OP) + math.atan(QS/PS)
        
    v_kop_end_build = R1*math.sin(max_angle)
    tvd_end_b = tvd_kop + v_kop_end_build
    hd_end_build = R1 - (R1*math.cos(max_angle))
    tvd_drop_start = tvd_end_b + (PS*math.cos(max_angle))
    hd_drop_start = hd_end_build + (PS*math.sin(max_angle))
    hd_drop_end = hd_drop_start + (R2*(math.cos(f_angle_target) \
                - math.cos(max_angle)))

    # At the surface
    easting_cordinates.append(surface_easting)
    v_cordinates.append(surface_dept)
    northening_cordinates.append(surface_northing)

    # At kickoff
    easting_cordinates.append(surface_easting)
    v_cordinates.append(tvd_kop)
    northening_cordinates.append(surface_northing)

    # At build
    for i in np.arange(tvd_kop, tvd_end_b, 10.0):
        v_cordinates.append(i)
        easting_cordinates.append(R1-math.sqrt((R1**2)-((i-tvd_kop)**2)))

    # At end of build / start of hold
    # h_cordinates.append(hd_end_build)
    # v_cordinates.append(tvd_end_b)
    
    count = 0
    for i in np.arange(hd_end_build, hd_drop_start, 10.0):
        easting_cordinates.append(i)
        count += 1
    for i in np.linspace(tvd_end_b, tvd_drop_start, count):
        v_cordinates.append(i)
        
    # At end of hold / start of drop
    # h_cordinates.append(hd_drop_start)
    # v_cordinates.append(tvd_drop_start)

    # At start of drop
    for i in np.arange(tvd_drop_start, tvd_drop_end, 10.0):
        v_cordinates.append(i)
        easting_cordinates.append(R1+OQ+math.sqrt((R2**2)-((tvd_kop+OP-i)**2)))

    # At end of drop
    # h_cordinates.append(hd_drop_end)
    # v_cordinates.append(tvd_drop_end)
    
    count = 0
    for i in np.arange(hd_drop_end, H, 10.0):
        easting_cordinates.append(i)
        count += 1
    for i in np.linspace(tvd_drop_end, tvd_target, count):
        v_cordinates.append(i)

    # At target
    # h_cordinates.append(H)
    # v_cordinates.append(tvd_target)

    build_target_z = np.linspace(surface_northing, target_northing, len(easting_cordinates)-2)
    northening_cordinates += list(build_target_z)
    
    plot_coordinates = (easting_cordinates, northening_cordinates, v_cordinates)

    parameters["Info"] = "\n[Target coodinates not suited for the\n given" \
    " true vertical dept to 'start of drop']" if tvd_target <= tvd_drop_start \
    or tvd_drop_end < tvd_drop_start else ""
    parameters["Horizontal displacement"] = H
    parameters["Target bearing"] = f"N {B} E"
    parameters["Radius of curvature at build section"] = R1
    parameters["Radius of curvature at drop section"] = R2
    parameters["Max inclination angle"] = max_angle

    ax = plt.axes(projection='3d')
    # plt.figure(figsize=(5, 6))
    # ax.plot3D(plot_coordinates[0], plot_coordinates[1], plot_coordinates[2])
    # print(plot_coordinates[0][-1], plot_coordinates[1][-1], plot_coordinates[2][-1])
    
    targets = tc.T
    ax.plot3D(targets[0], targets[1], targets[2])
    
    plt.gca().invert_zaxis()
    ax.set_xlabel("Eastings")
    ax.set_ylabel("Northenings")
    ax.set_zlabel("Vertical Depth")
    ax.view_init(elev=47, azim=(-45))
    ax.set_title("Build hold and drop profile")
    plt.show()

    return(plot_coordinates, parameters)


# Northening : easting : tvd
sc = [0, 0, 0]
tc = np.array(
    [[1284.59, 741.66, 1677.21],
    [238.21, 137.53, 1164.06],
    [337.47, 194.84, 1223.73],
    [759.59, 438.55, 1327.21]]
)
tvd_kop = 6000
bur = 2
drr = 2
tvd_drop_end = 11000
f_angle_target = 15

plot_coordinates, parameters = build_hold_and_drop(
    sc, tc, tvd_kop, bur, drr, tvd_drop_end, f_angle_target
)

