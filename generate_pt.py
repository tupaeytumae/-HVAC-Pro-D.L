from CoolProp.CoolProp import PropsSI
import CoolProp
import json, math
from pathlib import Path

# Datos generados en la compilación. La PWA no ejecuta CoolProp en el teléfono:
# usa estas tablas localmente y sin conexión.
FLUIDS = ["R407C", "R410A", "R32", "R134a", "R290", "R22"]
T_MIN_C = -50.0
STEP_C = 0.1
ATM_BAR = 1.01325

def sat_pressure_gauge_bar(fluid: str, temp_c: float, quality: int) -> float:
    p_abs_pa = PropsSI("P", "T", temp_c + 273.15, "Q", quality, fluid)
    return p_abs_pa / 100000.0 - ATM_BAR

def build_fluid(fluid: str):
    t_crit_c = PropsSI("Tcrit", fluid) - 273.15
    t_max_c = min(70.0, math.floor((t_crit_c - 1.0) * 10) / 10)
    dew, bubble = [], []
    n = int(round((t_max_c - T_MIN_C) / STEP_C)) + 1
    for i in range(n):
        t = round(T_MIN_C + i * STEP_C, 1)
        try:
            # Q=1: vapor saturado (dew); Q=0: líquido saturado (bubble)
            pd = sat_pressure_gauge_bar(fluid, t, 1)
            pb = sat_pressure_gauge_bar(fluid, t, 0)
            if math.isfinite(pd) and math.isfinite(pb) and pd > -ATM_BAR and pb > -ATM_BAR:
                dew.append([round(pd, 5), t])
                bubble.append([round(pb, 5), t])
        except Exception:
            continue
    if len(dew) < 100 or len(bubble) < 100:
        raise RuntimeError(f"Tabla insuficiente para {fluid}")
    return {"dew": dew, "bubble": bubble, "t_min_c": dew[0][1], "t_max_c": dew[-1][1]}

data = {
    "meta": {
        "engine": "CoolProp",
        "version": CoolProp.__version__,
        "pressure_input": "bar(g)",
        "atmospheric_pressure_bar": ATM_BAR,
        "temperature_step_c": STEP_C,
        "quality_definition": {"dew": 1, "bubble": 0}
    },
    "fluids": {}
}

for fluid in FLUIDS:
    data["fluids"][fluid] = build_fluid(fluid)

payload = "window.PT_DATABASE=" + json.dumps(data, separators=(",", ":")) + ";\n"
Path("pt_data.js").write_text(payload, encoding="utf-8")

# Pequeñas comprobaciones automáticas de consistencia
for fluid, table in data["fluids"].items():
    for phase in ("dew", "bubble"):
        arr = table[phase]
        assert all(arr[i][0] < arr[i+1][0] for i in range(len(arr)-1)), (fluid, phase)
        assert all(arr[i][1] < arr[i+1][1] for i in range(len(arr)-1)), (fluid, phase)

print(f"Generadas tablas con CoolProp {CoolProp.__version__}: {', '.join(data['fluids'])}")
