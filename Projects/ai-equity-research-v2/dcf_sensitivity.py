
from copy import deepcopy

from multistage_dcf import project_multistage_dcf


def run_dcf_sensitivity(
    fundamentals,
    assumptions,
    years=5,
    wacc_values=None,
    terminal_growth_values=None,
):
    """
    DCF sensitivity analysis using the existing Multi-Stage DCF engine.

    Returns:
        Dictionary containing scenario results and intrinsic value matrix.
    """

    if wacc_values is None:
        wacc_values = [0.08, 0.09, 0.10, 0.11, 0.12]

    if terminal_growth_values is None:
        terminal_growth_values = [0.015, 0.025, 0.035]

    if years < 1:
        return {
            "available": False,
            "reason": "Forecast years must be at least 1.",
        }

    matrix = []
    scenarios = []

    for wacc in wacc_values:
        row = {
            "wacc": wacc,
            "values": {},
        }

        for growth in terminal_growth_values:

            if wacc <= growth:
                result = {
                    "available": False,
                    "reason": "WACC must be greater than terminal growth.",
                }
            else:
                scenario_assumptions = deepcopy(assumptions)
                scenario_assumptions["wacc"] = wacc
                scenario_assumptions["terminal_growth"] = growth

                result = project_multistage_dcf(
                    fundamentals,
                    scenario_assumptions,
                    years=years,
                )

            intrinsic = (
                result.get("intrinsic_value_per_share")
                if result.get("available")
                else None
            )

            row["values"][growth] = intrinsic

            scenarios.append({
                "wacc": wacc,
                "terminal_growth": growth,
                "available": result.get("available", False),
                "intrinsic_value_per_share": intrinsic,
                "upside_downside_pct": result.get(
                    "upside_downside_pct"
                ),
                "enterprise_value": result.get("enterprise_value"),
                "equity_value": result.get("equity_value"),
                "terminal_fcff": result.get("terminal_fcff"),
                "reason": result.get("reason"),
            })

        matrix.append(row)

    base_case = next(
        (
            scenario
            for scenario in scenarios
            if abs(scenario["wacc"] - assumptions["wacc"]) < 1e-9
            and abs(
                scenario["terminal_growth"]
                - assumptions["terminal_growth"]
            ) < 1e-9
        ),
        None,
    )

    return {
        "available": True,
        "years": years,
        "wacc_values": list(wacc_values),
        "terminal_growth_values": list(terminal_growth_values),
        "matrix": matrix,
        "scenarios": scenarios,
        "base_case": base_case,
    }
