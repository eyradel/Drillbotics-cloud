def rop_tob_drillbotics(
    formation_aggressiveness,
    bit_aggressiveness_factor,
    WOB,
    RPM,
    Eff,
    D,
    CCS,
    side_force,
    side_cutting_factor,
):
    """
    This function predicts ROP, Lateral ROP of the bit, and Bit Torque.

    Output Variables, Units:
        - ROP: [ft/hr] (axial ROP)
        - ROPlateral: [ft/hr] (lateral ROP)
        - TOB: [ft-lbs] (bit torque)

    Input Variables, Units:
        - formation_aggressiveness: [] (drilling aggressiveness, Torque/WOB ratio
        which is heavily influenced by formation type. Based on paper by
        Pessier and Fear in SPE 24584 (1992). Contest will provide this.
        - bit_aggressiveness_factor: [] (range from 0.7 for unaggressive bits to
        1.3 for aggressive bits). Contestants or contest will choose a bit
        which will have an associated bit_aggressiveness_factor.
        - WOB: [lbs] (axial force on the bit)
        - RPM: [RPM] (revolutions per minute of the bit)
        - Eff: [] (drilling efficiency, usually 0.3 to 0.4)
        - D: [inches] (bit diameter)
        - CCS: [psi] (confined compressive strength of the rock)
        - side_force: [] (scaling factor for side cutting aggressiveness of the bit)

    Returns: ROP, ROPlateral, TOB
    """

    mu = formation_aggressiveness * bit_aggressiveness_factor
    ROP = (
        (13.33 * RPM * mu * WOB) * (Eff) / (D * CCS)
    )  # [ft/hr]; Derived from Teale MSE concept (1965).
    TOB = (
        D * (mu * WOB) / 36
    )  # [ft-lbs]; Derived from Pessier and Fear, SPE 24584 (1992).
    ROPlateral = side_cutting_factor * side_force * RPM / (D * CCS)  # [ft/hr]

    return ROP, ROPlateral, TOB
