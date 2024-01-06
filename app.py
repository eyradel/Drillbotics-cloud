import time

import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_card import card
import streamlit_toggle as tog

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio

from drillmodules.well_plan.well import InterpWell
from drillmodules.drill_string.select_drilling_apparatus import (
    selected_drill_pipes,
    selected_drill_collars,
)
from drillmodules.rss_model.rss import RSSDataGenerator, SimulatedStation

if "gen_well" not in st.session_state:
    st.session_state.gen_well = InterpWell()

if "ENTERED_DATA" not in st.session_state:
    st.session_state.ENTERED_DATA = False
if "cumulating_rss_data" not in st.session_state:
    st.session_state.cumulating_rss_data = []
if "rss_current_target" not in st.session_state:
    st.session_state.rss_current_target = 1
if "target_distance_away" not in st.session_state:
    st.session_state.target_distance_away = None
if "simulation_state" not in st.session_state:
    st.session_state.simulation_state = "initial"
if "simulation_condition" not in st.session_state:
    st.session_state.simulation_condition = "Yet to Start"

if "rss_generator_data" not in st.session_state:
    st.session_state.rss_generator_data = None
if "first_run" not in st.session_state:
    st.session_state.first_run = True

# session_state.cache = True

st.set_page_config(layout="wide")


def display_error(error):
    st.markdown(f"<span style='color: red'>{error}</span>", unsafe_allow_html=True)


def validate_station_coord(coord, error):
    try:
        x, y, z = coord.split(",")
        valid_coord = (float(x), float(y), float(z))
        return valid_coord
    except ValueError:
        display_error(error)


def validate_float(val, error):
    try:
        return float(val)
    except ValueError:
        display_error(error)


def well_inputs():
    well = st.session_state.gen_well
    rig_coord = []
    target_coord = []
    formation_aggr = []
    ccs = []

    st.sidebar.subheader("Rig Coordinates")
    rig_coord = st.sidebar.text_input(
        "Enter Rig Position Coordinates(East,North,Depth)",
        f"{well.surface_coordinates[0]},{well.surface_coordinates[1]},{well.surface_coordinates[2]}",
    )
    rig_coord = validate_station_coord(
        rig_coord, f"Invalid Rig Coordinates '{rig_coord}'. How: x,y,z"
    )

    st.sidebar.markdown('<hr style="border: 1px solid #ccc">', unsafe_allow_html=True)

    num_targets = st.sidebar.number_input(
        "Please enter number of targets", len(well.target_coordinates)
    )

    first_target_depth = 0
    if num_targets:
        for i in range(int(num_targets)):
            try:
                current_tc = well.target_coordinates[i]
                current_tc = f"{current_tc[0]},{current_tc[1]},{current_tc[2]}"
            except IndexError:
                current_tc = ""

            t = st.sidebar.text_input(
                f"Target {i + 1} (X,Y,Z)",
                current_tc,
            )
            t = validate_station_coord(
                t, f"Invalid Target{i + 1} Coordinates '{t}'. How: x,y,z"
            )
            target_coord.append(t)

            if i == 0:
                try:
                    first_target_depth = float(t[2])
                except TypeError:
                    pass

    st.sidebar.text("")

    st.sidebar.subheader("Kick Off Point")
    kop = st.sidebar.slider(
        "Leave blank for auto KOP suggestion", 0.0, first_target_depth + 0.000001
    )

    st.sidebar.subheader("Formation Characteristics")
    st.text("  ")

    num_formations = st.sidebar.number_input(
        "Please enter number of Formations", len(well.form_aggr)
    )
    cform, cfa, cccs = st.sidebar.columns(3)
    with cform:
        st.markdown("Formation")
    with cfa:
        st.markdown("Hardness")
    with cccs:
        st.markdown("CCS")

    for i in range(num_formations):
        with cform:
            form_ = st.text_input(
                "formation",
                help="",
                key=str(i) + "form",
                value=0,
                label_visibility="hidden",
            )
            form_ = validate_float(
                form_, f"Invalid formation value '{form_}'. Enter a decinal number"
            )
        with cfa:
            formation_aggr_ = st.text_input(
                "form hardness",
                help="",
                key=str(i) + "fa",
                value=0,
                label_visibility="hidden",
            )
            formation_aggr_ = validate_float(
                formation_aggr_,
                f"Invalid formation hardness value '{formation_aggr_}'. Enter a decinal number",
            )
        with cccs:
            ccs_ = st.text_input(
                "ccs", help="", key=str(i) + "ccs", value=0, label_visibility="hidden"
            )
            ccs_ = validate_float(
                ccs_, f"Invalid ccs value '{ccs_}'. Enter a decinal number"
            )

        formation_aggr.append((form_, formation_aggr_))
        ccs.append((form_, ccs_))

    survey_station = st.sidebar.number_input("Survey station", well.station_delta)

    least_form_aggr_kop = st.sidebar.number_input(
        "Least formation hardness for kickoff", well.kop_form_aggr
    )

    interpolators = [
        "PchipInterpolator",
        "Akima1DInterpolator",
    ]
    # Make current well interpolator the first in the list
    interpolators[interpolators.index(well.interpolator)] = interpolators[0]
    interpolators[0] = well.interpolator

    interpolator = st.sidebar.selectbox("Choose interpolator", interpolators)

    inputted_data = {
        "start_coord": rig_coord,
        "target_coord": target_coord,
        "kop": kop,
        "formation_aggr": formation_aggr,
        "ccs": ccs,
        "least_form_aggr_kop": least_form_aggr_kop,
        "survey_station": survey_station,
        "interpolator": interpolator,
    }

    return inputted_data


