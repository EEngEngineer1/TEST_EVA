"""
Industrial Electrical System Efficiency Analyzer

Interactive CLI tool for building a facility model from subsystems,
analysing total losses, costs, green alternatives, and savings.

Subsystem categories:
  1. Transformer          6. Compressed Air
  2. Industrial Motor     7. Data Centre / IT
  3. Pump                 8. VFD
  4. Chiller              9. Gas Boiler
  5. Lighting            10. Solar PV

Run:  python industrial_efficiency_analyzer.py
No external dependencies required.
"""

import math

# =============================================================================
#  CONSTANTS & PRESETS
# =============================================================================

CATEGORY_NAMES = {
    1: "Transformer",
    2: "Industrial Motor",
    3: "Pump",
    4: "Chiller",
    5: "Lighting",
    6: "Compressed Air",
    7: "Data Centre / IT",
    8: "VFD",
    9: "Gas Boiler",
    10: "Solar PV",
}

# Each preset: (label, dict of default params, upgrade_cost_per_unit $)
PRESETS = {
    1: [
        ("1000 kVA Oil-Filled",
         dict(rated_kva=1000, load_factor=75, no_load_loss_kw=1.7,
              full_load_loss_kw=10.5, hours=8760, qty=1), 35000),
        ("2000 kVA Dry-Type",
         dict(rated_kva=2000, load_factor=60, no_load_loss_kw=3.5,
              full_load_loss_kw=18.0, hours=8760, qty=1), 55000),
        ("500 kVA Pad-Mounted",
         dict(rated_kva=500, load_factor=80, no_load_loss_kw=1.0,
              full_load_loss_kw=6.0, hours=8760, qty=1), 22000),
    ],
    2: [
        ("75 kW IE2 Motor",
         dict(rated_kw=75, efficiency=93.6, load_factor=80, hours=6000, qty=4), 8500),
        ("15 kW IE1 Legacy Motor",
         dict(rated_kw=15, efficiency=88.0, load_factor=70, hours=6000, qty=10), 2800),
        ("200 kW IE3 Motor",
         dict(rated_kw=200, efficiency=96.0, load_factor=85, hours=6000, qty=2), 22000),
    ],
    3: [
        ("Centrifugal Pump 55 kW",
         dict(rated_kw=55, motor_eff=93, pump_eff=72, load_factor=80,
              hours=6000, qty=3), 15000),
        ("Submersible Pump 30 kW",
         dict(rated_kw=30, motor_eff=90, pump_eff=65, load_factor=70,
              hours=4000, qty=2), 9000),
    ],
    4: [
        ("Screw Chiller 200 kW",
         dict(cooling_kw=200, cop=4.2, load_factor=70, hours=4000, qty=2), 65000),
        ("Air-Cooled Chiller 150 kW",
         dict(cooling_kw=150, cop=3.0, load_factor=75, hours=4000, qty=1), 45000),
    ],
    5: [
        ("400 W Metal Halide x100",
         dict(wattage_w=400, qty=100, efficacy=75, ballast_loss=15,
              hours=4000, occupancy=90), 120),
        ("T8 Fluorescent 36 W x500",
         dict(wattage_w=36, qty=500, efficacy=80, ballast_loss=12,
              hours=4000, occupancy=85), 45),
    ],
    6: [
        ("Rotary Screw 75 kW",
         dict(compressor_kw=75, efficiency=85, leak_rate=25, load_factor=70,
              hours=6000, qty=2), 25000),
        ("Reciprocating 22 kW",
         dict(compressor_kw=22, efficiency=80, leak_rate=30, load_factor=60,
              hours=4000, qty=3), 12000),
    ],
    7: [
        ("Small Server Room 50 kW",
         dict(it_load_kw=50, pue=2.0, ups_eff=92, hours=8760), 80000),
        ("Medium Data Centre 200 kW",
         dict(it_load_kw=200, pue=1.8, ups_eff=94, hours=8760), 250000),
    ],
    8: [
        ("VFD on 75 kW Pump",
         dict(motor_kw=75, motor_eff=93, vfd_eff=97, avg_speed=70,
              hours=6000, qty=2), 7500),
        ("VFD on 30 kW Fan",
         dict(motor_kw=30, motor_eff=92, vfd_eff=97, avg_speed=65,
              hours=5000, qty=4), 4000),
    ],
    9: [
        ("1000 kW Gas Boiler",
         dict(thermal_output_kw=1000, efficiency=85, gas_cost=0.04,
              load_factor=60, hours=4000, qty=1), 45000),
        ("500 kW Gas Boiler",
         dict(thermal_output_kw=500, efficiency=82, gas_cost=0.04,
              load_factor=70, hours=3500, qty=2), 28000),
    ],
    10: [
        ("Rooftop 100 kWp",
         dict(peak_kw=100, annual_yield=1350, inverter_eff=97), 95000),
        ("Ground-Mount 500 kWp",
         dict(peak_kw=500, annual_yield=1400, inverter_eff=98), 420000),
    ],
}

# =============================================================================
#  UTILITY FUNCTIONS
# =============================================================================

def fmt_power(kw):
    """Auto-format a power value with appropriate unit."""
    if abs(kw) >= 1000:
        return f"{kw / 1000:,.2f} MW"
    elif abs(kw) >= 1:
        return f"{kw:,.2f} kW"
    else:
        return f"{kw * 1000:,.2f} W"


def fmt_energy(kwh):
    """Auto-format an energy value with appropriate unit."""
    if abs(kwh) >= 1_000_000:
        return f"{kwh / 1_000_000:,.2f} GWh"
    elif abs(kwh) >= 1000:
        return f"{kwh / 1000:,.2f} MWh"
    else:
        return f"{kwh:,.2f} kWh"


def fmt_currency(val):
    """Format currency with commas and 2 decimals."""
    if val < 0:
        return f"-${abs(val):,.2f}"
    return f"${val:,.2f}"


