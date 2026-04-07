"""
Absurd Viscosity Calculator

"What if we measured viscosity by dropping a Boeing 747 into a giant
tube of mystery fluid?"

Uses Stokes' Law with any object  - aircraft, cars, birds, whales,
shopping trolleys  - you name it. Pick a preset or enter your own.

Stokes' Law:  n = 2*r^2*(rho_obj - rho_fluid)*g / (9*v_terminal)

Objects are approximated as equivalent spheres (same volume -> effective
radius). This is wildly inaccurate for non-spherical objects, which is
entirely the point.
"""

import math

G = 9.81  # m/s^2

# ---------------------------------------------------------------
# Preset objects: (name, mass_kg, approx_volume_m3, fun_fact)
# ---------------------------------------------------------------
PRESETS = {
    # Aircraft
    "1":  ("Boeing 747-400",        178_756,    876.0,
           "You'd need a tube ~68 m wide and filled with something\n"
           "           thicker than peanut butter to even slow this down."),
    "2":  ("Airbus A380",           276_800,    1_570.0,
           "The A380's cabin volume alone is ~550 m^3  - it IS the tube."),
    "3":  ("Cessna 172",            1_111,      8.8,
           "The most produced aircraft ever. Now it's a viscometer."),
    "4":  ("F-16 Fighting Falcon",  12_000,     30.0,
           "Mach 2 in air... about 0.003 km/h in honey."),
    "5":  ("Chinook Helicopter",    12_200,     210.0,
           "Those rotors won't help in treacle."),

    # Land vehicles
    "6":  ("Ford Transit Van",      2_600,      12.5,
           "White van man meets fluid dynamics."),
    "7":  ("London Double-Decker",  12_650,     72.0,
           "The Routemaster: iconic on roads, useless in custard."),
    "8":  ("Tesla Cybertruck",      3_100,      10.2,
           "Elon didn't account for this use case."),
    "9":  ("Formula 1 Car",         798,        3.5,
           "0-100 in 2.6 seconds. 100-0 in syrup: never."),
    "10": ("Monster Truck",         5_400,      38.0,
           "SUNDAY SUNDAY SUNDAY... in a vat of glycerol!"),

    # Animals
    "11": ("Emperor Penguin",       23,         0.023,
           "Hydrodynamic in water. Less so in molasses."),
    "12": ("Bald Eagle",            6.3,        0.007,
           "Freedom falls... slowly."),
    "13": ("Blue Whale",            150_000,    135.0,
           "Already lives in fluid. Now imagine it's maple syrup."),
    "14": ("African Elephant",      6_000,      6.5,
           "They say elephants never forget. They'll remember this."),
    "15": ("Chicken",               2.5,        0.003,
           "Why did the chicken cross the viscous fluid? It didn't."),

    # Miscellaneous
    "16": ("Grand Piano",           480,        2.2,
           "Dropping pianos: slapstick meets science."),
    "17": ("Shopping Trolley",      25,         0.5,
           "One wonky wheel isn't the problem anymore."),
    "18": ("Fridge",                90,         0.55,
           "Contents may have shifted during descent."),
    "19": ("Phone Box (UK)",        750,        2.8,
           "The TARDIS it is not."),
    "20": ("ISS (approx)",         420_000,     916.0,
           "Orbital velocity: 7.66 km/s. Velocity in treacle: no."),
}


def equivalent_radius(volume_m3):
    """Radius of a sphere with the same volume as the object."""
    return (3 * volume_m3 / (4 * math.pi)) ** (1 / 3)


def stokes_viscosity(radius_m, rho_obj, rho_fluid, fall_distance_m, fall_time_s):
    """Calculate dynamic viscosity using Stokes' Law. Returns Pa.s."""
    v_terminal = fall_distance_m / fall_time_s
    return (2 * radius_m ** 2 * (rho_obj - rho_fluid) * G) / (9 * v_terminal)


def stokes_terminal_velocity(radius_m, rho_obj, rho_fluid, viscosity):
    """Calculate terminal velocity for a known viscosity."""
    return (2 * radius_m ** 2 * (rho_obj - rho_fluid) * G) / (9 * viscosity)


def get_float(prompt):
    while True:
        try:
            val = float(input(prompt))
            if val <= 0:
                print("  Must be positive. Try again.")
                continue
            return val
        except ValueError:
            print("  Invalid number. Try again.")