def setup_well(inputted_data):
    well = st.session_state.gen_well

    start_coord = inputted_data["start_coord"]
    target_coord = inputted_data["target_coord"]
    kop = inputted_data["kop"]
    formation_aggr = inputted_data["formation_aggr"]
    ccs = inputted_data["ccs"]
    least_form_aggr_kop = inputted_data["least_form_aggr_kop"]
    survey_station = inputted_data["survey_station"]
    interpolator = inputted_data["interpolator"]

    well.interpolator = interpolator
    well.kop = kop
    well.surface_coordinates = start_coord
    well.target_coordinates = target_coord
    well.kop_form_aggr = least_form_aggr_kop
    well.station_delta = survey_station
    well.form_aggr = formation_aggr
    well.ccs = ccs
    try:
        well_data = well.output_data[0]
    except IndexError:
        st.error("Enter at least one Valid target to drill!")
        st.stop()

    if kop == 0:
        well.suggest_kop()

    max_dls_row = well_data[well_data["dls"] == well_data["dls"].max()]
    x = max_dls_row["X"].values[0]
    y = max_dls_row["Y"].values[0]
    z = max_dls_row["Z"].values[0]
    md = max_dls_row["md"].values[0]
    max_dls = max_dls_row["dls"].values[0]

    st.markdown(
        f"<h4 style='color: rgb(200,100,100)'>[Max Dogleg: {max_dls:.2f}° per 100 ft @ ({x:.2f},{y:.2f},{z:.2f}), MD of {md:.2f}]</h4>",
        unsafe_allow_html=True,
    )

    st.session_state.gen_well = well