def fmt_co2(kg):
    """Format CO2 with appropriate unit."""
    if abs(kg) >= 1000:
        return f"{kg / 1000:,.2f} tonnes"
    return f"{kg:,.2f} kg"


def get_float(prompt, default=None):
    """Prompt user for a float. Accepts blank for default if provided."""
    while True:
        suffix = f" [{default}]: " if default is not None else ": "
        raw = input(prompt + suffix).strip()
        if raw == "" and default is not None:
            return float(default)
        try:
            val = float(raw)
            return val
        except ValueError:
            print("  Invalid number. Try again.")


def get_int(prompt, default=None):
    """Prompt user for an int."""
    while True:
        suffix = f" [{default}]: " if default is not None else ": "
        raw = input(prompt + suffix).strip()
        if raw == "" and default is not None:
            return int(default)
        try:
            val = int(raw)
            return val
        except ValueError:
            print("  Invalid integer. Try again.")


def npv(rate, years, annual_saving, initial_cost):
    """Net present value calculation."""
    total = -initial_cost
    for yr in range(1, years + 1):
        total += annual_saving / (1 + rate) ** yr
    return total


# =============================================================================
#  SUBSYSTEM CALCULATIONS
# =============================================================================

def calc_transformer(p):
    """Return (loss_kw, annual_loss_kwh, description) for a transformer."""
    lf = p["load_factor"] / 100
    loss_per = p["no_load_loss_kw"] + (lf ** 2) * p["full_load_loss_kw"]
    total_loss = loss_per * p["qty"]
    annual = total_loss * p["hours"]
    desc = (f"{p['qty']}x {p['rated_kva']} kVA transformer, "
            f"load factor {p['load_factor']}%")
    return total_loss, annual, desc


def calc_transformer_green(p):
    """Amorphous core transformer: 30% no-load factor, 85% full-load factor."""
    lf = p["load_factor"] / 100
    nl = p["no_load_loss_kw"] * 0.30
    fl = p["full_load_loss_kw"] * 0.85
    loss_per = nl + (lf ** 2) * fl
    total_loss = loss_per * p["qty"]
    annual = total_loss * p["hours"]
    return total_loss, annual, "Amorphous core transformer"


def calc_motor(p):
    lf = p["load_factor"] / 100
    eff = p["efficiency"] / 100
    input_per = p["rated_kw"] * lf / eff
    loss_per = input_per - p["rated_kw"] * lf
    total_loss = loss_per * p["qty"]
    annual = total_loss * p["hours"]
    desc = (f"{p['qty']}x {p['rated_kw']} kW motor at {p['efficiency']}% eff, "
            f"load factor {p['load_factor']}%")
    return total_loss, annual, desc


def calc_motor_green(p):
    lf = p["load_factor"] / 100
    eff = 0.97  # IE5
    input_per = p["rated_kw"] * lf / eff
    loss_per = input_per - p["rated_kw"] * lf
    total_loss = loss_per * p["qty"]
    annual = total_loss * p["hours"]
    return total_loss, annual, "IE5 ultra-premium motor (97% eff)"


def calc_pump(p):
    lf = p["load_factor"] / 100
    m_eff = p["motor_eff"] / 100
    p_eff = p["pump_eff"] / 100
    combined = m_eff * p_eff
    input_per = p["rated_kw"] * lf / combined
    loss_per = input_per - p["rated_kw"] * lf
    total_loss = loss_per * p["qty"]
    annual = total_loss * p["hours"]
    desc = (f"{p['qty']}x {p['rated_kw']} kW pump "
            f"(motor {p['motor_eff']}%, pump {p['pump_eff']}%)")
    return total_loss, annual, desc


def calc_pump_green(p):
    lf = p["load_factor"] / 100
    combined = 0.96 * 0.85  # high-eff motor + VFD pump
    input_per = p["rated_kw"] * lf / combined
    loss_per = input_per - p["rated_kw"] * lf
    total_loss = loss_per * p["qty"]
    annual = total_loss * p["hours"]
    return total_loss, annual, "High-eff pump + VFD (96%/85%)"


def calc_chiller(p):
    lf = p["load_factor"] / 100
    input_per = p["cooling_kw"] * lf / p["cop"]
    # "loss" here = electrical input (all becomes heat rejection overhead)
    total = input_per * p["qty"]
    annual = total * p["hours"]
    desc = (f"{p['qty']}x {p['cooling_kw']} kW chiller, "
            f"COP {p['cop']}, load {p['load_factor']}%")
    return total, annual, desc


def calc_chiller_green(p):
    lf = p["load_factor"] / 100
    input_per = p["cooling_kw"] * lf / 7.0  # magnetic bearing COP 7.0
    total = input_per * p["qty"]
    annual = total * p["hours"]
    return total, annual, "Magnetic bearing chiller (COP 7.0)"


def calc_lighting(p):
    ballast = p["ballast_loss"] / 100
    occ = p["occupancy"] / 100
    total_kw = p["wattage_w"] * (1 + ballast) * p["qty"] * occ / 1000
    annual = total_kw * p["hours"]
    desc = (f"{p['qty']}x {p['wattage_w']} W lamps, "
            f"{p['efficacy']} lm/W, {p['ballast_loss']}% ballast, "
            f"{p['occupancy']}% occupancy")
    return total_kw, annual, desc


def calc_lighting_green(p):
    occ = p["occupancy"] / 100
    # LED: 40% wattage, 150 lm/W, no ballast loss
    led_wattage = p["wattage_w"] * 0.40
    total_kw = led_wattage * p["qty"] * occ / 1000
    annual = total_kw * p["hours"]
    return total_kw, annual, "LED retrofit (150 lm/W, 40% wattage)"


