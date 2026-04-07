"""
Fluid Viscosity Calculator using Stokes' Law (Falling Ball Method)

Calculates dynamic viscosity from three groups of ball bearings (small,
medium, large) with 3 bearings per group dropped through a fluid.

For each size group the mean density is calculated from the 3 bearings
and used in the Stokes' Law viscosity calculation.

Stokes' Law:  n = 2*r^2*(rho_ball - rho_fluid)*g / (9*v_terminal)

Inputs:
  - Mass and diameter of 3 bearings per size group (x3 groups)
  - Mass and volume of the fluid
  - Fall distance and fall time for each bearing

Outputs:
  - Volume and density of each bearing
  - Mean density per size group
  - Density of fluid (from mass and volume)
  - Viscosity estimate from each bearing and each group
  - Overall average viscosity with standard deviation
"""

import math


G = 9.81  # gravitational acceleration (m/s^2)

SIZE_LABELS = ["Small", "Medium", "Large"]


def bearing_volume(diameter_m):
    """Calculate sphere volume from diameter in metres."""
    r = diameter_m / 2
    return (4 / 3) * math.pi * r ** 3


def fluid_density(mass_kg, volume_m3):
    """Calculate fluid density (kg/m^3)."""
    if volume_m3 <= 0:
        raise ValueError("Fluid volume must be positive.")
    return mass_kg / volume_m3


def stokes_viscosity(radius_m, rho_ball, rho_fluid, fall_distance_m, fall_time_s):
    """Calculate dynamic viscosity using Stokes' Law. Returns Pa.s."""
    if fall_time_s <= 0:
        raise ValueError("Fall time must be positive.")
    if fall_distance_m <= 0:
        raise ValueError("Fall distance must be positive.")

    v_terminal = fall_distance_m / fall_time_s
    return (2 * radius_m ** 2 * (rho_ball - rho_fluid) * G) / (9 * v_terminal)


def get_float(prompt):
    """Prompt the user for a positive float value."""
    while True:
        try:
            val = float(input(prompt))
            if val <= 0:
                print("  Value must be positive. Try again.")
                continue
            return val
        except ValueError:
            print("  Invalid number. Try again.")


