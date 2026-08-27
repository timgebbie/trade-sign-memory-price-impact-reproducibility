#!/usr/bin/env python3
"""Run W09 sensitivity, robustness and edge-case diagnostics."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from functions.acf import lmf_exact, raw_acf_fft  # noqa: E402
from functions.clocks import (  # noqa: E402
    event_timestamps,
    inverse_event_counter,
    operational_clock,
    waiting_times,
)
from functions.impact import (  # noqa: E402
    constant_rate_analytic,
    constant_rate_numeric,
    undamped_completion_impact,
)
from functions.response import piecewise_constant_response  # noqa: E402
from functions.sign_process import simulate_lmf_signs  # noqa: E402

VERSION = "v1.0"


def number(value: float) -> str:
    return format(float(value), ".17g")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def expect_value_error(callable_object) -> bool:
    try:
        callable_object()
    except ValueError:
        return True
    return False


def add_row(rows: list, category: str, scenario: str, metric: str, value, interpretation: str, status: str) -> None:
    rows.append(
        {
            "category": category,
            "scenario": scenario,
            "metric": metric,
            "value": number(value) if isinstance(value, (float, np.floating)) else str(value),
            "interpretation": interpretation,
            "status": status,
        }
    )


def main() -> int:
    config = json.loads((ROOT / "config" / "RDL-CFG-v1.1.json").read_text())
    w09 = json.loads((ROOT / "config" / "RDL-W09-v1.0.json").read_text())
    rows: list[dict[str, str]] = []
    tolerance = w09["tolerances"]
    master_seed = int(config["random"]["master_seed"])

    # Analytic LMF boundary and special-case checks.
    lags = np.asarray(w09["lmf"]["diagnostic_lags"], dtype=np.int64)
    lmf_boundary_pass = True
    for alpha in [float(x) for x in w09["lmf"]["analytic_alpha_edges"]]:
        values = lmf_exact(alpha, lags)
        c0_error = abs(float(values[0]) - 1.0)
        finite_positive = bool(np.all(np.isfinite(values)) and np.all(values >= 0.0))
        monotone = bool(np.all(np.diff(values) <= 0.0))
        lmf_boundary_pass &= (
            c0_error <= float(tolerance["identity_abs"])
            and finite_positive
            and monotone
        )
        add_row(rows, "lmf_analytic", f"alpha_L={alpha:g}", "C(0) absolute error", c0_error, "exact identity", "pass")
        add_row(rows, "lmf_analytic", f"alpha_L={alpha:g}", "minimum sampled C(tau)", float(np.min(values)), "finite nonnegative boundary check", "pass" if finite_positive else "fail")
        add_row(rows, "lmf_analytic", f"alpha_L={alpha:g}", "sampled path monotone", monotone, "exact working form remains ordered", "pass" if monotone else "fail")

    invalid_checks = {
        "lmf alpha at boundary": expect_value_error(lambda: lmf_exact(1.0, np.array([0, 1]))),
        "lmf negative lag": expect_value_error(lambda: lmf_exact(1.5, np.array([-1, 0]))),
        "zero activity": expect_value_error(lambda: operational_clock(np.array([0.0, 1.0]), 0.0)),
        "negative completion rate": expect_value_error(lambda: undamped_completion_impact(-1.0, 1.0, 1.0, 1.0)),
        "zero completion horizon": expect_value_error(lambda: undamped_completion_impact(1.0, 0.0, 1.0, 1.0)),
        "zero diffusion": expect_value_error(lambda: undamped_completion_impact(1.0, 1.0, 1.0, 0.0)),
        "negative resilience": expect_value_error(lambda: piecewise_constant_response(np.ones(4), 0.1, 1.0, 1.0, -1.0)),
    }
    for scenario, passed in invalid_checks.items():
        add_row(rows, "invalid_input", scenario, "ValueError raised", passed, "invalid branch rejected explicitly", "pass" if passed else "fail")

    # Finite-sample LMF sensitivity. These metrics are diagnostic, not promotion gates.
    mc = w09["lmf"]
    mc_repeatable = True
    mc_metrics = {}
    for alpha in [float(x) for x in mc["mc_alphas"]]:
        exact = lmf_exact(alpha, np.arange(int(mc["mc_max_lag"]) + 1))
        for n_events in [int(x) for x in mc["mc_event_counts"]]:
            rmses = []
            for replicate in range(int(mc["mc_replicates"])):
                seed = (master_seed, int(mc["seed_target_id"]), int(round(alpha * 100)), replicate)
                first = simulate_lmf_signs(alpha, n_events, int(mc["mc_burn_events"]), seed)
                second = simulate_lmf_signs(alpha, n_events, int(mc["mc_burn_events"]), seed)
                mc_repeatable &= bool(np.array_equal(first, second))
                estimate = raw_acf_fft(first, int(mc["mc_max_lag"]))
                rmses.append(float(np.sqrt(np.mean((estimate[1:] - exact[1:]) ** 2))))
            key = f"alpha_{alpha:g}_n_{n_events}"
            mc_metrics[key] = {
                "replicate_rmse": rmses,
                "mean_rmse": float(np.mean(rmses)),
                "rmse_range": float(np.ptp(rmses)),
            }
            add_row(rows, "lmf_monte_carlo", key, "mean replicate RMSE lags 1:64", mc_metrics[key]["mean_rmse"], "finite-sample sensitivity only", "diagnostic")
            add_row(rows, "lmf_monte_carlo", key, "replicate RMSE range", mc_metrics[key]["rmse_range"], "seed dispersion; no promotion threshold", "diagnostic")

    # Direct-clock seed sensitivity and invariants.
    clock_invariants = True
    clock_metrics = {}
    for scenario_index, scenario in enumerate(config["clock"]["waiting_scenarios"]):
        completions = []
        for offset in [int(x) for x in w09["clock"]["seed_offsets"]]:
            waits = waiting_times(
                scenario,
                int(w09["clock"]["n_events"]),
                master_seed,
                scenario_index + offset,
            )
            timestamps = event_timestamps(waits)
            inverse = inverse_event_counter(timestamps, timestamps)
            valid = bool(
                np.all(waits > 0.0)
                and np.all(np.diff(timestamps) > 0.0)
                and np.array_equal(inverse, np.arange(timestamps.size))
            )
            clock_invariants &= valid
            completions.append(float(timestamps[-1]))
        clock_metrics[scenario["id"]] = {
            "completion_min": min(completions),
            "completion_max": max(completions),
            "completion_spread": max(completions) - min(completions),
        }
        add_row(rows, "direct_clock", scenario["id"], "completion-time spread across seeds", clock_metrics[scenario["id"]]["completion_spread"], "calendar duration may vary while event order is preserved", "diagnostic")
    for activity in [float(x) for x in w09["clock"]["activity_edges"]]:
        calendar = np.linspace(0.0, 2.0, 101)
        operational = operational_clock(calendar, activity)
        valid = bool(np.all(np.diff(operational) >= 0.0))
        clock_invariants &= valid
        add_row(rows, "operational_clock", f"alpha_U={activity:g}", "terminal operational time", float(operational[-1]), "monotone deterministic edge", "pass" if valid else "fail")

    # Abel grid and pulse-width edge checks.
    response = w09["response"]
    response_pass = True
    response_errors = {}
    for resilience in [float(x) for x in response["resilience_edges"]]:
        for grid_points in [int(x) for x in response["grid_points"]]:
            u = np.linspace(0.0, float(response["display_horizon"]), grid_points)
            analytic = constant_rate_analytic(u, 1.0, float(response["completion_time"]), 1.0, 1.0, resilience)
            numeric = constant_rate_numeric(u, 1.0, float(response["completion_time"]), 1.0, 1.0, resilience)
            relative = float(np.max(np.abs(numeric - analytic)) / np.max(np.abs(analytic)))
            passed = relative <= float(tolerance["analytic_numeric_relative"])
            response_pass &= passed
            key = f"nu_{resilience:g}_n_{grid_points}"
            response_errors[key] = relative
            add_row(rows, "abel_grid", key, "relative L-infinity error", relative, "analytic versus cell-integrated response", "pass" if passed else "fail")

    pulse_pass = True
    pulse_metrics = {}
    pulse_points = int(response["pulse_grid_points"])
    pulse_time = np.linspace(0.0, 1.0, pulse_points)
    pulse_dt = float(pulse_time[1] - pulse_time[0])
    starts = pulse_time[:-1]
    for width in [float(x) for x in response["pulse_width_edges"]]:
        rates = np.where(starts < width, 1.0 / width, 0.0)
        path = piecewise_constant_response(rates, pulse_dt, 1.0, 1.0, 0.0)
        area_error = abs(float(np.sum(rates) * pulse_dt) - 1.0)
        finite = bool(np.all(np.isfinite(path)))
        passed = area_error <= float(tolerance["identity_abs"]) and finite
        pulse_pass &= passed
        pulse_metrics[f"tau_0={width:g}"] = {
            "area_error": area_error,
            "peak": float(np.max(path)),
        }
        add_row(rows, "pulse_width", f"tau_0={width:g}", "forcing-area absolute error", area_error, "fixed-area edge width", "pass" if passed else "fail")
        add_row(rows, "pulse_width", f"tau_0={width:g}", "finite response peak", float(np.max(path)), "peak height is width-sensitive", "diagnostic")

    # Extended schedule and scale identities.
    completion = w09["completion"]
    q = np.logspace(
        np.log10(float(completion["minimum_volume"])),
        np.log10(float(completion["maximum_volume"])),
        int(completion["count"]),
    )
    fixed_rate = undamped_completion_impact(np.ones_like(q), q, 1.0, 1.0)
    fixed_horizon = undamped_completion_impact(q, np.ones_like(q), 1.0, 1.0)
    slope_rate = float(np.polyfit(np.log(q), np.log(fixed_rate), 1)[0])
    slope_horizon = float(np.polyfit(np.log(q), np.log(fixed_horizon), 1)[0])
    liquidity_ratio = float(
        undamped_completion_impact(1.0, 1.0, 1.0, 1.0)
        / undamped_completion_impact(1.0, 1.0, 2.0, 1.0)
    )
    diffusion_ratio = float(
        undamped_completion_impact(1.0, 1.0, 1.0, 1.0)
        / undamped_completion_impact(1.0, 1.0, 1.0, 4.0)
    )
    completion_pass = bool(
        abs(slope_rate - 0.5) <= float(tolerance["slope_abs"])
        and abs(slope_horizon - 1.0) <= float(tolerance["slope_abs"])
        and abs(liquidity_ratio - 2.0) <= float(tolerance["identity_abs"])
        and abs(diffusion_ratio - 2.0) <= float(tolerance["identity_abs"])
    )
    add_row(rows, "completion", "fixed rate extended Q", "fitted slope", slope_rate, "schedule-conditional square-root identity", "pass" if completion_pass else "fail")
    add_row(rows, "completion", "fixed horizon extended Q", "fitted slope", slope_horizon, "slope-one negative control", "pass" if completion_pass else "fail")
    add_row(rows, "completion", "liquidity scaling", "impact ratio L=1 to L=2", liquidity_ratio, "inverse-liquidity identity", "pass" if completion_pass else "fail")
    add_row(rows, "completion", "diffusion scaling", "impact ratio D=1 to D=4", diffusion_ratio, "inverse-square-root diffusion identity", "pass" if completion_pass else "fail")

    # Existing controlled diagnostics and scope routing.
    diagnostic_files = {
        "F02": "RDL-F02-TST-v1.2.json",
        "F03": "RDL-F03-TST-v1.0.json",
        "F05": "RDL-F05-TST-v1.1.json",
        "F06": "RDL-F06-TST-v1.0.json",
        "F07": "RDL-F07-TST-v1.0.json",
    }
    existing_checks = {}
    for target, filename in diagnostic_files.items():
        payload = json.loads((ROOT / "diagnostics" / filename).read_text())
        existing_checks[target] = bool(all(payload["checks"].values()))
    with (ROOT / "registers" / "RDL-ACC-v1.9.csv").open(newline="", encoding="utf-8") as stream:
        acceptance = {row["acc_id"]: row["status"] for row in csv.DictReader(stream)}
    active_gate_pass = all(acceptance[f"ACC{i:02d}"] == "pass" for i in range(3, 27))
    scope_unchanged = config["conditional_targets"] == {
        "F04": "design_extension_after_F02_diagnostics",
        "F09": "blocked_price_return_kernel_repair",
        "F10": "after_F02_F04_F07_diagnostics",
        "nonlinear_volterra": "inactive_unless_Abel_branch_is_insufficient",
        "full_lattice_PDE": "future_successor_project_only",
    }

    checks = {
        "existing_target_diagnostics_pass": all(existing_checks.values()) and active_gate_pass,
        "lmf_analytic_boundary_checks_pass": lmf_boundary_pass,
        "invalid_inputs_rejected": all(invalid_checks.values()),
        "stochastic_seed_repeatability": mc_repeatable,
        "clock_invariants_hold_across_seeds": clock_invariants,
        "abel_grid_edge_checks_pass": response_pass,
        "pulse_width_edge_checks_pass": pulse_pass,
        "completion_and_scale_identities_pass": completion_pass,
        "simulation_only_route_unchanged": config["route"] == "simulation_only",
        "conditional_and_deferred_scope_unchanged": scope_unchanged,
    }

    csv_path = ROOT / "data" / f"RDL-W09-{VERSION}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["category", "scenario", "metric", "value", "interpretation", "status"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    report = {
        "version": VERSION,
        "checks": checks,
        "existing_target_checks": existing_checks,
        "lmf_monte_carlo_sensitivity": mc_metrics,
        "clock_completion_sensitivity": clock_metrics,
        "abel_relative_errors": response_errors,
        "pulse_width_sensitivity": pulse_metrics,
        "completion_scaling": {
            "fixed_rate_slope": slope_rate,
            "fixed_horizon_slope": slope_horizon,
            "liquidity_ratio": liquidity_ratio,
            "diffusion_ratio": diffusion_ratio,
        },
        "invalid_input_checks": invalid_checks,
        "data_csv_sha256": sha256(csv_path),
    }
    json_path = ROOT / "diagnostics" / f"RDL-W09-TST-{VERSION}.json"
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(checks, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