def calc_compressed_air(p):
    eff = p["efficiency"] / 100
    leak = p["leak_rate"] / 100
    lf = p["load_factor"] / 100
    useful_per = p["compressor_kw"] * lf * eff  # useful air energy
    input_per = p["compressor_kw"] * lf
    inefficiency_loss = input_per - useful_per
    leak_loss = useful_per * leak / (1 - leak)  # extra input to compensate leaks
    total_loss = (inefficiency_loss + leak_loss) * p["qty"]
    total_input = (input_per + leak_loss) * p["qty"]
    annual = total_input * p["hours"]
    desc = (f"{p['qty']}x {p['compressor_kw']} kW compressor, "
            f"{p['efficiency']}% eff, {p['leak_rate']}% leak")
    return total_input, annual, desc


def calc_compressed_air_green(p):
    eff = 0.92  # VSD compressor
    leak = 0.10  # after leak repair
    lf = p["load_factor"] / 100
    useful_per = p["compressor_kw"] * lf * eff
    input_per = p["compressor_kw"] * lf
    inefficiency_loss = input_per - useful_per
    leak_loss = useful_per * leak / (1 - leak)
    total_input = (input_per + leak_loss) * p["qty"]
    annual = total_input * p["hours"]
    return total_input, annual, "VSD compressor + leak repair (92% eff, 10% leak)"


def calc_data_centre(p):
    ups_eff = p["ups_eff"] / 100
    overhead = p["it_load_kw"] * (p["pue"] - 1)
    ups_loss = p["it_load_kw"] * (1 / ups_eff - 1)
    total = p["it_load_kw"] + overhead + ups_loss
    annual = total * p["hours"]
    desc = (f"IT {p['it_load_kw']} kW, PUE {p['pue']}, "
            f"UPS {p['ups_eff']}%")
    return total, annual, desc


def calc_data_centre_green(p):
    ups_eff = 0.97
    overhead = p["it_load_kw"] * (1.2 - 1)  # PUE 1.2
    ups_loss = p["it_load_kw"] * (1 / ups_eff - 1)
    total = p["it_load_kw"] + overhead + ups_loss
    annual = total * p["hours"]
    return total, annual, "Optimised DC (PUE 1.2, UPS 97%)"


def calc_vfd(p):
    """VFD with affinity law: power proportional to speed^3."""
    speed = p["avg_speed"] / 100
    m_eff = p["motor_eff"] / 100
    v_eff = p["vfd_eff"] / 100
    power_per = p["motor_kw"] * (speed ** 3) / m_eff / v_eff
    total = power_per * p["qty"]
    annual = total * p["hours"]
    # For comparison, DOL would be full speed
    dol_power = p["motor_kw"] / m_eff * p["qty"]
    dol_annual = dol_power * p["hours"]
    desc = (f"{p['qty']}x VFD on {p['motor_kw']} kW motor @ "
            f"{p['avg_speed']}% speed (saves {fmt_energy(dol_annual - annual)} vs DOL)")
    return total, annual, desc


def calc_vfd_green(p):
    """Already a green technology; just returns the same values."""
    speed = p["avg_speed"] / 100
    m_eff = p["motor_eff"] / 100
    v_eff = p["vfd_eff"] / 100
    power_per = p["motor_kw"] * (speed ** 3) / m_eff / v_eff
    total = power_per * p["qty"]
    annual = total * p["hours"]
    return total, annual, "Already VFD-equipped (no further green alt)"


def calc_boiler(p):
    lf = p["load_factor"] / 100
    eff = p["efficiency"] / 100
    fuel_per = p["thermal_output_kw"] * lf / eff
    total = fuel_per * p["qty"]
    annual = total * p["hours"]
    desc = (f"{p['qty']}x {p['thermal_output_kw']} kW boiler at "
            f"{p['efficiency']}% eff, LF {p['load_factor']}%")
    return total, annual, desc


def calc_boiler_green(p):
    lf = p["load_factor"] / 100
    eff = 0.95  # condensing boiler
    fuel_per = p["thermal_output_kw"] * lf / eff
    total = fuel_per * p["qty"]
    annual = total * p["hours"]
    return total, annual, "Condensing boiler (95% eff)"


def calc_solar(p):
    gen = p["peak_kw"] * p["annual_yield"] * (p["inverter_eff"] / 100)
    desc = (f"{p['peak_kw']} kWp solar, {p['annual_yield']} kWh/kWp, "
            f"{p['inverter_eff']}% inverter")
    # Negative = generation offsets consumption
    return 0, -gen, desc


def calc_solar_green(p):
    # Already green; same values
    gen = p["peak_kw"] * p["annual_yield"] * (p["inverter_eff"] / 100)
    return 0, -gen, "Already solar PV (no further green alt)"


CALC_FUNCS = {
    1: (calc_transformer, calc_transformer_green),
    2: (calc_motor, calc_motor_green),
    3: (calc_pump, calc_pump_green),
    4: (calc_chiller, calc_chiller_green),
    5: (calc_lighting, calc_lighting_green),
    6: (calc_compressed_air, calc_compressed_air_green),
    7: (calc_data_centre, calc_data_centre_green),
    8: (calc_vfd, calc_vfd_green),
    9: (calc_boiler, calc_boiler_green),
    10: (calc_solar, calc_solar_green),
}

# =============================================================================
#  INPUT COLLECTION PER SUBSYSTEM TYPE
# =============================================================================

