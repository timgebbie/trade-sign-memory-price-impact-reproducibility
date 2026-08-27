#!/usr/bin/env python3
"""Build and diagnose the finite-width child-order response target F05."""

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

from functions.impact import constant_rate_analytic  # noqa: E402
from functions.response import piecewise_constant_response  # noqa: E402

TARGET = "F05"
VERSION = "v1.1"


def number(value: float) -> str:
    return format(float(value), ".17g")


def parameter(value: float) -> str:
    return f"{float(value):g}"


def build_paths(config: dict) -> dict[tuple[float, float], dict[str, np.ndarray | float]]:
    response = config["response"]
    n_points = int(response["grid_points"])
    horizon = float(response["pulse_horizon"])
    u = np.linspace(0.0, horizon, n_points, dtype=np.float64)
    dt = float(u[1] - u[0])
    q_0 = float(response["pulse_q_0"])
    widths = [float(value) for value in response["pulse_tau_0_grid"]]
    resiliences = [0.0, 1.0, 4.0]
    paths = {}

    for width in widths:
        rate = q_0 / width
        starts = u[:-1]
        interval_rates = np.where(starts < width, rate, 0.0)
        for resilience in resiliences:
            analytic = constant_rate_analytic(
                u,
                rate,
                width,
                float(response["mathcal_L_u"]),
                float(response["D_u"]),
                resilience,
            )
            numerical = piecewise_constant_response(
                interval_rates,
                dt,
                float(response["mathcal_L_u"]),
                float(response["D_u"]),
                resilience,
            )
            paths[(width, resilience)] = {
                "time": u,
                "rate": rate,
                "interval_rates": interval_rates,
                "analytic": analytic,
                "numerical": numerical,
                "residual": numerical - analytic,
                "delivered_area": float(np.sum(interval_rates) * dt),
            }
    return paths


def write_csv(path: Path, config: dict, paths: dict) -> None:
    q_0 = float(config["response"]["pulse_q_0"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "target_id",
                "evidence_class",
                "clock",
                "schedule",
                "q_0",
                "tau_0",
                "nu_u",
                "phase",
                "u",
                "forcing_rate",
                "response_analytic",
                "response_numerical",
                "diagnostic_residual",
            ]
        )
        for (width, resilience), values in paths.items():
            for u, analytic, numerical, residual in zip(
                values["time"],
                values["analytic"],
                values["numerical"],
                values["residual"],
                strict=True,
            ):
                if u < width:
                    phase = "delivery"
                    forcing = values["rate"]
                elif np.isclose(u, width, rtol=0.0, atol=1e-14):
                    phase = "delivery_completion"
                    forcing = 0.0
                else:
                    phase = "relaxation"
                    forcing = 0.0
                writer.writerow(
                    [
                        TARGET,
                        "illustration_and_verification",
                        "operational_u",
                        "finite_width_top_hat",
                        parameter(q_0),
                        parameter(width),
                        parameter(resilience),
                        phase,
                        number(u),
                        number(forcing),
                        number(analytic),
                        number(numerical),
                        number(residual),
                    ]
                )