def disp_plan():
    well_data = st.session_state.gen_well.output_data[0]
    targets_coords = st.session_state.gen_well.output_data[1]

    # 2D
    with st.expander("View 2D Graph"):
        n = (well_data["Y"]) ** 2
        e = (well_data["X"]) ** 2
        hd = np.sqrt(n + e)

        tn = (targets_coords["Y"]) ** 2
        te = (targets_coords["X"]) ** 2
        thd = np.sqrt(tn + te)

        well_2d_trace = go.Scatter(
            x=hd,
            y=well_data["Z"],
            mode="lines",
            name="Well Path",
            line=dict(color="rgba(0,0,100,0.7)"),
        )
        targets_2d_trace = go.Scatter(
            x=thd,
            y=targets_coords["Z"],
            mode="markers",
            marker=dict(size=10, color="red"),
            name="Targets",
        )

        layout2d = go.Layout(
            xaxis=dict(title="Horizontal Displacement"),
            yaxis=dict(title="TVD", autorange="reversed"),
            margin=dict(l=0, r=0, b=0, t=0),
        )
        fig2d = go.Figure(data=[well_2d_trace, targets_2d_trace], layout=layout2d)

        st.plotly_chart(fig2d)

    # 3D
    well_3d_trace = go.Scatter3d(
        x=well_data["X"],
        y=well_data["Y"],
        z=well_data["Z"],
        mode="lines",
        line=dict(color="rgba(0,0,100,0.7)", width=10),
        name="Well Path",
    )
    targets_3d_trace = go.Scatter3d(
        x=targets_coords["X"],
        y=targets_coords["Y"],
        z=targets_coords["Z"],
        mode="markers",
        marker=dict(size=10, color="red"),
        name="Targets",
    )

    layout3d = go.Layout(
        scene=dict(
            xaxis=dict(title="Eastings"),
            yaxis=dict(title="Northings"),
            zaxis=dict(title="TVD", autorange="reversed"),
        ),
        scene_camera=dict(
            up=dict(x=0, y=0, z=1),
            center=dict(x=0, y=0, z=0),
            eye=dict(x=0.7, y=2, z=0.7),
        ),
        margin=dict(l=0, r=0, b=0, t=0),
    )
    fig3d = go.Figure(data=[well_3d_trace, targets_3d_trace], layout=layout3d)

    with st.container():
        st.subheader("Three Dimensional[3D]")
        st.plotly_chart(fig3d, use_container_width=True)

    with st.expander("View Well Data"):
        st.dataframe(well_data)


def best_choices(tool, tool_selection_instance):
    """
    Takes a DrillString or DrillPipe Instance and creates a streamlit display for choosing
    """
    num = st.sidebar.number_input(
        f"Number of best Drill {tool.capitalize()}:", 1, 30, 5, 1
    )
    selected = tool_selection_instance.get_optimum(num)
    best = selected[f"Best {tool}"]

    best_choices = []
    for idx, _tool in enumerate(best):
        try:
            toolname = str(idx) + " " + _tool.more_info()["Grade"]
        except KeyError:
            toolname = str(idx) + " slick " + _tool.more_info()["Connection"]
        best_choices.append(toolname)

    return best, best_choices


