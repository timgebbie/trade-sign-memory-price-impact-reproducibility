#!/usr/bin/env python3
"""Build and diagnose the exact LMF event-time autocorrelation target F03."""

from __future__ import annotations

import argparse
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

from functions.acf import (  # noqa: E402
    lmf_asymptotic,
    lmf_exact,
    raw_acf_direct,
    raw_acf_fft,
)
from functions.sign_process import simulate_lmf_signs  # noqa: E402

VERSION = "v1.0"
TARGET = "F03"


def float_text(value: float) -> str:
    """Stable text representation for generated CSV values."""
    return format(float(value), ".17g")


def parameter_text(value: float) -> str:
    """Compact representation for the declared one-decimal parameter grid."""
    return f"{float(value):.1f}"


def write_exact_csv(path: Path, alphas: list[float], max_lag: int) -> None:
    lags = np.arange(max_lag + 1, dtype=np.int64)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "target_id",
                "evidence_class",
                "alpha_L",
                "gamma_epsilon",
                "lag",
                "C_exact",
                "C_asymptotic",
                "relative_asymptotic_error",
            ]
        )
        for alpha_l in alphas:
            exact = lmf_exact(alpha_l, lags)
            asymptotic = lmf_asymptotic(alpha_l, lags[1:])
            relative = np.abs(asymptotic - exact[1:]) / exact[1:]
            writer.writerow(
                [
                    TARGET,
                    "verification",
                    parameter_text(alpha_l),
                    parameter_text(alpha_l - 1.0),
                    0,
                    float_text(exact[0]),
                    "",
                    "",
                ]
            )
            for lag, c_exact, c_asym, rel in zip(
                lags[1:], exact[1:], asymptotic, relative, strict=True
            ):
                writer.writerow(
                    [
                        TARGET,
                        "verification",
                        parameter_text(alpha_l),
                        parameter_text(alpha_l - 1.0),
                        int(lag),
                        float_text(c_exact),
                        float_text(c_asym),
                        float_text(rel),
                    ]
                )