PARAM_PROMPTS = {
    1: [
        ("rated_kva", "Rated capacity (kVA)"),
        ("load_factor", "Load factor (%)"),
        ("no_load_loss_kw", "No-load loss (kW)"),
        ("full_load_loss_kw", "Full-load loss (kW)"),
        ("hours", "Annual operating hours"),
        ("qty", "Quantity"),
    ],
    2: [
        ("rated_kw", "Rated power (kW)"),
        ("efficiency", "Efficiency (%)"),
        ("load_factor", "Load factor (%)"),
        ("hours", "Annual operating hours"),
        ("qty", "Quantity"),
    ],
    3: [
        ("rated_kw", "Rated power (kW)"),
        ("motor_eff", "Motor efficiency (%)"),
        ("pump_eff", "Pump efficiency (%)"),
        ("load_factor", "Load factor (%)"),
        ("hours", "Annual operating hours"),
        ("qty", "Quantity"),
    ],
    4: [
        ("cooling_kw", "Cooling capacity (kW)"),
        ("cop", "COP (coefficient of performance)"),
        ("load_factor", "Load factor (%)"),
        ("hours", "Annual operating hours"),
        ("qty", "Quantity"),
    ],
    5: [
        ("wattage_w", "Lamp wattage (W)"),
        ("qty", "Number of lamps"),
        ("efficacy", "Efficacy (lm/W)"),
        ("ballast_loss", "Ballast loss (%)"),
        ("hours", "Annual operating hours"),
        ("occupancy", "Occupancy factor (%)"),
    ],
    6: [
        ("compressor_kw", "Compressor rated power (kW)"),
        ("efficiency", "Compressor efficiency (%)"),
        ("leak_rate", "Leak rate (%)"),
        ("load_factor", "Load factor (%)"),
        ("hours", "Annual operating hours"),
        ("qty", "Quantity"),
    ],
    7: [
        ("it_load_kw", "IT load (kW)"),
        ("pue", "PUE (power usage effectiveness)"),
        ("ups_eff", "UPS efficiency (%)"),
        ("hours", "Annual operating hours"),
    ],
    8: [
        ("motor_kw", "Motor rated power (kW)"),
        ("motor_eff", "Motor efficiency (%)"),
        ("vfd_eff", "VFD efficiency (%)"),
        ("avg_speed", "Average operating speed (%)"),
        ("hours", "Annual operating hours"),
        ("qty", "Quantity"),
    ],
    9: [
        ("thermal_output_kw", "Thermal output (kW)"),
        ("efficiency", "Boiler efficiency (%)"),
        ("gas_cost", "Gas cost ($/kWh)"),
        ("load_factor", "Load factor (%)"),
        ("hours", "Annual operating hours"),
        ("qty", "Quantity"),
    ],
    10: [
        ("peak_kw", "Peak capacity (kWp)"),
        ("annual_yield", "Annual yield (kWh/kWp)"),
        ("inverter_eff", "Inverter efficiency (%)"),
    ],
}


def collect_params(cat_id):
    """Let user choose a preset or enter custom values. Returns (params, upgrade_cost)."""
    presets = PRESETS.get(cat_id, [])
    print(f"\n  Available presets for {CATEGORY_NAMES[cat_id]}:")
    for i, (label, _, cost) in enumerate(presets, 1):
        print(f"    [{i}] {label}  (upgrade cost: {fmt_currency(cost)})")
    print(f"    [C] Custom values")

    while True:
        choice = input("  Select: ").strip().upper()
        if choice == "C":
            break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(presets):
                label, params, cost = presets[idx]
                print(f"  -> Loaded preset: {label}")
                # Allow user to override individual values
                print("  (Press Enter to keep default for each parameter)")
                final = {}
                for key, prompt_text in PARAM_PROMPTS[cat_id]:
                    default_val = params.get(key)
                    final[key] = get_float(f"    {prompt_text}", default_val)
                upgrade_cost = get_float("    Upgrade cost per unit ($)", cost)
                if "qty" in final:
                    upgrade_cost *= final["qty"]
                return final, upgrade_cost
        except (ValueError, IndexError):
            pass
        print("  Invalid choice. Try again.")

    # Custom entry
    params = {}
    for key, prompt_text in PARAM_PROMPTS[cat_id]:
        params[key] = get_float(f"    {prompt_text}")
    upgrade_cost = get_float("    Estimated upgrade cost per unit ($)", 0)
    if "qty" in params:
        upgrade_cost *= params["qty"]
    return params, upgrade_cost


# =============================================================================
#  DEMO FACILITY
# =============================================================================