def describe_viscosity(eta):
    """Return a humorous real-world comparison."""
    if eta < 0.001:
        return "thinner than water  - basically dropping it through air with extra steps"
    elif eta < 0.01:
        return "about as viscous as milk  - a gentle plop"
    elif eta < 0.1:
        return "olive oil territory  - a slow, dignified descent"
    elif eta < 1:
        return "engine oil / glycerol  - now we're getting sluggish"
    elif eta < 10:
        return "honey / golden syrup  - a proper ooze"
    elif eta < 100:
        return "ketchup / chocolate sauce  - barely moving"
    elif eta < 1000:
        return "peanut butter zone  - geological timescales"
    elif eta < 100_000:
        return "tar / bitumen  - come back next century"
    elif eta < 1_000_000:
        return "molten glass  - this thing isn't going anywhere"
    else:
        return "mantle of the Earth  - check back in a few million years"


def time_to_human(seconds):
    """Convert seconds to a human-readable string."""
    if seconds < 0.001:
        return f"{seconds*1e6:.2f} microseconds"
    if seconds < 1:
        return f"{seconds*1000:.2f} milliseconds"
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    if seconds < 3600:
        return f"{seconds/60:.2f} minutes"
    if seconds < 86400:
        return f"{seconds/3600:.2f} hours"
    if seconds < 365.25 * 86400:
        return f"{seconds/86400:.2f} days"
    if seconds < 365.25 * 86400 * 1000:
        return f"{seconds/(365.25*86400):.2f} years"
    if seconds < 365.25 * 86400 * 1e6:
        return f"{seconds/(365.25*86400*1000):.2f} millennia"
    return f"{seconds/(365.25*86400*1e9):.2f} billion years"


def print_presets():
    print("\n  AIRCRAFT:")
    for k in ["1","2","3","4","5"]:
        print(f"    [{k:>2}] {PRESETS[k][0]}")
    print("  LAND VEHICLES:")
    for k in ["6","7","8","9","10"]:
        print(f"    [{k:>2}] {PRESETS[k][0]}")
    print("  ANIMALS:")
    for k in ["11","12","13","14","15"]:
        print(f"    [{k:>2}] {PRESETS[k][0]}")
    print("  MISCELLANEOUS:")
    for k in ["16","17","18","19","20"]:
        print(f"    [{k:>2}] {PRESETS[k][0]}")
    print(f"    [ C] Custom object")


KNOWN_FLUIDS = [
    ("Water (20 degC)",           0.001,     998),
    ("Milk",                   0.003,     1033),
    ("Olive oil",              0.08,      911),
    ("Engine oil SAE 30",      0.2,       880),
    ("Glycerol (25 degC)",        0.95,      1261),
    ("Golden syrup",           5.0,       1440),
    ("Honey",                  5.0,       1420),
    ("Ketchup",               10.0,       1150),
    ("Chocolate sauce",       25.0,       1280),
    ("Peanut butter",        250.0,       1090),
    ("Tar / bitumen",      30000.0,       1150),
    ("Molten glass",      100000.0,       2500),
    ("Earth's mantle",     1e21,          4500),
]