def write_figure(pdf_path: Path, png_path: Path, config: dict, paths: dict) -> None:
    response = config["response"]
    baseline_width = float(response["pulse_tau_0"])
    colors = ["#173f5f", "#3caea3", "#ed553b"]
    fig, (ax_damping, ax_width) = plt.subplots(1, 2, figsize=(10.8, 4.3))

    for resilience, color in zip([0.0, 1.0, 4.0], colors, strict=True):
        values = paths[(baseline_width, resilience)]
        ax_damping.plot(
            values["time"],
            values["analytic"],
            color=color,
            linewidth=2.0,
            label=rf"$\nu_u={resilience:g}$",
        )
        ax_damping.plot(
            values["time"][::100],
            values["numerical"][::100],
            linestyle="none",
            marker="o",
            markersize=3.2,
            markerfacecolor="white",
            markeredgecolor=color,
            markeredgewidth=0.9,
        )

    for width, color in zip(
        [float(value) for value in response["pulse_tau_0_grid"]], colors, strict=True
    ):
        values = paths[(width, 0.0)]
        ax_width.plot(
            values["time"],
            values["analytic"],
            color=color,
            linewidth=2.0,
            label=rf"$\tau_0={width:g}$",
        )
        ax_width.plot(
            values["time"][::100],
            values["numerical"][::100],
            linestyle="none",
            marker="o",
            markersize=3.2,
            markerfacecolor="white",
            markeredgecolor=color,
            markeredgewidth=0.9,
        )

    ax_damping.axvline(baseline_width, color="0.25", linestyle=":", linewidth=1.0)
    ax_damping.set_title(rf"(a) Damping at $\tau_0={baseline_width:g}$")
    ax_damping.legend(frameon=False, fontsize=8.5)

    for width, color in zip(
        [float(value) for value in response["pulse_tau_0_grid"]], colors, strict=True
    ):
        ax_width.axvline(width, color=color, linestyle=":", linewidth=0.8, alpha=0.65)
    ax_width.set_title(r"(b) Width sensitivity at $\nu_u=0$")
    ax_width.legend(frameon=False, fontsize=8.5)

    for axis in (ax_damping, ax_width):
        axis.set_xlabel(r"operational time $u$")
        axis.set_ylabel(r"child-order response $I_u(u)$ (log scale)")
        axis.set_yscale("log")
        axis.set_xlim(0.0, float(response["pulse_horizon"]))
        axis.grid(True, which="major", color="0.88", linewidth=0.55)
        axis.grid(True, which="minor", color="0.94", linewidth=0.35)
        axis.spines[["top", "right"]].set_visible(False)

    fig.suptitle("Finite-width single-child-order response")
    fig.tight_layout()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def relative_linf(numerical: np.ndarray, reference: np.ndarray) -> float:
    return float(
        np.max(np.abs(numerical - reference)) / np.max(np.abs(reference))
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def diagnostics(config: dict, paths: dict, csv_path: Path, pdf_path: Path, png_path: Path) -> dict:
    q_0 = float(config["response"]["pulse_q_0"])
    area_errors = {
        f"tau={parameter(width)},nu={parameter(resilience)}": float(
            abs(values["delivered_area"] - q_0)
        )
        for (width, resilience), values in paths.items()
    }
    finite_origin = {
        f"tau={parameter(width)},nu={parameter(resilience)}": bool(
            np.all(np.isfinite(values["numerical"]))
            and np.all(np.isfinite(values["analytic"]))
            and values["numerical"][0] == 0.0
            and values["analytic"][0] == 0.0
        )
        for (width, resilience), values in paths.items()
    }
    analytic_errors = {
        f"tau={parameter(width)},nu={parameter(resilience)}": relative_linf(
            values["numerical"], values["analytic"]
        )
        for (width, resilience), values in paths.items()
    }
    acceptance = config["acceptance"]
    checks = {
        "ACC20": all(error <= 1e-12 for error in area_errors.values()),
        "ACC21": all(finite_origin.values()),
        "F06_kernel_inheritance": all(
            error <= float(acceptance["analytic_numeric_relative"])
            for error in analytic_errors.values()
        ),
    }
    return {
        "target": TARGET,
        "version": VERSION,
        "checks": checks,
        "pulse_area_absolute_errors": area_errors,
        "finite_and_zero_at_origin": finite_origin,
        "analytic_numeric_relative_linf_errors": analytic_errors,
        "pre_forcing_response": 0.0,
        "checksums": {
            "csv": sha256(csv_path),
            "pdf": sha256(pdf_path),
            "png": sha256(png_path),
        },
    }


def main() -> int:
    with (ROOT / "config" / "RDL-CFG-v1.1.json").open(encoding="utf-8") as stream:
        config = json.load(stream)
    paths = build_paths(config)
    csv_path = ROOT / "data" / f"RDL-{TARGET}-{VERSION}.csv"
    pdf_path = ROOT / "figures" / "python" / f"RDL-{TARGET}-{VERSION}.pdf"
    png_path = ROOT / "figures" / "python" / f"RDL-{TARGET}-{VERSION}.png"
    write_csv(csv_path, config, paths)
    write_figure(pdf_path, png_path, config, paths)
    report = diagnostics(config, paths, csv_path, pdf_path, png_path)
    report_path = ROOT / "diagnostics" / f"RDL-{TARGET}-TST-{VERSION}.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["checks"], sort_keys=True))
    return 0 if all(report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
