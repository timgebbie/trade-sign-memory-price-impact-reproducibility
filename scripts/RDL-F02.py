#!/usr/bin/env python3
"""Build and diagnose the two route-separated clock projections for F02."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("SOURCE_DATE_EPOCH", "0")

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from functions.clocks import (  # noqa: E402
    event_timestamps,
    inverse_event_counter,
    operational_clock,
    waiting_times,
)
from functions.impact import constant_rate_analytic  # noqa: E402

TARGET = "F02"
VERSION = "v1.2"


def number(value: float) -> str:
    return format(float(value), ".17g")


def build_route_a(config: dict, target_config: dict) -> dict[str, dict[str, np.ndarray | float | dict]]:
    clock = config["clock"]
    master_seed = int(config["random"]["master_seed"])
    n_events = int(clock["metaorder_events"])
    constant_completion = float(n_events)
    horizon = (
        float(target_config["route_a"]["calendar_horizon_constant_completion_multiples"])
        * constant_completion
    )
    calendar = np.linspace(
        0.0, horizon, int(clock["direct_calendar_grid_points"]), dtype=np.float64
    )
    seed_ids = {"constant": 0, "exponential": 1, "lomax_finite_mean": 2, "pareto_infinite_mean": 3}
    paths = {}
    for scenario in clock["waiting_scenarios"]:
        clock_id = scenario["id"]
        waits = waiting_times(
            scenario, n_events, master_seed, seed_ids[clock_id]
        )
        timestamps = event_timestamps(waits)
        counter = inverse_event_counter(timestamps, calendar)
        volume = counter.astype(np.float64) / n_events
        paths[clock_id] = {
            "scenario": scenario,
            "waits": waits,
            "timestamps": timestamps,
            "calendar": calendar,
            "counter": counter,
            "volume": volume,
            "completion": float(timestamps[-1]),
            "constant_completion": constant_completion,
        }
    return paths


def build_route_b(config: dict, target_config: dict) -> dict[str, dict[str, np.ndarray | float]]:
    clock = config["clock"]
    response = config["response"]
    calendar = np.linspace(
        0.0,
        float(target_config["route_b"]["calendar_horizon_T_u_multiples"])
        * float(response["T_u"]),
        int(clock["operational_calendar_grid_points"]),
        dtype=np.float64,
    )
    paths = {}
    for activity in [float(value) for value in clock["deterministic_activity_grid"]]:
        operational = operational_clock(calendar, activity)
        impact = constant_rate_analytic(
            operational,
            float(response["mu_0"]),
            float(response["T_u"]),
            float(response["mathcal_L_u"]),
            float(response["D_u"]),
            0.0,
        )
        clock_id = f"activity_{activity:g}"
        paths[clock_id] = {
            "activity": activity,
            "calendar": calendar,
            "operational": operational,
            "impact": impact,
            "calendar_completion": float(response["T_u"]) / activity,
            "operational_domain_max": (
                float(target_config["route_b"]["operational_response_domain_T_u_multiples"])
                * float(response["T_u"])
            ),
        }
    return paths


def write_waits(path: Path, route_a: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "target_id",
                "route_id",
                "clock_id",
                "event_index",
                "waiting_time",
                "event_timestamp",
                "declared_mean",
                "seed_context",
            ]
        )
        for clock_id, values in route_a.items():
            scenario = values["scenario"]
            declared_mean = "" if scenario["mean"] is None else number(scenario["mean"])
            seed_context = "deterministic" if clock_id == "constant" else f"[20260710,2,{ {'exponential':1,'lomax_finite_mean':2,'pareto_infinite_mean':3}[clock_id] },0]"
            for event, wait in enumerate(values["waits"], start=1):
                writer.writerow(
                    [
                        TARGET,
                        "A",
                        clock_id,
                        event,
                        number(wait),
                        number(values["timestamps"][event]),
                        declared_mean,
                        seed_context,
                    ]
                )


def write_data(path: Path, route_a: dict, route_b: dict, target_config: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            [
                "target_id",
                "evidence_class",
                "route_id",
                "clock_id",
                "native_object",
                "projection_mapping",
                "native_time",
                "calendar_time",
                "calendar_time_normalized",
                "event_count",
                "cumulative_volume",
                "impact",
            ]
        )
        for clock_id, values in route_a.items():
            for calendar, counter, volume in zip(
                values["calendar"], values["counter"], values["volume"], strict=True
            ):
                writer.writerow(
                    [
                        TARGET,
                        "illustration",
                        "A",
                        clock_id,
                        target_config["route_a"]["native_object"],
                        target_config["route_a"]["mapping"],
                        int(counter),
                        number(calendar),
                        number(calendar / values["constant_completion"]),
                        int(counter),
                        number(volume),
                        "",
                    ]
                )
        for clock_id, values in route_b.items():
            for calendar, operational, impact in zip(
                values["calendar"], values["operational"], values["impact"], strict=True
            ):
                writer.writerow(
                    [
                        TARGET,
                        "illustration",
                        "B",
                        clock_id,
                        target_config["route_b"]["native_object"],
                        target_config["route_b"]["mapping"],
                        number(operational),
                        number(calendar),
                        number(calendar),
                        "",
                        "",
                        number(impact),
                    ]
                )


def write_figure(
    pdf_path: Path,
    png_path: Path,
    route_a: dict,
    route_b: dict,
    target_config: dict,
) -> None:
    colors_a = ["#173f5f", "#20639b", "#3caea3", "#ed553b"]
    colors_b = ["#6a3d9a", "#b15928", "#1b9e77"]
    labels_a = {
        "constant": "constant",
        "exponential": "exponential",
        "lomax_finite_mean": "Lomax (finite mean)",
        "pareto_infinite_mean": "Pareto-I (infinite mean)",
    }
    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(12.2, 5.35))

    for (clock_id, values), color in zip(route_a.items(), colors_a, strict=True):
        ax_a.step(
            values["calendar"] / values["constant_completion"],
            values["volume"],
            where="post",
            color=color,
            linewidth=1.8,
            label=labels_a[clock_id],
        )
    ax_a.set_xlabel(r"calendar time $t/T_c^{\mathrm{const}}$ (event-counter route)")
    ax_a.set_ylabel(r"normalized cumulative executed volume $Q_{N_t}/Q$")
    ax_a.set_title(target_config["figure"]["panel_a_title"], fontsize=10.4, pad=12)
    ax_a.set_xlim(
        0.0,
        float(target_config["route_a"]["calendar_horizon_constant_completion_multiples"]),
    )
    ax_a.set_ylim(-0.02, 1.04)
    ax_a.legend(frameon=False, fontsize=7.8, loc="center right")
    route_a_position = target_config["figure"]["route_a_mapping_position_axes"]
    ax_a.text(
        float(route_a_position[0]),
        float(route_a_position[1]),
        r"$Q_m\;\overset{N_t}{\longrightarrow}\;Q_{N_t}$",
        transform=ax_a.transAxes,
        ha="center",
        va="center",
        fontsize=9.2,
    )
    pareto = route_a["pareto_infinite_mean"]
    ax_a.annotate(
        "completion outside window\n(one realization; no population mean)",
        xy=(
            pareto["calendar"][-1] / pareto["constant_completion"],
            pareto["volume"][-1],
        ),
        xytext=(2.12, 0.36),
        fontsize=7.5,
        color=colors_a[-1],
        arrowprops={"arrowstyle": "->", "color": colors_a[-1], "linewidth": 0.8},
        ha="left",
        va="center",
    )

    for (clock_id, values), color in zip(route_b.items(), colors_b, strict=True):
        activity = values["activity"]
        label = rf"$\alpha_U={activity:g}$"
        ax_b.plot(
            values["calendar"],
            values["impact"],
            color=color,
            linewidth=2.0,
            label=label,
        )
    ax_b.set_xlabel(r"calendar time $t/T_u$ (activity-clock route)")
    ax_b.set_ylabel(r"subordinated reduced Abel impact $I_B(t)=I_u(U(t))$")
    ax_b.set_title(target_config["figure"]["panel_b_title"], fontsize=10.4, pad=12)
    ax_b.set_xlim(
        0.0,
        float(target_config["route_b"]["calendar_horizon_T_u_multiples"]),
    )
    ax_b.legend(frameon=False, fontsize=8.3)
    route_b_position = target_config["figure"]["route_b_mapping_position_axes"]
    ax_b.text(
        float(route_b_position[0]),
        float(route_b_position[1]),
        r"$I_u(u)\;\overset{u=U(t)}{\longrightarrow}\;I_u(U(t))$",
        transform=ax_b.transAxes,
        ha="right",
        va="top",
        fontsize=9.2,
    )

    for axis in (ax_a, ax_b):
        axis.grid(True, color="0.90", linewidth=0.55)
        axis.spines[["top", "right"]].set_visible(False)

    fig.suptitle(target_config["figure"]["title"], fontsize=13.0, y=0.965)
    fig.text(
        0.5,
        0.035,
        target_config["figure"]["clarification"],
        ha="center",
        va="bottom",
        fontsize=8.1,
        wrap=True,
    )
    fig.subplots_adjust(left=0.075, right=0.985, top=0.82, bottom=0.23, wspace=0.29)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def diagnostics(
    config: dict,
    target_config: dict,
    route_a: dict,
    route_b: dict,
    data_path: Path,
    waits_path: Path,
) -> dict:
    n_events = int(config["clock"]["metaorder_events"])
    direct = {}
    inversion = {}
    preservation = {}
    for clock_id, values in route_a.items():
        waits = values["waits"]
        timestamps = values["timestamps"]
        counter_at_events = inverse_event_counter(timestamps, timestamps)
        direct[clock_id] = {
            "waits_positive": bool(np.all(waits > 0.0)),
            "timestamps_strict": bool(np.all(np.diff(timestamps) > 0.0)),
            "counter_nondecreasing": bool(np.all(np.diff(values["counter"]) >= 0)),
        }
        inversion[clock_id] = int(
            np.max(np.abs(counter_at_events - np.arange(n_events + 1)))
        )
        terminal_counter = int(inverse_event_counter(timestamps, np.array([timestamps[-1]]))[0])
        preservation[clock_id] = {
            "event_order_exact": bool(np.array_equal(counter_at_events, np.arange(n_events + 1))),
            "terminal_volume_error": float(abs(terminal_counter / n_events - 1.0)),
        }

    operational = {}
    for clock_id, values in route_b.items():
        activity = values["activity"]
        operational[clock_id] = {
            "clock_monotone": bool(np.all(np.diff(values["operational"]) >= 0.0)),
            "domain_max": float(values["operational"][-1]),
            "declared_response_domain_max": float(values["operational_domain_max"]),
            "domain_clipped": bool(
                values["operational"][-1] > values["operational_domain_max"] + 1e-14
            ),
            "response_finite": bool(np.all(np.isfinite(values["impact"]))),
            "identity_path_error": 0.0,
        }
        if np.isclose(activity, 1.0):
            response = config["response"]
            reference = constant_rate_analytic(
                values["calendar"],
                float(response["mu_0"]),
                float(response["T_u"]),
                float(response["mathcal_L_u"]),
                float(response["D_u"]),
                0.0,
            )
            operational[clock_id]["identity_path_error"] = float(
                np.max(np.abs(values["impact"] - reference))
            )

    with data_path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    route_fields_separated = all(
        (row["route_id"] == "A" and row["impact"] == "")
        or (
            row["route_id"] == "B"
            and row["event_count"] == ""
            and row["cumulative_volume"] == ""
        )
        for row in rows
    )
    native_objects_labeled = all(
        (
            row["route_id"] == "A"
            and row["native_object"] == target_config["route_a"]["native_object"]
            and row["projection_mapping"] == target_config["route_a"]["mapping"]
        )
        or (
            row["route_id"] == "B"
            and row["native_object"] == target_config["route_b"]["native_object"]
            and row["projection_mapping"] == target_config["route_b"]["mapping"]
        )
        for row in rows
    )
    different_native_objects = (
        target_config["route_a"]["native_object"]
        != target_config["route_b"]["native_object"]
    )
    route_separation = (
        route_fields_separated and native_objects_labeled and different_native_objects
    )

    checks = {
        "ACC15": all(all(result.values()) for result in direct.values()),
        "ACC16": all(error == 0 for error in inversion.values()),
        "ACC17": all(
            result["event_order_exact"] and result["terminal_volume_error"] <= 1e-12
            for result in preservation.values()
        ),
        "ACC18": all(
            result["clock_monotone"]
            and not result["domain_clipped"]
            and result["identity_path_error"] <= 1e-12
            for result in operational.values()
        ),
        "ACC19": route_separation,
    }
    return {
        "target": TARGET,
        "version": VERSION,
        "checks": checks,
        "direct_clock_validity": direct,
        "maximum_inversion_index_error": inversion,
        "event_and_volume_preservation": preservation,
        "operational_clock_validity": operational,
        "route_separation": route_separation,
        "route_semantics": {
            "route_fields_separated": route_fields_separated,
            "native_objects_labeled": native_objects_labeled,
            "different_native_objects": different_native_objects,
            "figure_clarification": target_config["figure"]["clarification"],
        },
        "realized_completion_ratios": {
            key: float(value["completion"] / value["constant_completion"])
            for key, value in route_a.items()
        },
        "checksums": {
            "data_csv": sha256(data_path),
            "waits_csv": sha256(waits_path),
        },
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    with (ROOT / "config" / "RDL-CFG-v1.1.json").open(encoding="utf-8") as stream:
        config = json.load(stream)
    with (ROOT / "config" / f"RDL-F02-{VERSION}.json").open(encoding="utf-8") as stream:
        target_config = json.load(stream)
    route_a = build_route_a(config, target_config)
    route_b = build_route_b(config, target_config)

    data_path = ROOT / "data" / f"RDL-{TARGET}-{VERSION}.csv"
    waits_path = ROOT / "raw-outputs" / f"RDL-{TARGET}-WAITS-{VERSION}.csv"
    pdf_path = ROOT / "figures" / "python" / f"RDL-{TARGET}-{VERSION}.pdf"
    png_path = ROOT / "figures" / "python" / f"RDL-{TARGET}-{VERSION}.png"
    write_waits(waits_path, route_a)
    write_data(data_path, route_a, route_b, target_config)
    write_figure(pdf_path, png_path, route_a, route_b, target_config)

    report = diagnostics(config, target_config, route_a, route_b, data_path, waits_path)
    report["checksums"]["pdf"] = sha256(pdf_path)
    report["checksums"]["png"] = sha256(png_path)
    report_path = ROOT / "diagnostics" / f"RDL-{TARGET}-TST-{VERSION}.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["checks"], sort_keys=True))
    return 0 if all(report["checks"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
