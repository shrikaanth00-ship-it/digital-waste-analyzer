# carbon.py
# Convert estimated runtime to energy (kWh) and CO2 using simple formulas.

def seconds_to_kwh(seconds: float, cpu_watts: float = 15.0) -> float:
    """
    Convert seconds of CPU usage to kWh using average CPU wattage.
    Default CPU wattage is 15 W (laptop average). Use 65 for desktop/server.
    """
    # Energy (kWh) = (Watts * seconds) / 3600 / 1000? careful: Watts * seconds = Joules (W*s)
    # Actually: Wh = Watts * (seconds/3600); kWh = Wh / 1000
    # So kWh = Watts * seconds / 3600 / 1000  -> that's wrong scale. Simpler:
    # Wh = Watts * (seconds / 3600)
    # kWh = Wh / 1000 = Watts * seconds / 3600000
    kwh = cpu_watts * seconds / 3600000.0
    return kwh


def kwh_to_co2_grams(kwh: float, carbon_intensity_g_per_kwh: float = 475.0) -> float:
    """
    Convert kWh to grams of CO2 using carbon intensity (g CO2 per kWh).
    Default 475 g/kWh global average.
    """
    return kwh * carbon_intensity_g_per_kwh


def estimate_energy_and_co2(seconds: float, cpu_watts: float = 15.0,
                            carbon_intensity_g_per_kwh: float = 475.0) -> dict:
    kwh = seconds_to_kwh(seconds, cpu_watts=cpu_watts)
    co2_g = kwh_to_co2_grams(kwh, carbon_intensity_g_per_kwh=carbon_intensity_g_per_kwh)
    return {"kwh": kwh, "co2_g": co2_g}