def main():
    print("=" * 62)
    print("   ABSURD VISCOSITY CALCULATOR")
    print("   'What viscosity would you need to slow down a 747?'")
    print("=" * 62)

    while True:
        print("\n  Choose a mode:")
        print("    [A] Find viscosity  - drop an object, measure fall time")
        print("    [B] Find fall time  - pick an object AND a known fluid")
        print("    [Q] Quit")
        mode = input("\n  Mode: ").strip().upper()

        if mode == "Q":
            print("\n  Goodbye! No objects were harmed in this simulation.\n")
            break

        # ---- Select or define object ----
        print_presets()
        choice = input("\n  Select object: ").strip().upper()

        if choice == "C":
            print("\n  -- Custom Object --")
            obj_name = input("    Name: ").strip() or "Mystery Object"
            obj_mass = get_float("    Mass (kg): ")
            obj_vol = get_float("    Volume (m^3): ")
            fun_fact = "A custom object of mystery and wonder."
        elif choice in PRESETS:
            obj_name, obj_mass, obj_vol, fun_fact = PRESETS[choice]
        else:
            print("  Invalid choice.")
            continue

        obj_density = obj_mass / obj_vol
        obj_r = equivalent_radius(obj_vol)

        print(f"\n  Object:             {obj_name}")
        print(f"  Mass:               {obj_mass:,.2f} kg")
        print(f"  Volume:             {obj_vol:,.4f} m^3")
        print(f"  Density:            {obj_density:,.2f} kg/m^3")
        print(f"  Equivalent radius:  {obj_r:.4f} m  (sphere of same volume)")
        print(f"  Fun fact:           {fun_fact}")

        if mode == "A":
            # ---- MODE A: Calculate viscosity from fall observation ----
            print("\n  --- Fluid ---")
            fluid_mass = get_float("    Mass of fluid (kg): ")
            fluid_vol = get_float("    Volume of fluid (m^3): ")
            rho_fluid = fluid_mass / fluid_vol
            print(f"    -> Fluid density: {rho_fluid:.2f} kg/m^3")

            if obj_density <= rho_fluid:
                print(f"\n  The {obj_name} would FLOAT! (rho_obj={obj_density:.1f}"
                      f" <= rho_fluid={rho_fluid:.1f})")
                print("  Viscosity cannot be determined  - object never sinks.")
                continue

            fall_dist = get_float("    Fall distance (m): ")
            fall_time = get_float("    Fall time (s): ")

            eta = stokes_viscosity(obj_r, obj_density, rho_fluid, fall_dist, fall_time)

            print(f"\n{'='*62}")
            print(f"  RESULT")
            print(f"{'='*62}")
            print(f"  Viscosity: {eta:.6f} Pa.s")
            print(f"  That's {describe_viscosity(eta)}.")
            print(f"{'='*62}")

        elif mode == "B":
            # ---- MODE B: Pick a known fluid, calculate what would happen ----
            print("\n  --- Pick a fluid ---")
            for idx, (fname, feta, frho) in enumerate(KNOWN_FLUIDS, 1):
                print(f"    [{idx:>2}] {fname:<22}  n={feta:<12.4f} Pa.s   rho={frho} kg/m^3")
            print(f"    [ C] Custom fluid")

            fchoice = input("\n  Select fluid: ").strip().upper()
            if fchoice == "C":
                fname = input("    Fluid name: ").strip() or "Mystery Fluid"
                feta = get_float("    Viscosity (Pa.s): ")
                frho = get_float("    Density (kg/m^3): ")
            elif fchoice.isdigit() and 1 <= int(fchoice) <= len(KNOWN_FLUIDS):
                fname, feta, frho = KNOWN_FLUIDS[int(fchoice) - 1]
            else:
                print("  Invalid choice.")
                continue

            if obj_density <= frho:
                print(f"\n  The {obj_name} would FLOAT in {fname}!")
                print(f"  (rho_obj={obj_density:.1f} <= rho_fluid={frho:.1f})")
                continue

            fall_dist = get_float("    Fall distance (m): ")

            v_term = stokes_terminal_velocity(obj_r, obj_density, frho, feta)
            fall_time = fall_dist / v_term

            # Reynolds number check
            re = (frho * v_term * 2 * obj_r) / feta if feta > 0 else float("inf")

            print(f"\n{'='*62}")
            print(f"  SCENARIO: {obj_name} dropped into {fname}")
            print(f"{'='*62}")
            print(f"  Terminal velocity:   {v_term:.6e} m/s")

            if v_term > 0.001:
                print(f"                       ({v_term*3.6:.4f} km/h)")
            elif v_term > 1e-9:
                print(f"                       ({v_term*1000:.6f} mm/s)")
            else:
                print(f"                       (essentially stationary)")

            print(f"  Time to fall {fall_dist:.1f} m:  {time_to_human(fall_time)}")
            print(f"  Reynolds number:     {re:.4f}", end="")
            if re < 1:
                print("  (laminar - Stokes' Law valid)")
            elif re < 1000:
                print("  (transitional - Stokes' Law approximate)")
            else:
                print("  (turbulent - Stokes' Law NOT valid here!)")
                print("  (Real drag would be much higher - it'd actually")
                print("   fall faster than Stokes predicts at low n,")
                print("   slower at high n due to turbulent drag.)")

            print(f"\n  {describe_viscosity(feta).capitalize()}.")

            # Bonus comparisons
            print(f"\n  --- For perspective ---")
            if fall_time > 365.25 * 86400:
                print(f"  In the time it takes to fall {fall_dist:.1f} m,")
                print(f"  light would travel {fall_time * 299_792_458 / 9.461e15:.2f} light-years.")
            if fall_time > 3600:
                cups_of_tea = fall_time / 240
                print(f"  You could brew {cups_of_tea:,.0f} cups of tea while waiting.")
            if v_term > 0 and v_term < 1e-6:
                print(f"  A snail (0.001 m/s) would outpace it by {0.001/v_term:,.0f}x.")
            print(f"{'='*62}")

        else:
            print("  Invalid mode.")


if __name__ == "__main__":
    main()
