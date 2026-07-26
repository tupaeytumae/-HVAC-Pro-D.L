from __future__ import annotations

import json
import math
from pathlib import Path

import CoolProp
from CoolProp.CoolProp import PropsSI

FLUIDS = ["R407C", "R410A", "R32", "R134a", "R22", "R290", "R453A"]
T_MIN_C = -50.0
T_MAX_LIMIT_C = 70.0
STEP_C = 0.1
ATM_BAR = 1.01325
OUTPUT_FILE = Path("pt_data.js")


def saturation_pressure_gauge_bar(fluid: str, temp_c: float, quality: int) -> float:
    pressure_abs_pa = PropsSI("P", "T", temp_c + 273.15, "Q", quality, fluid)
    return pressure_abs_pa / 100000.0 - ATM_BAR


def build_fluid(fluid: str) -> dict[str, object]:
    critical_temp_c = PropsSI("Tcrit", fluid) - 273.15
    max_temp_c = min(
        T_MAX_LIMIT_C,
        math.floor((critical_temp_c - 1.0) / STEP_C) * STEP_C,
    )

    dew: list[list[float]] = []
    bubble: list[list[float]] = []
    point_count = int(round((max_temp_c - T_MIN_C) / STEP_C)) + 1

    for index in range(point_count):
        temp_c = round(T_MIN_C + index * STEP_C, 1)
        try:
            dew_pressure = saturation_pressure_gauge_bar(fluid, temp_c, 1)
            bubble_pressure = saturation_pressure_gauge_bar(fluid, temp_c, 0)
        except (ValueError, RuntimeError):
            continue

        if not all(math.isfinite(v) for v in (dew_pressure, bubble_pressure)):
            continue
        if dew_pressure <= -ATM_BAR or bubble_pressure <= -ATM_BAR:
            continue

        dew.append([round(dew_pressure, 5), temp_c])
        bubble.append([round(bubble_pressure, 5), temp_c])

    if len(dew) < 100 or len(bubble) < 100:
        raise RuntimeError(
            f"Tabla insuficiente para {fluid}: dew={len(dew)}, bubble={len(bubble)}"
        )

    return {
        "dew": dew,
        "bubble": bubble,
        "t_min_c": dew[0][1],
        "t_max_c": dew[-1][1],
    }


def validate_points(fluid: str, phase: str, points: list[list[float]]) -> None:
    if not all(points[i][0] < points[i + 1][0] for i in range(len(points) - 1)):
        raise RuntimeError(f"Presiones no monotónicas: {fluid} {phase}")
    if not all(points[i][1] < points[i + 1][1] for i in range(len(points) - 1)):
        raise RuntimeError(f"Temperaturas no monotónicas: {fluid} {phase}")


def main() -> None:
    data: dict[str, object] = {
        "meta": {
            "engine": "CoolProp",
            "version": CoolProp.__version__,
            "pressure_input": "bar(g)",
            "atmospheric_pressure_bar": ATM_BAR,
            "temperature_step_c": STEP_C,
            "quality_definition": {"dew": 1, "bubble": 0},
            "generated_by": "generate_pt.py",
        },
        "fluids": {},
    }

    fluids = data["fluids"]
    assert isinstance(fluids, dict)

    for fluid in FLUIDS:
        table = build_fluid(fluid)
        validate_points(fluid, "dew", table["dew"])
        validate_points(fluid, "bubble", table["bubble"])
        fluids[fluid] = table
        print(f"{fluid}: {len(table['dew'])} puntos")

    payload = "window.PT_DATABASE=" + json.dumps(
        data, ensure_ascii=False, separators=(",", ":")
    ) + ";\n"
    OUTPUT_FILE.write_text(payload, encoding="utf-8")

    print(
        f"Generadas tablas con CoolProp {CoolProp.__version__}: "
        + ", ".join(FLUIDS)
    )


if __name__ == "__main__":
    main()