DEMO_SCENARIOS = {
    "1": {
        "name": "Steel Mill / Heavy Manufacturing",
        "settings": {"hours": 7200, "tariff": 0.09, "demand": 18, "gas": 1.05, "carbon": 0.45},
        "items": [
            (1, 1), (1, 0),               # 2000 kVA + 1000 kVA transformers
            (2, 2), (2, 0), (2, 0), (2, 1),# 200kW, 75kW×2, 15kW IE1 motors
            (3, 0), (3, 0),               # Centrifugal 55kW×2 — cooling, hydraulic
            (4, 0),                        # Screw chiller 200kWt — process cooling
            (5, 0), (5, 1),               # HID warehouse, fluorescent offices
            (6, 0), (6, 1),               # Rotary screw 75kW, reciprocating 22kW
            (7, 0),                        # Server room 50kW — SCADA
            (8, 0),                        # VFD on 75kW pump
            (9, 0), (9, 1),               # Gas boiler 1000kWt + 500kWt
            (10, 0),                       # Rooftop PV 100kWp
        ]
    },
    "2": {
        "name": "Automotive Assembly Plant",
        "settings": {"hours": 5600, "tariff": 0.11, "demand": 15, "gas": 1.10, "carbon": 0.42},
        "items": [
            (1, 1), (1, 0),               # 2000 kVA main + 1000 kVA body shop
            (2, 2), (2, 0), (2, 1),       # 200kW paint fans, 75kW conveyor, 15kW IE1 old
            (3, 0), (3, 1),               # 55kW coolant, 30kW submersible wash
            (4, 0),                        # Screw chiller 200kWt — process
            (5, 0), (5, 1),               # HID plant floor, fluorescent offices
            (6, 0), (6, 1),               # 75kW assembly tools, 22kW instruments
            (7, 0),                        # Server room — MES
            (8, 0), (8, 1),               # VFD on pump, VFD on fan
            (9, 0),                        # Gas boiler 1000kWt — paint ovens
            (10, 0),                       # Rooftop PV 100kWp
        ]
    },
    "3": {
        "name": "Pharmaceutical / Clean Room Facility",
        "settings": {"hours": 8000, "tariff": 0.14, "demand": 14, "gas": 1.15, "carbon": 0.38},
        "items": [
            (1, 0), (1, 2),               # 1000 kVA main, 500 kVA clean room
            (2, 0), (2, 1),               # 75kW HVAC, 15kW IE1 old mixers
            (3, 0), (3, 1),               # 55kW chilled water, 30kW submersible
            (4, 0), (4, 1),               # Screw 200kWt, air-cooled 150kWt
            (5, 1), (5, 1),               # Fluorescent clean rooms, fluorescent packaging
            (6, 0),                        # 75kW clean air compressor
            (7, 0),                        # Server room — GxP systems
            (8, 0), (8, 1),               # VFD on pump, VFD on fan
            (9, 1),                        # Gas boiler 500kWt — sterilisation steam
            (10, 0),                       # Rooftop PV 100kWp
        ]
    },
    "4": {
        "name": "Data Centre (Colocation)",
        "settings": {"hours": 8760, "tariff": 0.10, "demand": 20, "gas": 1.10, "carbon": 0.40},
        "items": [
            (1, 1), (1, 1), (1, 0),       # 2000 kVA A-feed, B-feed, 1000 kVA mech
            (7, 1), (7, 0), (7, 0),       # 200kW Hall A, 50kW Hall B, 50kW Hall C
            (4, 0), (4, 1),               # Screw 200kWt, air-cooled 150kWt
            (3, 0), (3, 1),               # 55kW chilled water, 30kW condenser
            (5, 1), (5, 1),               # Fluorescent server halls, fluorescent offices
            (8, 0), (8, 1),               # VFD on pump, VFD on fans
            (10, 1),                       # Ground-mount PV 500kWp
        ]
    },
    "5": {
        "name": "Commercial Office Building",
        "settings": {"hours": 3000, "tariff": 0.15, "demand": 10, "gas": 1.20, "carbon": 0.35},
        "items": [
            (1, 2),                        # 500 kVA transformer
            (2, 1),                        # 15kW IE1 — old AHU motors
            (3, 1), (3, 1),               # 30kW HVAC circ, 30kW DHW
            (4, 1),                        # 150kWt air-cooled chiller
            (5, 1), (5, 1),               # Fluorescent offices, fluorescent lobbies
            (7, 0),                        # Server room 50kW
            (8, 1),                        # VFD on AHU fan
            (9, 1),                        # Gas boiler 500kWt — heating
            (10, 0),                       # Rooftop PV 100kWp
        ]
    },
    "6": {
        "name": "Water Treatment Works",
        "settings": {"hours": 8760, "tariff": 0.10, "demand": 16, "gas": 1.05, "carbon": 0.42},
        "items": [
            (1, 0), (1, 2),               # 1000 kVA, 500 kVA
            (2, 0), (2, 0), (2, 1), (2, 1), # 75kW blower, 75kW intake, 15kW scrapers×2
            (3, 0), (3, 0), (3, 0), (3, 1), # 55kW high-lift, 55kW backwash, 55kW dosing, 30kW site
            (6, 0),                        # 75kW process air
            (5, 0), (5, 1),               # HID outdoor, fluorescent control bldg
            (8, 0), (8, 0), (8, 1),       # VFD on pump×2, VFD on fan
            (7, 0),                        # Server room — SCADA
            (10, 0),                       # Rooftop PV 100kWp
        ]
    },
    "7": {
        "name": "Food & Beverage Processing",
        "settings": {"hours": 5000, "tariff": 0.12, "demand": 14, "gas": 1.10, "carbon": 0.42},
        "items": [
            (1, 0),                        # 1000 kVA
            (2, 0), (2, 1), (2, 1),       # 75kW mixing, 15kW IE1 conveyors×2
            (3, 0), (3, 1),               # 55kW CIP, 30kW product transfer
            (4, 0), (4, 1),               # Screw 200kWt cooling, air-cooled 150kWt glycol
            (5, 0), (5, 1),               # HID warehouse, fluorescent hall
            (6, 0),                        # 75kW packaging line air
            (8, 0), (8, 1),               # VFD on pump, fan
            (9, 0), (9, 1),               # 1000kWt steam, 500kWt CIP hot water
            (7, 0),                        # Server room — MES
            (10, 0),                       # Rooftop PV 100kWp
        ]
    },
    "8": {
        "name": "Cold Storage / Distribution Warehouse",
        "settings": {"hours": 8760, "tariff": 0.11, "demand": 12, "gas": 1.10, "carbon": 0.42},
        "items": [
            (1, 2),                        # 500 kVA
            (2, 1), (2, 1),               # 15kW IE1 conveyors, 15kW dock doors
            (4, 1),                        # 150kWt air-cooled — offices
            (5, 0), (5, 1),               # HID main warehouse, fluorescent offices
            (6, 0),                        # 75kW ammonia refrigeration
            (8, 0), (8, 1),               # VFD on compressor, VFD on fans
            (7, 0),                        # Server room — WMS
            (10, 0),                       # Rooftop PV 100kWp
        ]
    },
}


def build_demo(scenario_key):
    """Return a list of subsystems for the given scenario key."""
    scenario = DEMO_SCENARIOS[scenario_key]
    subs = []
    for cat_id, preset_idx in scenario["items"]:
        label, params, cost = PRESETS[cat_id][preset_idx]
        total_cost = cost * params.get("qty", 1)
        subs.append({
            "cat_id": cat_id,
            "label": label,
            "params": dict(params),
            "upgrade_cost": total_cost,
        })
    return subs, scenario


# =============================================================================
#  ANALYSIS ENGINE
# =============================================================================

