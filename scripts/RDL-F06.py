#!/usr/bin/env python3
"""Build and diagnose the reduced Abel impact target F06."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from functions.impact import (  # noqa: E402
    constant_rate_analytic,
    constant_rate_numeric,
    front_loaded_rates,
    integrated_abel_cell,
)
from functions.response import piecewise_constant_response  # noqa: E402

TARGET = "F06"
VERSION = "v1.0"


def number(value: float) -> str:
    return format(float(value), ".17g")


def parameter(value: float) -> str:
    return f"{float(value):g}"


def build_grid(response: dict, n_points: int) -> np.ndarray:
    horizon = float(response["post_completion_T_multiple"]) * float(response["T_u"])
    return np.linspace(0.0, horizon, n_points, dtype=np.float64)


def evaluate_constant_paths(config: dict, n_points: int) -> dict[float, dict[str, np.ndarray]]:
    response = config["response"]
    u = build_grid(response, n_points)
    paths = {}
    for resilience in [float(value) for value in response["nu_u_grid"]]:
        analytic = constant_rate_analytic(
            u,
            float(response["mu_0"]),
            float(response["T_u"]),
            float(response["mathcal_L_u"]),
            float(response["D_u"]),
            resilience,
        )
        numerical = constant_rate_numeric(
            u,
            float(response["mu_0"]),
            float(response["T_u"]),
            float(response["mathcal_L_u"]),
            float(response["D_u"]),
            resilience,
        )
        paths[resilience] = {
            "time": u,
            "analytic": analytic,
            "numerical": numerical,
            "residual": numerical - analytic,
        }
    return paths


def write_csv(path: Path, config: dict, paths: dict[float, dict[str, np.ndarray]]) -> None:
    completion = float(config["response"]["T_u"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "target_id",
                "evidence_class",
                "clock",
                "schedule",
                "nu_u",
                "phase",
                "u",
                "impact_analytic",
                "impact_numerical",
                "diagnostic_residual",
            ]
        )
        for resilience, values in paths.items():
            for u, analytic, numerical, residual in zip(
                values["time"],
                values["analytic"],
                values["numerical"],
                values["residual"],
                strict=True,
            ):
                if u < completion:
                    phase = "execution"
                elif np.isclose(u, completion, rtol=0.0, atol=1e-14):
                    phase = "completion"
                else:
                    phase = "relaxation"
                writer.writerow(
                    [
                        TARGET,
                        "verification",
                        "operational_u",
                        "constant_rate_[0,T_u]",
                        parameter(resilience),
                        phase,
                        number(u),
                        number(analytic),
                        number(numerical),
                        number(residual),
                    ]
                )


def write_figure(
    pdf_path: Path,
    png_path: Path,
    config: dict,
    paths: dict[float, dict[str, np.ndarray]],
) -> None:
    completion = float(config["response"]["T_u"])
    colors = ["#173f5f", "#20639b", "#3caea3", "#ed553b"]
    fig, (ax_path, ax_relax) = plt.subplots(1, 2, figsize=(10.8, 4.3))

    for (resilience, values), color in zip(paths.items(), colors, strict=True):
        scaled_time = values["time"] / completion
        label = rf"$\nu_uT_u={resilience:g}$"
        ax_path.plot(scaled_time, values["analytic"], color=color, linewidth=2.0, label=label)
        ax_path.plot(
            scaled_time[::100],
            values["numerical"][::100],
            linestyle="none",
            marker="o",
            markersize=3.2,
            markerfacecolor="white",
            markeredgecolor=color,
            markeredgewidth=0.9,
        )

        mask = values["time"] >= completion
        completion_value = constant_rate_analytic(
            np.array([completion]),
            float(config["response"]["mu_0"]),
            completion,
            float(config["response"]["mathcal_L_u"]),
            float(config["response"]["D_u"]),
            resilience,
        )[0]
        ax_relax.plot(
            scaled_time[mask],
            values["analytic"][mask] / completion_value,
            color=color,
            linewidth=2.0,
            label=label,
        )

    ax_path.axvline(1.0, color="0.25", linestyle=":", linewidth=1.1)
    ax_path.text(1.04, 0.04, "completion", rotation=90, transform=ax_path.get_xaxis_transform(), fontsize=8)
    ax_path.set_xlabel(r"operational time $u/T_u$")
    ax_path.set_ylabel(r"impact displacement $I_u(u)$")
    ax_path.set_title("(a) Execution and relaxation")
    ax_path.legend(frameon=False, fontsize=8.5)

    ax_relax.axvline(1.0, color="0.25", linestyle=":", linewidth=1.1)
    ax_relax.set_xlabel(r"operational time $u/T_u$")
    ax_relax.set_ylabel(r"normalized relaxation $I_u(u)/I_u(T_u)$")
    ax_relax.set_title("(b) Post-completion decay")
    ax_relax.legend(frameon=False, fontsize=8.5)

    for axis in (ax_path, ax_relax):
        axis.grid(True, color="0.90", linewidth=0.55)
        axis.spines[["top", "right"]].set_visible(False)
        axis.set_xlim(0.0, float(config["response"]["post_completion_T_multiple"]))

    fig.suptitle("Constant-rate Abel impact and post-completion relaxation")
    fig.tight_layout()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def relative_linf(numerical: np.ndarray, reference: np.ndarray) -> float:
    scale = float(np.max(np.abs(reference)))
    return float(np.max(np.abs(numerical - reference)) / scale)


def refinement_errors(config: dict) -> dict[str, dict[str, float]]:
    response = config["response"]
    grids = [int(value) for value in response["refinement_grid_points"]]
    results: dict[float, dict[int, np.ndarray]] = {}
    for resilience in [float(value) for value in response["nu_u_grid"]]:
        results[resilience] = {}
        for n_points in grids:
            u = build_grid(response, n_points)
            dt = float(u[1] - u[0])
            rates = front_loaded_rates(
                u, float(response["mu_0"]), float(response["T_u"])
            )
            results[resilience][n_points] = piecewise_constant_response(
                rates,
                dt,
                float(response["mathcal_L_u"]),
                float(response["D_u"]),
                resilience,
            )

    errors = {}
    for resilience, paths in results.items():
        coarse, middle, fine = (paths[n] for n in grids)
        errors[parameter(resilience)] = {
            "1001_to_2001": relative_linf(coarse, middle[::2]),
            "2001_to_4001": relative_linf(middle, fine[::2]),
        }
    return errors


def diagnostics(config: dict, paths: dict[float, dict[str, np.ndarray]]) -> dict:
    response = config["response"]
    acceptance = config["acceptance"]
    completion = float(response["T_u"])
    scale_errors = {
        parameter(resilience): relative_linf(values["numerical"], values["analytic"])
        for resilience, values in paths.items()
    }

    continuity = {}
    for resilience in paths:
        execution = integrated_abel_cell(
            np.array([0.0]),
            np.array([completion]),
            float(response["D_u"]),
            resilience,
        )[0]
        relaxation = integrated_abel_cell(
            np.array([completion - completion]),
            np.array([completion]),
            float(response["D_u"]),
            resilience,
        )[0]
        continuity[parameter(resilience)] = float(abs(execution - relaxation))

    u = paths[0.0]["time"]
    undamped = constant_rate_analytic(
        u,
        float(response["mu_0"]),
        completion,
        float(response["mathcal_L_u"]),
        float(response["D_u"]),
        0.0,
    )
    near_zero = constant_rate_analytic(
        u,
        float(response["mu_0"]),
        completion,
        float(response["mathcal_L_u"]),
        float(response["D_u"]),
        1e-12,
    )
    nu_limit_error = relative_linf(near_zero, undamped)
    refinement = refinement_errors(config)
    refinement_max = max(value["2001_to_4001"] for value in refinement.values())

    checks = {
        "ACC11": scale_errors["0"] <= float(acceptance["analytic_numeric_relative"]),
        "ACC12": all(
            value <= float(acceptance["analytic_numeric_relative"])
            for key, value in scale_errors.items()
            if key != "0"
        )
        and nu_limit_error <= float(acceptance["analytic_numeric_relative"]),
        "ACC13": all(
            value <= float(acceptance["exact_identity_abs"])
            for value in continuity.values()
        ),
        "ACC14": refinement_max <= float(acceptance["grid_refinement_relative"]),
    }
    return {
        "target": TARGET,
        "version": VERSION,
        "checks": checks,
        "constant_rate_relative_linf_errors": scale_errors,
        "nu_to_zero_relative_linf_error": nu_limit_error,
        "completion_continuity_absolute_errors": continuity,
        "front_loaded_schedule_refinement": refinement,
        "maximum_2001_to_4001_refinement_change": refinement_max,
        "nonlinear_volterra_status": "inactive",
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    config_path = ROOT / "config" / "RDL-CFG-v1.1.json"
    with config_path.open(encoding="utf-8") as stream:
        config = json.load(stream)

    n_points = int(config["response"]["grid_points"])
    paths = evaluate_constant_paths(config, n_points)
    csv_path = ROOT / "data" / f"RDL-{TARGET}-{VERSION}.csv"
    pdf_path = ROOT / "figures" / "python" / f"RDL-{TARGET}-{VERSION}.pdf"
    png_path = ROOT / "figures" / "python" / f"RDL-{TARGET}-{VERSION}.png"
    write_csv(csv_path, config, paths)
    write_figure(pdf_path, png_path, config, paths)

    report = diagnostics(config, paths)
    report["checksums"] = {
        "csv": sha256(csv_path),
        "pdf": sha256(pdf_path),
        "png": sha256(png_path),
    }
    report_path = ROOT / "diagnostics" / f"RDL-{TARGET}-TST-{VERSION}.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["checks"], sort_keys=True))
    return 0 if all(report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