def main():
    print("=" * 60)
    print("   FLUID VISCOSITY CALCULATOR  (Stokes' Law)")
    print("=" * 60)

    # ---- Fluid properties ----
    print("\n--- Fluid Properties ---")
    fluid_mass = get_float("  Mass of fluid (kg): ")
    fluid_vol = get_float("  Volume of fluid (m^3): ")
    rho_fluid = fluid_density(fluid_mass, fluid_vol)
    print(f"  -> Fluid density: {rho_fluid:.4f} kg/m^3")

    # ---- Fall distance ----
    print("\n--- Fall Distance ---")
    fall_distance = get_float("  Fall distance in fluid (m): ")

    # ---- Ball bearing groups ----
    BEARINGS_PER_GROUP = 3
    all_viscosities = []
    group_results = []

    for size in SIZE_LABELS:
        print(f"\n{'='*60}")
        print(f"   {size.upper()} BEARINGS")
        print(f"{'='*60}")

        bearings = []
        for j in range(1, BEARINGS_PER_GROUP + 1):
            print(f"\n  -- {size} Bearing #{j} --")
            mass = get_float(f"    Mass (kg): ")
            diameter = get_float(f"    Diameter (m): ")
            fall_time = get_float(f"    Fall time (s): ")

            vol = bearing_volume(diameter)
            density = mass / vol

            print(f"    -> Volume:  {vol:.6e} m^3")
            print(f"    -> Density: {density:.2f} kg/m^3")

            bearings.append({
                "num": j,
                "mass_kg": mass,
                "diameter_m": diameter,
                "volume_m3": vol,
                "density_kgm3": density,
                "fall_time_s": fall_time,
            })

        # Mean density for this size group
        mean_density = sum(b["density_kgm3"] for b in bearings) / BEARINGS_PER_GROUP
        print(f"\n  -> Mean {size.lower()} bearing density: {mean_density:.2f} kg/m^3")

        # Calculate viscosity for each bearing using the group mean density
        for b in bearings:
            radius = b["diameter_m"] / 2
            eta = stokes_viscosity(radius, mean_density, rho_fluid, fall_distance, b["fall_time_s"])
            b["viscosity_pas"] = eta
            all_viscosities.append(eta)
            print(f"     Bearing #{b['num']}: viscosity = {eta:.6f} Pa.s")

        group_avg = sum(b["viscosity_pas"] for b in bearings) / BEARINGS_PER_GROUP
        print(f"  -> Mean {size.lower()} viscosity: {group_avg:.6f} Pa.s")

        group_results.append({
            "size": size,
            "mean_density": mean_density,
            "mean_viscosity": group_avg,
            "bearings": bearings,
        })

    # ---- Overall summary ----
    overall_avg = sum(all_viscosities) / len(all_viscosities)
    overall_std = math.sqrt(sum((v - overall_avg) ** 2 for v in all_viscosities) / len(all_viscosities))

    print(f"\n{'='*60}")
    print("   RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"  Fluid density:       {rho_fluid:.4f} kg/m^3")
    print(f"  Fall distance:       {fall_distance} m")
    print()
    print(f"  {'Group':<10} {'Mean rho (kg/m^3)':<18} {'Mean n (Pa.s)':<16}")
    print(f"  {'-'*10} {'-'*18} {'-'*16}")
    for g in group_results:
        print(f"  {g['size']:<10} {g['mean_density']:<18.2f} {g['mean_viscosity']:<16.6f}")
    print()
    print(f"  Overall average viscosity:  {overall_avg:.6f} Pa.s")
    print(f"  Standard deviation:         {overall_std:.6f} Pa.s")
    print(f"  Relative std dev:           {(overall_std / overall_avg * 100) if overall_avg != 0 else 0:.2f}%")
    print(f"{'='*60}")

    # ---- Group comparison ----
    print(f"\n{'='*60}")
    print("   GROUP COMPARISON")
    print(f"{'='*60}")

    viscosities_by_group = [g["mean_viscosity"] for g in group_results]
    min_v = min(viscosities_by_group)
    max_v = max(viscosities_by_group)
    spread = max_v - min_v
    spread_pct = (spread / overall_avg * 100) if overall_avg != 0 else 0

    print(f"\n  Spread across groups:  {spread:.6f} Pa.s ({spread_pct:.2f}%)")
    print()

    if spread_pct < 5:
        print("  All three bearing sizes produced consistent results.")
        print("  This suggests the fluid is behaving as a Newtonian fluid")
        print("  and Stokes' Law is a good model at these conditions.")
    elif spread_pct < 15:
        print("  Moderate variation between groups detected.")
        print("  Possible causes:")
        print("    - Bearings not reaching terminal velocity before measurement")
        print("    - Wall effects (tube diameter too close to bearing size)")
        print("    - Slight non-Newtonian behaviour at different shear rates")
    else:
        print("  Significant variation between groups detected.")
        print("  The fluid may be non-Newtonian (viscosity depends on shear")
        print("  rate), or experimental error is present. Larger bearings fall")
        print("  faster and impose higher shear rates on the fluid.")

    # Show which group gave highest/lowest
    sorted_groups = sorted(group_results, key=lambda g: g["mean_viscosity"])
    print(f"\n  Lowest  viscosity: {sorted_groups[0]['size']:<8} ({sorted_groups[0]['mean_viscosity']:.6f} Pa.s)")
    print(f"  Highest viscosity: {sorted_groups[-1]['size']:<8} ({sorted_groups[-1]['mean_viscosity']:.6f} Pa.s)")

    if sorted_groups[-1]["mean_viscosity"] > sorted_groups[0]["mean_viscosity"] * 1.1:
        if sorted_groups[-1]["size"] == "Small":
            print("\n  Smaller bearings gave higher viscosity -> they fall slower")
            print("  relative to their size, experiencing lower shear rates.")
            print("  This pattern is typical of shear-thinning fluids (e.g.")
            print("  ketchup, paint, blood, polymer solutions).")
        elif sorted_groups[-1]["size"] == "Large":
            print("\n  Larger bearings gave higher viscosity -> possible wall")
            print("  effects or the bearings may not have reached terminal")
            print("  velocity. Check tube-to-bearing diameter ratio (should")
            print("  be at least 10:1).")

    # ---- Real-world comparison ----
    print(f"\n{'='*60}")
    print("   REAL-WORLD VISCOSITY COMPARISON")
    print(f"{'='*60}")

    KNOWN_FLUIDS = [
        ("Air (20 degC)",              0.000018),
        ("Water (20 degC)",            0.001),
        ("Mercury (20 degC)",          0.00155),
        ("Olive oil (20 degC)",        0.08),
        ("Engine oil SAE 30",       0.2),
        ("Glycerol (25 degC)",         0.95),
        ("Golden syrup",            5.0),
        ("Honey (20 degC)",            5.0),
        ("Ketchup",                10.0),
        ("Peanut butter",         250.0),
        ("Tar / bitumen (20 degC)", 30000.0),
    ]

    print(f"\n  {'Fluid':<25} {'n (Pa.s)':<14} {'vs. your result'}")
    print(f"  {'-'*25} {'-'*14} {'-'*20}")
    closest_name = ""
    closest_diff = float("inf")
    for name, eta in KNOWN_FLUIDS:
        if overall_avg != 0:
            ratio = eta / overall_avg
            label = f"{ratio:.2f}x"
        else:
            label = "N/A"
        print(f"  {name:<25} {eta:<14.6f} {label}")
        diff = abs(math.log10(eta + 1e-30) - math.log10(overall_avg + 1e-30))
        if diff < closest_diff:
            closest_diff = diff
            closest_name = name

    print(f"\n  Your fluid (n = {overall_avg:.6f} Pa.s) is closest to: {closest_name}")

    # ---- Applications ----
    print(f"\n{'='*60}")
    print("   REAL-WORLD APPLICATIONS")
    print(f"{'='*60}")

    if overall_avg < 0.001:
        print("""
  Your fluid has very low viscosity (thinner than water).
  Applications for low-viscosity fluids:
    - Hydraulic systems requiring fast response
    - Inkjet printing
    - Fuel injection systems
    - Cooling systems (heat transfer fluids)
    - Cleaning solvents and degreasers""")
    elif overall_avg < 0.1:
        print("""
  Your fluid has low-to-moderate viscosity (water to light oil).
  Applications:
    - Lubrication of light machinery and bearings
    - Food processing (beverages, sauces)
    - Pharmaceutical coatings and suspensions
    - Cosmetics (lotions, light creams)
    - Agricultural sprays and pesticides""")
    elif overall_avg < 1.0:
        print("""
  Your fluid has moderate viscosity (oil to glycerol range).
  Applications:
    - Engine and gear lubrication
    - Damping fluids in shock absorbers
    - Coating and painting processes
    - Food production (syrups, dressings)
    - Drilling muds in oil/gas extraction""")
    elif overall_avg < 50:
        print("""
  Your fluid has high viscosity (syrup / honey range).
  Applications:
    - Adhesives and sealants
    - Thick food products (honey, caramel, chocolate)
    - Polymer processing and extrusion
    - Medical gels and ointments
    - Grease for heavy-duty bearings""")
    else:
        print("""
  Your fluid has very high viscosity (paste / tar range).
  Applications:
    - Road construction (asphalt / bitumen)
    - Heavy industrial adhesives
    - Glass manufacturing (molten glass)
    - Geological modelling (mantle convection)
    - Sealants for extreme environments""")

    print(f"\n{'='*60}")


if __name__ == "__main__":
    main()