def analyse(facility_settings, subsystems):
    """Run full analysis and print results."""
    tariff = facility_settings["tariff"]
    demand_charge = facility_settings["demand_charge"]
    carbon = facility_settings["carbon_intensity"]

    if not subsystems:
        print("\n  No subsystems added. Nothing to analyse.")
        return

    print(f"\n{'=' * 78}")
    print("   FACILITY EFFICIENCY ANALYSIS")
    print(f"{'=' * 78}")
    print(f"  Electricity tariff : {fmt_currency(tariff)}/kWh")
    print(f"  Demand charge      : {fmt_currency(demand_charge)}/kW/month")
    print(f"  Carbon intensity   : {carbon} kgCO2/kWh")
    print(f"  Subsystems         : {len(subsystems)}")

    # -- Calculate current and green for each subsystem --
    rows = []
    for sub in subsystems:
        cat = sub["cat_id"]
        calc_current, calc_green = CALC_FUNCS[cat]
        p = sub["params"]

        cur_kw, cur_kwh, cur_desc = calc_current(p)
        grn_kw, grn_kwh, grn_desc = calc_green(p)

        # Cost calculation
        if cat == 9:
            # Gas boiler uses gas cost, not electricity tariff
            gas_cost_rate = p.get("gas_cost", 0.04)
            cur_cost = cur_kwh * gas_cost_rate
            grn_cost = grn_kwh * gas_cost_rate
            cur_demand_cost = 0
            grn_demand_cost = 0
        elif cat == 10:
            # Solar offsets electricity cost
            cur_cost = cur_kwh * tariff  # negative kwh -> negative cost (saving)
            grn_cost = grn_kwh * tariff
            cur_demand_cost = 0
            grn_demand_cost = 0
        else:
            cur_cost = cur_kwh * tariff
            grn_cost = grn_kwh * tariff
            cur_demand_cost = cur_kw * demand_charge * 12
            grn_demand_cost = grn_kw * demand_charge * 12

        rows.append({
            "label": sub["label"],
            "cat_name": CATEGORY_NAMES[cat],
            "cat_id": cat,
            "cur_kw": cur_kw,
            "cur_kwh": cur_kwh,
            "cur_desc": cur_desc,
            "cur_cost": cur_cost + cur_demand_cost,
            "grn_kw": grn_kw,
            "grn_kwh": grn_kwh,
            "grn_desc": grn_desc,
            "grn_cost": grn_cost + grn_demand_cost,
            "upgrade_cost": sub["upgrade_cost"],
            "saving_kwh": cur_kwh - grn_kwh,
            "saving_cost": (cur_cost + cur_demand_cost) - (grn_cost + grn_demand_cost),
        })

    # Sort by annual energy impact (largest first)
    rows.sort(key=lambda r: abs(r["cur_kwh"]), reverse=True)

    # ------------------------------------------------------------------
    # TABLE 1: Current Loss / Consumption Breakdown
    # ------------------------------------------------------------------
    print(f"\n{'=' * 78}")
    print("   ENERGY CONSUMPTION BREAKDOWN (sorted by annual impact)")
    print(f"{'=' * 78}")
    print(f"  {'#':<3} {'Subsystem':<30} {'Power':>10} {'Annual Energy':>16} {'Annual Cost':>14}")
    print(f"  {'-'*3} {'-'*30} {'-'*10} {'-'*16} {'-'*14}")

    total_cur_kwh = 0
    total_cur_cost = 0
    total_cur_kw = 0
    for i, r in enumerate(rows, 1):
        total_cur_kwh += r["cur_kwh"]
        total_cur_cost += r["cur_cost"]
        total_cur_kw += r["cur_kw"]
        print(f"  {i:<3} {r['cat_name'] + ': ' + r['label']:<30} "
              f"{fmt_power(r['cur_kw']):>10} "
              f"{fmt_energy(r['cur_kwh']):>16} "
              f"{fmt_currency(r['cur_cost']):>14}")

    print(f"  {'-'*3} {'-'*30} {'-'*10} {'-'*16} {'-'*14}")
    print(f"  {'':3} {'TOTAL':<30} {fmt_power(total_cur_kw):>10} "
          f"{fmt_energy(total_cur_kwh):>16} {fmt_currency(total_cur_cost):>14}")

    # ------------------------------------------------------------------
    # TABLE 2: Green Alternatives
    # ------------------------------------------------------------------
    # Only show rows where there is actually a change
    green_rows = [r for r in rows if abs(r["saving_kwh"]) > 0.1]

    print(f"\n{'=' * 78}")
    print("   GREEN ALTERNATIVES & SAVINGS")
    print(f"{'=' * 78}")
    if green_rows:
        print(f"  {'#':<3} {'Current -> Green':<40} {'Energy Saved':>14} {'Cost Saved':>13}")
        print(f"  {'-'*3} {'-'*40} {'-'*14} {'-'*13}")
        for i, r in enumerate(green_rows, 1):
            label = f"{r['cat_name']}: {r['grn_desc']}"
            if len(label) > 40:
                label = label[:37] + "..."
            print(f"  {i:<3} {label:<40} "
                  f"{fmt_energy(r['saving_kwh']):>14} "
                  f"{fmt_currency(r['saving_cost']):>13}")
    else:
        print("  No green alternatives available for current subsystems.")

    # ------------------------------------------------------------------
    # FINANCIAL SUMMARY
    # ------------------------------------------------------------------
    total_grn_kwh = sum(r["grn_kwh"] for r in rows)
    total_grn_cost = sum(r["grn_cost"] for r in rows)
    total_saving_kwh = total_cur_kwh - total_grn_kwh
    total_saving_cost = total_cur_cost - total_grn_cost
    total_upgrade = sum(r["upgrade_cost"] for r in green_rows)

    payback = total_upgrade / total_saving_cost if total_saving_cost > 0 else float("inf")
    npv_val = npv(0.08, 10, total_saving_cost, total_upgrade)
    co2_current = total_cur_kwh * carbon / 1000 if total_cur_kwh > 0 else 0
    co2_green = total_grn_kwh * carbon / 1000 if total_grn_kwh > 0 else 0
    co2_reduction = co2_current - co2_green

    print(f"\n{'=' * 78}")
    print("   FINANCIAL SUMMARY")
    print(f"{'=' * 78}")
    print(f"  Current annual energy cost     : {fmt_currency(total_cur_cost)}")
    print(f"  Optimised annual energy cost   : {fmt_currency(total_grn_cost)}")
    print(f"  Annual energy saving           : {fmt_energy(total_saving_kwh)}")
    print(f"  Annual cost saving             : {fmt_currency(total_saving_cost)}")
    print(f"  {'-' * 44}")
    print(f"  Total upgrade investment       : {fmt_currency(total_upgrade)}")
    if payback < 100:
        print(f"  Simple payback period          : {payback:.1f} years")
    else:
        print(f"  Simple payback period          : N/A (no net saving)")
    print(f"  NPV (10 yr @ 8% discount)     : {fmt_currency(npv_val)}")
    print(f"  {'-' * 44}")
    print(f"  Current annual CO2             : {fmt_co2(co2_current * 1000)}")
    print(f"  Optimised annual CO2           : {fmt_co2(co2_green * 1000)}")
    print(f"  Annual CO2 reduction           : {fmt_co2(co2_reduction * 1000)}")

    # ------------------------------------------------------------------
    # PRIORITY LIST: Top 3 subsystems to upgrade
    # ------------------------------------------------------------------
    # Rank by saving-to-cost ratio (bang for buck)
    upgradeable = [r for r in rows if r["saving_cost"] > 0 and r["upgrade_cost"] > 0]
    upgradeable.sort(key=lambda r: r["saving_cost"] / r["upgrade_cost"], reverse=True)

    print(f"\n{'=' * 78}")
    print("   PRIORITY UPGRADES (best payback first)")
    print(f"{'=' * 78}")
    if upgradeable:
        for i, r in enumerate(upgradeable[:3], 1):
            pb = r["upgrade_cost"] / r["saving_cost"] if r["saving_cost"] > 0 else 999
            print(f"\n  #{i}  {r['cat_name']}: {r['label']}")
            print(f"      Upgrade to     : {r['grn_desc']}")
            print(f"      Annual saving  : {fmt_currency(r['saving_cost'])}  "
                  f"({fmt_energy(r['saving_kwh'])})")
            print(f"      Upgrade cost   : {fmt_currency(r['upgrade_cost'])}")
            print(f"      Payback        : {pb:.1f} years")
    else:
        print("  No upgrades with positive return identified.")

    # ------------------------------------------------------------------
    # COMPARISON: Putting savings in perspective
    # ------------------------------------------------------------------
    print(f"\n{'=' * 78}")
    print("   SAVINGS IN PERSPECTIVE")
    print(f"{'=' * 78}")

    COMPARISONS = [
        ("Average UK home annual electricity", 3100),
        ("Electric vehicle driven 20,000 km/yr", 4000),
        ("Street light running 1 year", 1500),
        ("Bitcoin transaction (avg)", 700),
        ("Server rack running 1 year", 20000),
        ("Commercial office per 100 m2/yr", 15000),
        ("Residential swimming pool heater/yr", 8000),
    ]

    if total_saving_kwh > 0:
        print(f"\n  Your potential annual saving of {fmt_energy(total_saving_kwh)} is equivalent to:\n")
        for label, kwh_ref in COMPARISONS:
            multiple = total_saving_kwh / kwh_ref
            if multiple >= 1:
                print(f"    - {multiple:,.1f}x {label} ({fmt_energy(kwh_ref)})")
            else:
                pct = multiple * 100
                print(f"    - {pct:.1f}% of {label} ({fmt_energy(kwh_ref)})")

        co2_trees = co2_reduction * 1000 / 21 if co2_reduction > 0 else 0  # ~21 kg CO2/tree/yr
        if co2_trees > 0:
            print(f"\n  CO2 reduction equivalent to planting {co2_trees:,.0f} trees per year.")
    else:
        print("\n  No net energy saving identified. The facility is already well optimised,")
        print("  or additional subsystems need to be added for analysis.")

    # ------------------------------------------------------------------
    # PRACTICAL RECOMMENDATIONS
    # ------------------------------------------------------------------
    print(f"\n{'=' * 78}")
    print("   PRACTICAL RECOMMENDATIONS")
    print(f"{'=' * 78}")

    recs = []

    # Check for high leak rates in compressed air
    for sub in subsystems:
        if sub["cat_id"] == 6 and sub["params"].get("leak_rate", 0) > 20:
            recs.append(
                "COMPRESSED AIR: Leak rate exceeds 20%. An ultrasonic leak survey\n"
                "      can typically find and fix leaks for minimal cost, saving 10-30%\n"
                "      of compressor energy immediately.")

    # Check for poor PUE
    for sub in subsystems:
        if sub["cat_id"] == 7 and sub["params"].get("pue", 1) > 1.8:
            recs.append(
                "DATA CENTRE: PUE above 1.8 indicates significant cooling overhead.\n"
                "      Consider hot/cold aisle containment, raising set-point temps,\n"
                "      or free-cooling economisers.")

    # Check for old lighting
    for sub in subsystems:
        if sub["cat_id"] == 5 and sub["params"].get("efficacy", 999) < 100:
            recs.append(
                "LIGHTING: Legacy lamps below 100 lm/W detected. LED retrofits\n"
                "      typically pay back within 1-3 years and also reduce cooling load.")

    # Check for low motor efficiency
    for sub in subsystems:
        if sub["cat_id"] == 2 and sub["params"].get("efficiency", 100) < 90:
            recs.append(
                "MOTORS: Motors below 90% efficiency found. At high running hours\n"
                "      the 5-10% efficiency gain from IE4/IE5 motors accumulates to\n"
                "      substantial savings over the motor lifetime.")

    # Check for low boiler efficiency
    for sub in subsystems:
        if sub["cat_id"] == 9 and sub["params"].get("efficiency", 100) < 88:
            recs.append(
                "GAS BOILER: Boiler efficiency below 88%. Condensing boilers recover\n"
                "      latent heat from flue gases, achieving 92-95% efficiency.\n"
                "      Also consider waste heat recovery from other processes.")

    # Check for chillers with low COP
    for sub in subsystems:
        if sub["cat_id"] == 4 and sub["params"].get("cop", 99) < 4.0:
            recs.append(
                "CHILLER: COP below 4.0 detected. Modern magnetic bearing centrifugal\n"
                "      chillers achieve COP 6-7+. Also ensure chilled water delta-T\n"
                "      is optimised and condenser coils are clean.")

    if not recs:
        recs.append(
            "No major red flags detected. Continue monitoring energy use and\n"
            "      consider an energy audit for deeper savings opportunities.")

    for i, rec in enumerate(recs, 1):
        print(f"\n  {i}. {rec}")

    print(f"\n{'=' * 78}")
    print("   END OF ANALYSIS")
    print(f"{'=' * 78}\n")