def list_card(title, lst=None, bg_color="lavender", height=160, text_position="center"):
    lst_items = ""
    for ls, val in lst:
        lst_items += f"<li style='list-style: none'>{ls}: <span style='padding: 1px; background-color: black; border-radius: 5px; color: white'>{val}</span></li>"

    st.markdown(
        f"""
        <div class="card" style="background-color: {bg_color}; width: 100%; height: {height}px; text-align: {text_position}; margin: 2px; margin-top: 5px;">
            <h5>{title}</h5>
            <ul style="text-align: left">
                {lst_items}
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def drillstring():
    while True:
        info = st.empty()
        try:
            selected_drillpipes = st.session_state.selected_drillpipes
            selected_drillcollars = st.session_state.selected_drillcollars
            break
        except AttributeError:
            with info.container:
                st.markdown(
                    "Computing the best Drill string and collars for the path generated..."
                )

    best_collar_ins, best_collar_strings = best_choices(
        "collars", selected_drillcollars
    )
    current_drillcollar = st.sidebar.radio("Select Drill Collar", best_collar_strings)

    best_pipe_ins, best_pipe_strings = best_choices("strings", selected_drillpipes)
    current_drillpipe = st.sidebar.radio("Select DrillPipe", best_pipe_strings)

    st.markdown("---")

    chosen_collar_idx = int(current_drillcollar.split(" ")[0])
    chosen_collar = best_collar_ins[chosen_collar_idx]
    chosen_collar_data = chosen_collar.more_info()

    chosen_string_idx = int(current_drillpipe.split(" ")[0])
    chosen_pipe = best_pipe_ins[chosen_string_idx]
    chosen_pipe_data = chosen_pipe.more_info()

    st.session_state.drillpipe = chosen_pipe
    st.session_state.drillcollar = chosen_collar

    chosen_collar_id = "Slick" + chosen_collar_data["Connection"]
    st.markdown(f"Drill Collar: <b>{chosen_collar_id}</b>", unsafe_allow_html=True)
    cc1, cc2, cc3 = st.columns(3)

    dcid = chosen_collar_data["collar_inner_diameter"]
    dcod = chosen_collar_data["collar_outer_diameter"]
    dcconnection = chosen_collar_data["Connection"]
    dctype = chosen_collar_data["Type"]
    dcaw = chosen_collar_data["weight"]
    dcmutmin = chosen_collar_data["MUT Min (ft-lbs)"]
    dcmutmax = chosen_collar_data["MUT Max (ft-lbs)"]

    with cc1:
        lst = [("Collar ID (in)", dcid), ("Collar OD (in)", dcod)]
        list_card(title="Diameters", lst=lst, bg_color="lavender")

    with cc2:
        lst = [("Adjusted Weight (lb/ft)", dcaw)]
        list_card(title="Weights", lst=lst, bg_color="lavender")

    with cc3:
        lst = [
            ("Type", dctype),
            ("Connection", dcconnection),
            ("MUT Min (ft-lbs)", dcmutmin),
            ("MUT Max (ft-lbs)", dcmutmax),
        ]
        list_card(title="Other", lst=lst, bg_color="lavender")

    chosen_pipe_id = chosen_pipe_data["Grade"]
    st.markdown(f"Drill Pipe: <b>{chosen_pipe_id}</b>", unsafe_allow_html=True)
    cp1, cp2, cp3 = st.columns(3)

    cpnw = chosen_pipe_data["pipe_weight"]
    cpod = chosen_pipe_data["pipe_outer_diameter"]
    cptubeid = chosen_pipe_data["pipe_inner_diameter"]
    cpconnection = chosen_pipe_data["Connection"]
    cprange = chosen_pipe_data["Range"]
    cpwall = chosen_pipe_data["Wall (in)"]
    cpadjusted_weight = chosen_pipe_data["Adjusted Weight (lb/ft)"]
    cptjod = chosen_pipe_data["TJ OD (in)"]
    cptjid = chosen_pipe_data["TJ ID (in)"]
    cptjyield = chosen_pipe_data["TJ YIELD (ft-lbs)"]
    cpmutmin = chosen_pipe_data["MUT Min (ft-lbs)"]
    cpmutmax = chosen_pipe_data["MUT Max (ft-lbs)"]
    cpptt = chosen_pipe_data["Prem Tube Tensile (lbs)"]
    with cp1:
        lst = [
            ("Pipe ID", cptubeid),
            ("Pipe OD", cpod),
            ("TJ OD", cptjod),
            ("TJ ID", cptjid),
        ]
        list_card(title="Diameters", lst=lst, bg_color="lavender", height=270)

    with cp2:
        lst = [
            ("Norminal Weight (lb/ft)", cpnw),
            ("Adjusted Weight (lb/ft)", cpadjusted_weight),
        ]
        list_card(title="Weights", lst=lst, bg_color="lavender", height=270)

    with cp3:
        lst = [
            ("Connection", cpconnection),
            ("Range", cprange),
            ("Wall (in)", cpwall),
            ("TJ YIELD (ft-lbs)", cptjyield),
            ("MUT Min (ft-lbs)", cpmutmin),
            ("MUT Max(ft-lbs)", cpmutmax),
            ("Prem Tube Tensile(lbs)", cpptt),
        ]
        list_card(title="Other", lst=lst, bg_color="lavender", height=270)

    st.markdown("---")

    # with st.expander("Collar properties along well path"):
    #     collar_properties = pd.DataFrame(
    #         {
    #             "Buckle": chosen_collar.buckles,
    #         },
    #         columns=["Buckle"],
    #     )
    #     st.dataframe(collar_properties)

    # with st.expander("Pipe properties along well path"):
    #     pipe_properties = pd.DataFrame(
    #         {
    #             "Torque": chosen_pipe.torques,
    #             "Drag": chosen_pipe.drags,
    #             "Buckle": chosen_pipe.buckles,
    #         },
    #         columns=["Torque", "Drag", "Buckle"],
    #     )
    #     st.dataframe(pipe_properties)


def display_simulated_graph():
    plan_data, target_coords = st.session_state.gen_well.output_data
    rss_data = st.session_state.cumulating_rss_data

    targets_3d_trace = go.Scatter3d(
        x=target_coords["X"],
        y=target_coords["Y"],
        z=target_coords["Z"],
        mode="markers",
        marker=dict(size=7, color="red"),
        name="Targets",
    )

    plan_3d_trace = go.Scatter3d(
        x=plan_data["X"],
        y=plan_data["Y"],
        z=plan_data["Z"],
        mode="lines",
        line=dict(color="rgba(0,0,100,0.7)", width=10),
        name="Plan",
        hovertemplate="X: %{x}<br>Y: %{y}<br>Z: %{z}, <br>Incl: %{incl}, <br>Azi: %{azi}, <br>MD: %{md}",
    )

    sim_3d_trace = go.Scatter3d(
        x=[station.coordinates[0] for station in rss_data],
        y=[station.coordinates[1] for station in rss_data],
        z=[station.coordinates[2] for station in rss_data],
        mode="lines",
        line=dict(color="green", width=11),
        name="RSS Simulation",
    )

    layout3d = go.Layout(
        scene=dict(
            xaxis=dict(title="Eastings"),
            yaxis=dict(title="Northings"),
            zaxis=dict(title="TVD", autorange="reversed"),
        ),
        scene_camera=dict(
            up=dict(x=0, y=0, z=1),
            center=dict(x=0, y=0, z=0),
            eye=dict(x=0.7, y=2, z=0.7),
        ),
        margin=dict(l=0, r=0, b=0, t=0),
    )

    fig = go.Figure(
        data=[targets_3d_trace, plan_3d_trace, sim_3d_trace],
        layout=layout3d,
    )

    st.plotly_chart(fig)


def display_parameters():
    data = st.session_state.cumulating_rss_data
    target = st.session_state.rss_current_target
    target_distance_away = st.session_state.target_distance_away
    try:
        pre_data = data[-2]
    except IndexError:
        pre_data = SimulatedStation((0, 0, 0), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    wob = data[-1].wob
    delta_wob = wob - pre_data.wob
    wob_decrease = wob < pre_data.wob

    rpm = data[-1].rpm
    delta_rpm = rpm - pre_data.rpm
    rpm_decrease = rpm < pre_data.rpm
    delta_rpm = -delta_rpm if rpm_decrease else delta_rpm
    delta_md = data[-1].md - pre_data.md

    st.metric(
        "Down Hole WOB",
        f"{wob:.1f} lbs",
        f"{'-' if wob_decrease else ''}{delta_wob * 10 / delta_md:.2f} lbs per 10 feet",
    )
    st.markdown(
        """<hr style='border-top: 2px solid rgba(0,0,0,1);'>""",
        unsafe_allow_html=True,
    )
    st.metric(
        "RPM",
        f"{rpm:.1f} rpm",
        f"{'-' if rpm_decrease else ''}{delta_rpm * 10 / delta_md:.2f} rev/min per 10 ft",
    )
    st.markdown(
        """<hr style='border-top: 2px solid rgba(0,0,0,1);'>""",
        unsafe_allow_html=True,
    )
    st.metric("CURRENT TARGET", target, f"-{target_distance_away:.3f} feet away")


def display_current_sim(sim_placeholder, buckling_placeholder, tob_placeholder):
    try:
        rss_data = st.session_state.cumulating_rss_data
    except AttributeError:
        rss_data = None
    with sim_placeholder.container():
        col1, col2, col3 = st.columns((6, 1.5, 1))

        with col1:
            display_simulated_graph()
        with col2:
            display_parameters()
        with col3:
            plot_rop()

    with buckling_placeholder.container():
        buckling = 0 if rss_data is None else rss_data[-1].buckling
        buckling = 0 if np.isnan(buckling) else buckling

        buckling_intensity = (
            "primary"
            if buckling < st.session_state.drillpipe._buckling_force(1000)
            else "danger"
        )  # NOTE: Axial force should not be dtermined here
        st.markdown(
            f"<span class='btn alert alert-{buckling_intensity}'><b>Buckling</b>: <br> {buckling:.2f}<span>",
            unsafe_allow_html=True,
        )

    with tob_placeholder.container():
        tob = 0 if rss_data is None else rss_data[-1].tob
        st.markdown(
            f"<span class='btn alert alert-primary'><b>TOB</b>: <br>{tob:.2f} ft-lbs<span>",
            unsafe_allow_html=True,
        )


def plot_rop():
    data = st.session_state.cumulating_rss_data
    rop = [station.rop_axial for station in data]
    md = [station.md for station in data]

    line_chart = go.Scatter(
        x=rop,
        y=md,
        mode="lines",
        line=dict(color="blue", width=1),
        # marker=dict(color="blue", size=3),
    )
    layout = go.Layout(
        margin=dict(t=0),
        width=150,
        xaxis=dict(title="ROP"),
        yaxis=dict(title="MD", autorange="reversed"),
    )
    fig = go.Figure(data=[line_chart], layout=layout)
    st.plotly_chart(fig)


def simulation_display():
    plan_data, target_coords = st.session_state.gen_well.output_data

    c0, c1, c2, c3, c4, c5 = st.columns((2, 2, 2, 1.5, 2, 2))
    with c0:
        st.button(
            "Play Simulation",
            on_click=change_simulation_state,
            args=("play",),
        )
    with c1:
        st.button(
            "Pause Simulation",
            on_click=change_simulation_state,
            args=("pause",),
        )
    with c2:
        st.button(
            "Restart Simulation",
            on_click=change_simulation_state,
            args=("restart",),
        )
    with c3:
        simulation_state = st.session_state.simulation_condition
        if simulation_state == "Restarted":
            with st.spinner("Restarting..."):
                time.sleep(2)
            st.session_state.simulation_condition = "Running"

        simulation_state = st.session_state.simulation_condition
        if simulation_state == "Paused":
            simulation_state_color = "yellow"
        elif simulation_state == "Running":
            simulation_state_color = "green"
        else:
            simulation_state_color = "red"
        state_placeholder = st.empty()
        with state_placeholder:
            st.markdown(
                f"<span style='color: {simulation_state_color}'>{simulation_state}...</span>",
                unsafe_allow_html=True,
            )
    with c4:
        buckling_placeholder = st.empty()
        with buckling_placeholder.container():
            st.markdown(
                "<span style='font-size: 20px' class='btn alert alert-primary'><b>Buckling</b>: 0<span>",
                unsafe_allow_html=True,
            )
            pass
    with c5:
        tob_placeholder = st.empty()
        with tob_placeholder.container():
            st.markdown(
                "<span style='font-size: 20px' class='btn alert alert-primary'><b>TOB</b>: 0 ft-lbs<span>",
                unsafe_allow_html=True,
            )

    simulation_display_placeholder = st.empty()
    if st.session_state.simulation_state == "pause":
        display_current_sim(
            simulation_display_placeholder, buckling_placeholder, tob_placeholder
        )

    if st.session_state.simulation_state == "restart":
        st.session_state.rss_current_target = 1
        st.session_state.target_distance_away = target_coords["Z"].iloc[-1]
        st.session_state.rss_generator_data = RSSDataGenerator(
            plan=plan_data,
            drillcollar=st.session_state.drillcollar,
            drillpipe=st.session_state.drillpipe,
            t_delta=150,
        ).data()
        st.session_state.cumulating_rss_data.clear()

        st.session_state.simulation_state = "play"
        st.session_state.simulation_condition = "Restarted"

    if st.session_state.simulation_state == "play":
        while True:
            try:
                st.session_state.cumulating_rss_data.append(
                    next(st.session_state.rss_generator_data)
                )

                last_coordinate = st.session_state.cumulating_rss_data[-1].coordinates

                for idx, t in enumerate(target_coords.itertuples(index=False)):
                    if t[-1] >= last_coordinate[-1]:
                        st.session_state.rss_current_target = idx + 1
                        st.session_state.target_distance_away = (
                            t[-1] - last_coordinate[-1]
                        )
                        break

                time.sleep(0.08)

            except StopIteration:
                st.session_state.target_distance_away = 0
                namedtuple_data = st.session_state.cumulating_rss_data
                simulation_data = pd.DataFrame([i._asdict() for i in namedtuple_data])

                with state_placeholder:
                    st.markdown(
                        f"<span style='color: {simulation_state_color}'>Simulation Complete!🥳</span>",
                        unsafe_allow_html=True,
                    )

                st.dataframe(simulation_data)
                break

            display_current_sim(
                simulation_display_placeholder, buckling_placeholder, tob_placeholder
            )

    st.markdown(
        """
            <style>
            /*center metric label*/
            [data-testid="stMetricLabel"] > div:nth-child(1) {
                justify-content: center;
            }

            /*center metric value*/
            [data-testid="stMetricValue"] > div:nth-child(1) {
                justify-content: center;
            }
            </style>
            """,
        unsafe_allow_html=True,
    )


def change_simulation_state(action):
    st.session_state.simulation_state = action

    if action == "play":
        st.session_state.simulation_state = "play"

        if st.session_state.first_run:
            st.session_state.rss_generator_data = RSSDataGenerator(
                plan=st.session_state.gen_well.output_data[0],
                drillpipe=st.session_state.drillpipe,
                drillcollar=st.session_state.drillcollar,
                t_delta=120,
            ).data()
            st.session_state.first_run = False

        st.session_state.simulation_condition = "Running"

    if action == "restart":
        st.session_state.simulation_state = "restart"
        st.session_state.simulation_condition = "Restarted"

    if action == "pause":
        st.session_state.simulation_state = "pause"
        st.session_state.simulation_condition = "Paused"


def prepare_drillstring_choice():
    well_data = st.session_state.gen_well.output_data[0]
    selected_drillpipes = selected_drill_pipes(
        well_data=well_data,
        friction_co=0.2,
        string_force=324,
        youngs_modulus=30000000,
        inner_mud_weight=15,
        outer_mud_weight=7.3,
        hole_diameter=10,
        internal_fluid_pressure=12800,
        external_fluid_pressure=4790,
        buoyancy_factor=0.8,
    )

    selected_drillcollars = selected_drill_collars(
        well_data=well_data,
        youngs_modulus=30000000,
        inner_mud_weight=15,
        outer_mud_weight=7.3,
        hole_diameter=10,
    )

    st.session_state.selected_drillpipes = selected_drillpipes
    st.session_state.selected_drillcollars = selected_drillcollars


st.markdown(
    '<link href="https://cdnjs.cloudflare.com/ajax/libs/mdbootstrap/4.19.1/css/mdb.css" rel="stylesheet">',
    unsafe_allow_html=True,
)
st.markdown(
    '<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">',
    unsafe_allow_html=True,
)
st.markdown("""""", unsafe_allow_html=True)
st.markdown(
    """
    <nav class="navbar fixed-top navbar-expand-lg navbar-dark" style="background-color: #4267B2;">
    <a class="navbar-icon"><img src="https://i.ibb.co/80hrpMB/UMaX.png" alt="UMaX" border="0" style="width:50px"></a>
    <a class="navbar-brand" href="#"  target="_blank">UMaX Simulator</a>
   
    </nav>
""",
    unsafe_allow_html=True,
)
hide_streamlit_style = """
            <style>
    
                header{visibility:hidden;}
                .main {
                    margin-top: -120px;
                    padding-top:10px;
                }
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}

            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)


def streamlit_menu():
    selected = option_menu(
        menu_title=None,  # required
        options=["Well Plan", "Drill String", "Simulation"],  # required
        icons=["house", "pencil", "play"],  # optional
        menu_icon="cast",  # optional
        default_index=0,  # optional
        orientation="horizontal",
        styles={
            "nav-link-selected": {"background-color": "#4267B2"},
        },
    )

    return selected


selected = streamlit_menu()

if selected == "Well Plan":
    inputted_data = well_inputs()

    if st.sidebar.button("Run"):
        st.session_state.ENTERED_DATA = True

    if st.session_state.ENTERED_DATA:
        setup_well(inputted_data)
        prepare_drillstring_choice()
        disp_plan()

    else:
        st.header("Enter well data in the side bar and click run")

if selected == "Drill String":
    try:
        well_data = st.session_state.gen_well.output_data[0]
        drillstring()
        st.sidebar.button("Select this Drillstring")
    except TypeError:
        st.header("Generate well path before!")
    except IndexError:
        st.header("Generate well path before!")

if selected == "Simulation":
    try:
        simulation_display()

    except IndexError:
        st.header("Generate well path before!")
