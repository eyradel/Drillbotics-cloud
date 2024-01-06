from typing import Union

import math
import numpy as np
import matplotlib.pyplot as plt


def build_hold_and_drop(sc: str, tc: str, tvd_target: float, tvd_kop: float, 
                        bur: float, drr: float, tvd_drop_end: float,
                        f_angle_target: float) -> Union[dict, tuple]:
    """
    R1:             radius of curvature in degree per 100 meters[buildup section]
    R2:             radius of curvature in degree per 100 meters[dropoff section]
    sc:             surface_coodinates(x: northing, x: easting)
    tc:             target_coodinates(x: northing, x: easting)
    tvd_target:     true vertical dept to target
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
    Returns neccessary calculated parameters and the ploting cordinates
    as a turple of lists
    """
    
    f_angle_target = math.radians(f_angle_target) # Change angle to radians

    parameters = dict()                                                            # Code written at Virtual world
    h_cordinates = []                                                              # BB: Vadmin
    v_cordinates = []
    
    tc = tc.split(",")
    sc = sc.split(",")
    target_northing = float(tc[0])
    target_easting = float(tc[1])
    surface_northing = float(sc[0])
    surface_easting = float(sc[1])
    
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

    h_cordinates.append(0)
    v_cordinates.append(0)
    h_cordinates.append(0)
    v_cordinates.append(tvd_kop)
    for i in np.arange(tvd_kop, tvd_end_b, 10.0):
        v_cordinates.append(i)
        h_cordinates.append(R1-math.sqrt((R1**2)-((i-tvd_kop)**2)))
    h_cordinates.append(hd_end_build)
    v_cordinates.append(tvd_end_b)
    h_cordinates.append(hd_drop_start)
    v_cordinates.append(tvd_drop_start)
    for i in np.arange(tvd_drop_start, tvd_drop_end, 10.0):
        v_cordinates.append(i)
        h_cordinates.append(R1+OQ+math.sqrt((R2**2)-((tvd_kop+OP-i)**2)))
    h_cordinates.append(hd_drop_end)
    v_cordinates.append(tvd_drop_end)
    h_cordinates.append(H)
    v_cordinates.append(tvd_target)
    plot_coordinates = (h_cordinates, v_cordinates)

    parameters["Info"] = "\n[Target coodinates not suited for the\n given" \
    " true vertical dept to 'start of drop']" if tvd_target <= tvd_drop_start \
    or tvd_drop_end < tvd_drop_start else ""
    parameters["Horizontal displacement"] = H
    parameters["Target bearing"] = f"N {B} E"
    parameters["Radius of curvature at build section"] = R1
    parameters["Radius of curvature at drop section"] = R2
    parameters["Max inclination angle"] = max_angle
    
    return(plot_coordinates, parameters)


sc = input("Input surface coordinates measured in feet as northings," \
  " easting [e.g, 14.0,4.9 ]: ")
tc = input("Input target coordinates measured in feet as northings," \
  " easting [e.g, 1555,4500 ]: ")
tvd_target = float(input("Input true vertical dept of target: "))
tvd_kop = float(input("Input true vertical dept to kickoff point: "))
bur = float(input("Input buildup rate in degree per 100ft: "))
drr = float(input("Input dropoff rate in degree per 100ft: "))
tvd_drop_end = float(input("Input true vertical dept to end of drop: "))
f_angle_target = float(input("Input final angle of inclinatin through target: "))

plot_coordinates, parameters = build_hold_and_drop(
    sc, tc, tvd_target, tvd_kop, bur, drr, tvd_drop_end, f_angle_target
)

print("\n"*2)
for key, val in parameters.items():
    print(key, val)

plt.figure(figsize=(5, 6))
plt.plot(plot_coordinates[0], plot_coordinates[1])
plt.gca().invert_yaxis()
plt.title("Build and hold profile"+str(parameters.get("Info")))
plt.xlabel("Horizontal distance")
plt.ylabel("Vertical distace")
plt.show()


# Please make sure to always use right values for the input to avoid errors
# since errors area't caught yet