# =============================================================================
#  MAIN PROGRAM
# =============================================================================

def main():
    print("=" * 78)
    print("   INDUSTRIAL ELECTRICAL SYSTEM EFFICIENCY ANALYZER")
    print("=" * 78)
    print("  Build a facility model by adding subsystems, then analyse")
    print("  total losses, costs, green alternatives, and potential savings.")
    print()

    # -- Facility settings --
    print("-" * 78)
    print("  FACILITY SETTINGS")
    print("-" * 78)
    tariff = get_float("  Electricity tariff ($/kWh)", 0.12)
    demand_charge = get_float("  Demand charge ($/kW/month)", 15.0)
    carbon = get_float("  Carbon intensity (kgCO2/kWh)", 0.4)

    facility_settings = {
        "tariff": tariff,
        "demand_charge": demand_charge,
        "carbon_intensity": carbon,
    }

    subsystems = []

    # -- Main menu loop --
    while True:
        print(f"\n{'-' * 78}")
        print("  MAIN MENU")
        print(f"{'-' * 78}")
        print("  Add subsystem:")
        for num, name in CATEGORY_NAMES.items():
            print(f"    [{num:>2}] {name}")
        print()
        print(f"  [D]  Load industry example scenario")
        print(f"  [A]  Analyse facility ({len(subsystems)} subsystems loaded)")
        print(f"  [L]  List current subsystems")
        print(f"  [R]  Remove a subsystem")
        print(f"  [Q]  Quit")

        choice = input("\n  Select: ").strip().upper()

        if choice == "Q":
            print("\n  Goodbye.")
            break
        elif choice == "D":
            print(f"\n  {'='*60}")
            print("   INDUSTRY EXAMPLE SCENARIOS")
            print(f"  {'='*60}")
            for key, sc in DEMO_SCENARIOS.items():
                print(f"    [{key}] {sc['name']}")
            demo_choice = input("\n  Select scenario: ").strip()
            if demo_choice in DEMO_SCENARIOS:
                subsystems, scenario = build_demo(demo_choice)
                # Apply scenario settings
                s = scenario["settings"]
                facility_settings["tariff"] = s.get("tariff", facility_settings["tariff"])
                facility_settings["demand_charge"] = s.get("demand", facility_settings["demand_charge"])
                facility_settings["carbon_intensity"] = s.get("carbon", facility_settings["carbon_intensity"])
                print(f"\n  Loaded: {scenario['name']}")
                print(f"  {len(subsystems)} subsystems | ${s.get('tariff',0.12)}/kWh | ${s.get('demand',15)}/kW/mo")
                print(f"  Subsystems:")
                for sub in subsystems:
                    print(f"    - {CATEGORY_NAMES[sub['cat_id']]}: {sub['label']}")
            else:
                print("  Invalid selection.")
        elif choice == "A":
            analyse(facility_settings, subsystems)
        elif choice == "L":
            if not subsystems:
                print("\n  No subsystems added yet.")
            else:
                print(f"\n  Current facility ({len(subsystems)} subsystems):")
                for i, s in enumerate(subsystems, 1):
                    print(f"    {i:>3}. {CATEGORY_NAMES[s['cat_id']]}: {s['label']}")
        elif choice == "R":
            if not subsystems:
                print("\n  No subsystems to remove.")
            else:
                print(f"\n  Current facility ({len(subsystems)} subsystems):")
                for i, s in enumerate(subsystems, 1):
                    print(f"    {i:>3}. {CATEGORY_NAMES[s['cat_id']]}: {s['label']}")
                idx = get_int("  Enter number to remove", 0)
                if 1 <= idx <= len(subsystems):
                    removed = subsystems.pop(idx - 1)
                    print(f"  Removed: {CATEGORY_NAMES[removed['cat_id']]}: {removed['label']}")
                else:
                    print("  Invalid selection.")
        else:
            try:
                cat_id = int(choice)
                if cat_id not in CATEGORY_NAMES:
                    raise ValueError
            except ValueError:
                print("  Invalid choice. Try again.")
                continue

            print(f"\n  Adding: {CATEGORY_NAMES[cat_id]}")
            params, upgrade_cost = collect_params(cat_id)

            # Generate label
            preset_match = None
            for label, pvals, _ in PRESETS.get(cat_id, []):
                if all(params.get(k) == v for k, v in pvals.items()):
                    preset_match = label
                    break
            if preset_match is None:
                preset_match = f"Custom {CATEGORY_NAMES[cat_id]}"

            subsystems.append({
                "cat_id": cat_id,
                "label": preset_match,
                "params": params,
                "upgrade_cost": upgrade_cost,
            })

            # Quick preview
            calc_fn, _ = CALC_FUNCS[cat_id]
            kw, kwh, desc = calc_fn(params)
            print(f"\n  Added: {desc}")
            print(f"  Power draw: {fmt_power(kw)}, Annual energy: {fmt_energy(kwh)}")
            print(f"  Facility now has {len(subsystems)} subsystem(s).")


if __name__ == "__main__":
    main()
