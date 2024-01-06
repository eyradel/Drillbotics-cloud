import well_profile as wp

def vprofile(target_depth, cells_no, units, set_start,):
    well = wp.get(target_depth,   # define target depth (md) in m or ft
            cells_no=cells_no,   # (optional) define number of cells
            units=units,   # (optional) define system of units 'metric' for meters or 'english' for feet
            set_start=set_start)    # (optional) set the location of initial point

    return well.df()


def sprofile(target_depth, kop, eob, build_angle, sod, eod, units, cells_no, set_start):    
    well = wp.get(target_depth,
        profile='S',    # set S-type well profile 
        kop=kop,    # set kick off point in m or ft
        eob=eob,   # set end of build in m or ft        
        build_angle=build_angle,   # set build angle in °
        sod=sod,   # set start of drop in m or ft
        eod=eod,   # set end of drop in m or ft
        units=units,   # (optional) define system of units 'metric' for meters or 'english' for feet
        cells_no=cells_no,   # (optional) define number of cells
        set_start=set_start
        )
                
    return well.df()


def jprofile(target_depth, kop, eob, build_angle, units, cells_no, set_start):
    well = wp.get(target_depth,   # define target depth (md) in m or ft
        profile='J',    # set J-type well profile 
        kop=kop,    # set kick off point in m or ft
        eob=eob,   # set end of build in m or ft
        build_angle=build_angle,   # set build angle in °
        cells_no=cells_no,   # (optional) define number of cells
        units=units,   # (optional) define system of units 'metric' for meters or 'english' for feet
        change_azimuth=50,
        set_start=set_start)    # (optional) set the location of initial point

    return well.df()


def hscprofile(target_depth, kop, eob, build_angle, units, cells_no, set_start):
    well = wp.get(target_depth,   # define target depth (md) in m or ft
            profile='H1',    # set horizontal single curve well profile 
            kop=kop,    # set kick off point in m or ft
            eob=eob,   # set end of build in m or ft
            build_angle=build_angle,   # set build angle in °
            cells_no=cells_no,   # (optional) define number of cells
            units=units,   # (optional) define system of units 'metric' for meters or 'english' for feet
            set_start=set_start)    # (optional) set the location of initial point

    return well.df()


def hdcprofile(target_depth, kop, eob, build_angle, units, cells_no, set_start):
    well = wp.get(target_depth,   # define target depth (md) in m or ft
        profile='H2',    # set horizontal single curve well profile 
        kop=kop,    # set kick off point in m or ft
        eob=eob,   # set end of build in m or ft
        build_angle=build_angle,   # set build angle in °
        cells_no=cells_no,   # (optional) define number of cells
        units=units,   # (optional) define system of units 'metric' for meters or 'english' for feet
        set_start=set_start)    # (optional) set the location of initial point

    return well.df()


def get_well_data(profile_type, target_depth, kop=0, eob=0, build_angle=0, sod=0, eod=0, units='metric', cells_no=100, set_start={'north': 0, 'east': 0, 'depth': 0}):
    
    if profile_type.lower() == 'v':
        well_data = vprofile(target_depth, cells_no, units, set_start)
    elif profile_type.lower() == 's':
        well_data = sprofile(target_depth, kop, eob, build_angle, sod, eod, units, cells_no, set_start)
    elif profile_type.lower() == 'j':
        well_data = jprofile(target_depth, kop, eob, build_angle, units, cells_no, set_start)
    elif profile_type.lower() == 'hsc':
        well_data = hscprofile(target_depth, kop, eob, build_angle, units, cells_no, set_start)
    elif profile_type.lower() == 'hdc':
        well_data = hdcprofile(target_depth, kop, eob, build_angle, units, cells_no, set_start)
    else:
        raise ValueError("Invalid well type")
    
    return well_data


def get_well_coods(well_data):
    """
    Takes a pd dataframe of well from get_well_data
    and returns the 3 coordinate axes values for plotting
    """
    xyzframe = well_data[['east', 'north', 'tvd']]
    x, y, z = xyzframe.values.T.tolist()

    return x, y, z