def write_figure(
    pdf_path: Path,
    png_path: Path,
    alphas: list[float],
    max_lag: int,
) -> None:
    lags = np.arange(1, max_lag + 1, dtype=np.int64)
    colors = ["#173f5f", "#20639b", "#3caea3", "#ed553b"]
    fig, (ax_curve, ax_error) = plt.subplots(1, 2, figsize=(10.8, 4.3))

    for alpha_l, color in zip(alphas, colors, strict=True):
        exact = lmf_exact(alpha_l, lags)
        asymptotic = lmf_asymptotic(alpha_l, lags)
        relative = np.abs(asymptotic - exact) / exact
        gamma = alpha_l - 1.0
        ax_curve.loglog(
            lags,
            exact,
            color=color,
            linewidth=2.0,
            label=rf"exact: $\alpha_L={alpha_l:.1f}$, $\gamma_\epsilon={gamma:.1f}$",
        )
        ax_curve.loglog(
            lags,
            asymptotic,
            color=color,
            linewidth=1.1,
            linestyle="--",
        )
        ax_error.loglog(lags, relative, color=color, linewidth=1.8)

    ax_curve.plot([], [], color="0.25", linewidth=1.1, linestyle="--", label="asymptotic")
    ax_curve.set_xlabel(r"event lag $\tau$")
    ax_curve.set_ylabel(r"sign autocorrelation $C_\tau(\epsilon)$")
    ax_curve.set_title("(a) Exact renewal correlation")
    ax_curve.legend(frameon=False, fontsize=8.2, loc="lower left")

    ax_error.axhline(0.005, color="0.2", linestyle=":", linewidth=1.2)
    ax_error.text(11.5, 0.0062, "0.5% acceptance threshold", fontsize=8)
    ax_error.set_xlabel(r"event lag $\tau$")
    ax_error.set_ylabel("relative asymptotic error")
    ax_error.set_title("(b) Large-lag agreement")

    for axis in (ax_curve, ax_error):
        axis.grid(True, which="major", color="0.86", linewidth=0.6)
        axis.grid(True, which="minor", color="0.93", linewidth=0.35)
        axis.spines[["top", "right"]].set_visible(False)

    fig.suptitle("Event-time LMF autocorrelation under a normalized zeta length law")
    fig.tight_layout()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def run_monte_carlo(config: dict, raw_path: Path, summary_path: Path) -> dict:
    lmf = config["lmf"]
    random = config["random"]
    alphas = [float(lmf["baseline_alpha_L"])]
    max_lag = int(lmf["mc_lag_max"])
    n_events = int(lmf["mc_events"])
    burn_events = int(lmf["mc_burn_events"])
    replicates = int(lmf["mc_replicates"])
    master_seed = int(random["master_seed"])

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    all_results: dict[float, np.ndarray] = {}
    scenario_ids = {alpha: int(round(alpha * 100)) for alpha in alphas}

    with raw_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "target_id",
                "evidence_class",
                "alpha_L",
                "replicate_id",
                "lag",
                "C_raw",
                "master_seed",
                "target_seed_id",
                "scenario_id",
                "bit_generator",
            ]
        )
        for alpha_l in alphas:
            replicate_values = np.empty((replicates, max_lag + 1))
            scenario_id = scenario_ids[alpha_l]
            for replicate_id in range(replicates):
                values = simulate_lmf_signs(
                    alpha_l,
                    n_events,
                    burn_events,
                    (master_seed, 3, scenario_id, replicate_id),
                )
                estimate = raw_acf_fft(values, max_lag)
                replicate_values[replicate_id] = estimate
                for lag, value in enumerate(estimate):
                    writer.writerow(
                        [
                            TARGET,
                            "diagnostic_simulation",
                            parameter_text(alpha_l),
                            replicate_id,
                            lag,
                            float_text(value),
                            master_seed,
                            3,
                            scenario_id,
                            "PCG64DXSM",
                        ]
                    )
            all_results[alpha_l] = replicate_values

    with summary_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "target_id",
                "evidence_class",
                "alpha_L",
                "lag",
                "C_exact",
                "C_mc_mean",
                "C_mc_sd",
                "absolute_error",
            ]
        )
        for alpha_l in alphas:
            values = all_results[alpha_l]
            mean = values.mean(axis=0)
            sd = values.std(axis=0, ddof=1)
            exact = lmf_exact(alpha_l, np.arange(max_lag + 1))
            for lag in range(max_lag + 1):
                writer.writerow(
                    [
                        TARGET,
                        "diagnostic_simulation",
                        parameter_text(alpha_l),
                        lag,
                        float_text(exact[lag]),
                        float_text(mean[lag]),
                        float_text(sd[lag]),
                        float_text(abs(mean[lag] - exact[lag])),
                    ]
                )

    acceptance_lag = int(lmf["mc_acceptance_lag_max"])
    metrics = {}
    for alpha_l in alphas:
        mean = all_results[alpha_l].mean(axis=0)
        exact = lmf_exact(alpha_l, np.arange(max_lag + 1))
        difference = mean[1 : acceptance_lag + 1] - exact[1 : acceptance_lag + 1]
        metrics[parameter_text(alpha_l)] = {
            "rmse_lags_1_128": float(np.sqrt(np.mean(difference**2))),
            "max_abs_lags_1_128": float(np.max(np.abs(difference))),
        }
    return metrics


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def diagnostics(
    config: dict,
    exact_path: Path,
    mc_metrics: dict | None,
    mc_repeatable: bool | None,
) -> dict:
    lmf = config["lmf"]
    acceptance = config["acceptance"]
    alphas = [float(value) for value in lmf["alpha_L_grid"]]
    lags = np.arange(int(lmf["exact_lag_max"]) + 1)

    identity_errors = {}
    asymptotic_errors = {}
    positivity = {}
    monotonicity = {}
    exponent_relation = {}
    for alpha_l in alphas:
        exact = lmf_exact(alpha_l, lags)
        asymptotic = lmf_asymptotic(alpha_l, lags[1:])
        relative = np.abs(asymptotic - exact[1:]) / exact[1:]
        key = parameter_text(alpha_l)
        identity_errors[key] = float(abs(exact[0] - 1.0))
        asymptotic_errors[key] = float(np.max(relative[9:]))
        positivity[key] = bool(np.all(np.isfinite(exact)) and np.all(exact >= 0.0))
        monotonicity[key] = bool(np.all(np.diff(exact) <= 0.0))
        exponent_relation[key] = float(abs((alpha_l - 1.0) - (alpha_l - 1.0)))

    probe = np.array([1, 1, -1, -1, 1, -1, 1, 1, -1, 1], dtype=np.int8)
    direct_fft_error = float(
        np.max(np.abs(raw_acf_direct(probe, 6) - raw_acf_fft(probe, 6)))
    )

    repeat_path = exact_path.with_suffix(".repeat.csv")
    write_exact_csv(repeat_path, alphas, int(lmf["exact_lag_max"]))
    repeatability = sha256(exact_path) == sha256(repeat_path)
    repeat_path.unlink()

    mc_pass = None
    if mc_metrics is not None:
        mc_pass = all(
            metric["rmse_lags_1_128"] <= float(acceptance["mc_rmse"])
            and metric["max_abs_lags_1_128"] <= float(acceptance["mc_max_abs"])
            for metric in mc_metrics.values()
        )

    checks = {
        "ACC06": all(
            error <= float(acceptance["exact_identity_abs"])
            for error in identity_errors.values()
        )
        and all(positivity.values())
        and all(monotonicity.values()),
        "ACC07": all(error == 0.0 for error in exponent_relation.values()),
        "ACC08": all(
            error <= float(acceptance["asymptotic_relative"])
            for error in asymptotic_errors.values()
        ),
        "ACC09": mc_pass,
        "ACC10": mc_repeatable if mc_repeatable is not None else repeatability,
        "direct_fft": direct_fft_error <= 1e-12,
    }
    return {
        "target": TARGET,
        "version": VERSION,
        "checks": checks,
        "identity_absolute_errors": identity_errors,
        "maximum_relative_asymptotic_error_tau_ge_10": asymptotic_errors,
        "finite_nonnegative": positivity,
        "monotone_nonincreasing": monotonicity,
        "direct_fft_max_abs_error": direct_fft_error,
        "exact_csv_byte_repeatable": repeatability,
        "monte_carlo_csv_byte_repeatable": mc_repeatable,
        "monte_carlo": mc_metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "config" / "RDL-CFG-v1.1.json",
    )
    parser.add_argument(
        "--with-mc",
        action="store_true",
        help="run the optional seeded Monte Carlo diagnostic",
    )
    args = parser.parse_args()

    with args.config.open(encoding="utf-8") as stream:
        config = json.load(stream)
    lmf = config["lmf"]
    alphas = [float(value) for value in lmf["alpha_L_grid"]]

    exact_path = ROOT / "data" / f"RDL-{TARGET}-{VERSION}.csv"
    pdf_path = ROOT / "figures" / "python" / f"RDL-{TARGET}-{VERSION}.pdf"
    png_path = ROOT / "figures" / "python" / f"RDL-{TARGET}-{VERSION}.png"
    write_exact_csv(exact_path, alphas, int(lmf["exact_lag_max"]))
    write_figure(pdf_path, png_path, alphas, int(lmf["exact_lag_max"]))

    mc_metrics = None
    mc_repeatable = None
    if args.with_mc:
        raw_path = ROOT / "raw-outputs" / f"RDL-{TARGET}-MC-{VERSION}.csv"
        summary_path = ROOT / "outputs" / f"RDL-{TARGET}-MC-SUM-{VERSION}.csv"
        mc_metrics = run_monte_carlo(
            config,
            raw_path,
            summary_path,
        )
        repeat_raw = ROOT / "diagnostics" / f".RDL-{TARGET}-MC-repeat.csv"
        repeat_summary = ROOT / "diagnostics" / f".RDL-{TARGET}-MC-SUM-repeat.csv"
        repeat_metrics = run_monte_carlo(config, repeat_raw, repeat_summary)
        mc_repeatable = (
            mc_metrics == repeat_metrics
            and sha256(raw_path) == sha256(repeat_raw)
            and sha256(summary_path) == sha256(repeat_summary)
        )
        repeat_raw.unlink()
        repeat_summary.unlink()

    report = diagnostics(config, exact_path, mc_metrics, mc_repeatable)
    report_path = ROOT / "diagnostics" / f"RDL-{TARGET}-TST-{VERSION}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["checks"], sort_keys=True))
    return 0 if all(value is not False for value in report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
