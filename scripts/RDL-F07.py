#!/usr/bin/env python3
"""Build and diagnose completion-impact schedule scaling for F07."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
# Fix PDF creation metadata so identical inputs produce byte-identical artifacts.
os.environ.setdefault("SOURCE_DATE_EPOCH", "0")

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from functions.impact import undamped_completion_impact  # noqa: E402

TARGET = "F07"
VERSION = "v1.0"


def number(value: float) -> str:
    return format(float(value), ".17g")


def fitted_slope(volume: np.ndarray, impact: np.ndarray) -> float:
    return float(np.polyfit(np.log(volume), np.log(impact), 1)[0])


def build_scenarios(config: dict) -> dict[str, dict[str, np.ndarray | float | str]]:
    completion = config["completion"]
    response = config["response"]
    grid = completion["Q_grid"]
    q = np.logspace(
        np.log10(float(grid["minimum"])),
        np.log10(float(grid["maximum"])),
        int(grid["count"]),
    )
    liquidity = float(response["mathcal_L_u"])
    diffusion = float(response["D_u"])
    fixed_rate = float(completion["fixed_operational_rate"])
    fixed_horizon = float(completion["fixed_operational_horizon"])
    eta = float(completion["participation_eta"])
    background_flux = float(completion["background_flux_J"])
    participation_rate = eta * background_flux

    scenarios = {}
    rate = np.full_like(q, fixed_rate)
    horizon = q / rate
    impact = undamped_completion_impact(rate, horizon, liquidity, diffusion)
    scenarios["fixed_operational_rate"] = {
        "Q": q,
        "rate": rate,
        "horizon": horizon,
        "calendar_completion": horizon,
        "impact": impact,
        "clock": "identity_t=u",
        "participation": "not_applicable",
        "background_flux": "not_applicable",
        "slope": fitted_slope(q, impact),
    }

    rate = np.full_like(q, participation_rate)
    horizon = q / rate
    impact = undamped_completion_impact(rate, horizon, liquidity, diffusion)
    scenarios["fixed_participation"] = {
        "Q": q,
        "rate": rate,
        "horizon": horizon,
        "calendar_completion": horizon,
        "impact": impact,
        "clock": "identity_t=u",
        "participation": number(eta),
        "background_flux": number(background_flux),
        "slope": fitted_slope(q, impact),
    }

    horizon = np.full_like(q, fixed_horizon)
    rate = q / horizon
    impact = undamped_completion_impact(rate, horizon, liquidity, diffusion)
    scenarios["fixed_operational_horizon"] = {
        "Q": q,
        "rate": rate,
        "horizon": horizon,
        "calendar_completion": horizon,
        "impact": impact,
        "clock": "identity_t=u",
        "participation": "not_applicable",
        "background_flux": "not_applicable",
        "slope": fitted_slope(q, impact),
    }

    base_rate = np.full_like(q, fixed_rate)
    base_horizon = q / base_rate
    base_impact = undamped_completion_impact(
        base_rate, base_horizon, liquidity, diffusion
    )
    for activity in [float(value) for value in config["clock"]["deterministic_activity_grid"]]:
        scenario_id = f"activity_{activity:g}"
        scenarios[scenario_id] = {
            "Q": q,
            "rate": base_rate,
            "horizon": base_horizon,
            "calendar_completion": base_horizon / activity,
            "impact": base_impact,
            "clock": f"U(t)={activity:g}t",
            "participation": "not_applicable",
            "background_flux": "not_applicable",
            "activity": activity,
            "slope": fitted_slope(q, base_impact),
        }
    return scenarios


def write_csv(path: Path, scenarios: dict, config: dict) -> None:
    q_grid = config["completion"]["Q_grid"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "target_id",
                "evidence_class",
                "schedule_id",
                "clock_convention",
                "Q",
                "operational_rate",
                "operational_horizon",
                "calendar_completion_time",
                "participation_eta",
                "background_flux_J",
                "completion_impact",
                "fitted_slope",
                "fit_Q_min",
                "fit_Q_max",
            ]
        )
        for scenario_id, values in scenarios.items():
            evidence = (
                "negative_control"
                if scenario_id == "fixed_operational_horizon"
                else "verification"
                if scenario_id in {"fixed_operational_rate", "fixed_participation"}
                else "clock_illustration"
            )
            for q, rate, horizon, calendar, impact in zip(
                values["Q"],
                values["rate"],
                values["horizon"],
                values["calendar_completion"],
                values["impact"],
                strict=True,
            ):
                writer.writerow(
                    [
                        TARGET,
                        evidence,
                        scenario_id,
                        values["clock"],
                        number(q),
                        number(rate),
                        number(horizon),
                        number(calendar),
                        values["participation"],
                        values["background_flux"],
                        number(impact),
                        number(values["slope"]),
                        number(q_grid["minimum"]),
                        number(q_grid["maximum"]),
                    ]
                )


def write_figure(pdf_path: Path, png_path: Path, scenarios: dict) -> None:
    colors = ["#173f5f", "#3caea3", "#ed553b"]
    fig, (ax_impact, ax_clock) = plt.subplots(1, 2, figsize=(10.8, 4.3))

    fixed_rate = scenarios["fixed_operational_rate"]
    participation = scenarios["fixed_participation"]
    fixed_horizon = scenarios["fixed_operational_horizon"]
    ax_impact.loglog(
        fixed_rate["Q"],
        fixed_rate["impact"],
        color=colors[0],
        linewidth=2.2,
        label=rf"fixed rate: slope {fixed_rate['slope']:.1f}",
    )
    ax_impact.loglog(
        participation["Q"][::4],
        participation["impact"][::4],
        linestyle="none",
        marker="o",
        markersize=4.2,
        markerfacecolor="white",
        markeredgecolor=colors[1],
        markeredgewidth=1.1,
        label=rf"fixed participation: slope {participation['slope']:.1f}",
    )
    ax_impact.loglog(
        fixed_horizon["Q"],
        fixed_horizon["impact"],
        color=colors[2],
        linestyle="--",
        linewidth=2.0,
        label=rf"fixed horizon: slope {fixed_horizon['slope']:.1f}",
    )
    ax_impact.set_xlabel(r"signed volume $Q$")
    ax_impact.set_ylabel(r"completion impact $I(Q)$")
    ax_impact.set_title("(a) Schedule-dependent impact scaling")
    ax_impact.legend(frameon=False, fontsize=8.2)

    for activity, color in zip([0.5, 1.0, 2.0], colors, strict=True):
        values = scenarios[f"activity_{activity:g}"]
        ax_clock.loglog(
            values["Q"],
            values["calendar_completion"],
            color=color,
            linewidth=2.0,
            label=rf"$\alpha_U={activity:g}$",
        )
    ax_clock.set_xlabel(r"signed volume $Q$")
    ax_clock.set_ylabel(r"calendar completion time $t_c$")
    ax_clock.set_title("(b) Clock-dependent calendar duration")
    ax_clock.legend(frameon=False, fontsize=8.5)

    for axis in (ax_impact, ax_clock):
        axis.grid(True, which="major", color="0.88", linewidth=0.55)
        axis.grid(True, which="minor", color="0.94", linewidth=0.35)
        axis.spines[["top", "right"]].set_visible(False)

    fig.suptitle("Completion impact: schedule convention and clock representation")
    fig.tight_layout()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def diagnostics(config: dict, scenarios: dict, csv_path: Path, pdf_path: Path, png_path: Path) -> dict:
    slope_fixed_rate = float(scenarios["fixed_operational_rate"]["slope"])
    slope_participation = float(scenarios["fixed_participation"]["slope"])
    slope_fixed_horizon = float(scenarios["fixed_operational_horizon"]["slope"])
    identity_errors = {}
    for scenario_id, values in scenarios.items():
        identity_errors[scenario_id] = float(
            np.max(np.abs(values["Q"] - values["rate"] * values["horizon"]))
        )

    activity_impacts = [
        scenarios[f"activity_{activity:g}"]["impact"] for activity in [0.5, 1.0, 2.0]
    ]
    clock_invariance = float(
        max(np.max(np.abs(path - activity_impacts[0])) for path in activity_impacts[1:])
    )

    with csv_path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    required = {
        "schedule_id",
        "clock_convention",
        "operational_rate",
        "operational_horizon",
        "calendar_completion_time",
        "participation_eta",
        "background_flux_J",
        "fitted_slope",
        "fit_Q_min",
        "fit_Q_max",
    }
    labels_complete = all(all(row[field] != "" for field in required) for row in rows)
    tolerance = float(config["acceptance"]["slope_abs"])
    checks = {
        "ACC22": abs(slope_fixed_rate - 0.5) <= tolerance
        and abs(slope_participation - 0.5) <= tolerance,
        "ACC23": abs(slope_fixed_horizon - 1.0) <= tolerance,
        "ACC24": labels_complete,
    }
    return {
        "target": TARGET,
        "version": VERSION,
        "checks": checks,
        "fitted_slopes": {
            "fixed_operational_rate": slope_fixed_rate,
            "fixed_participation": slope_participation,
            "fixed_operational_horizon": slope_fixed_horizon,
        },
        "volume_duration_identity_max_abs_errors": identity_errors,
        "operational_impact_clock_invariance_max_abs_error": clock_invariance,
        "schedule_and_clock_labels_complete": labels_complete,
        "checksums": {
            "csv": sha256(csv_path),
            "pdf": sha256(pdf_path),
            "png": sha256(png_path),
        },
    }


def main() -> int:
    with (ROOT / "config" / "RDL-CFG-v1.1.json").open(encoding="utf-8") as stream:
        config = json.load(stream)
    scenarios = build_scenarios(config)
    csv_path = ROOT / "data" / f"RDL-{TARGET}-{VERSION}.csv"
    pdf_path = ROOT / "figures" / "python" / f"RDL-{TARGET}-{VERSION}.pdf"
    png_path = ROOT / "figures" / "python" / f"RDL-{TARGET}-{VERSION}.png"
    write_csv(csv_path, scenarios, config)
    write_figure(pdf_path, png_path, scenarios)
    report = diagnostics(config, scenarios, csv_path, pdf_path, png_path)
    report_path = ROOT / "diagnostics" / f"RDL-{TARGET}-TST-{VERSION}.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["checks"], sort_keys=True))
    return 0 if all(report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
