"""Direct event counters and operational activity clocks for RDL."""

from __future__ import annotations

import numpy as np


def waiting_times(
    scenario: dict,
    n_events: int,
    master_seed: int,
    scenario_id: int,
) -> np.ndarray:
    """Generate the declared deterministic or seeded positive waiting times."""
    law = scenario["law"]
    if law == "constant":
        waits = np.full(n_events, float(scenario["value"]), dtype=np.float64)
    else:
        seed = np.random.SeedSequence([master_seed, 2, scenario_id, 0])
        rng = np.random.Generator(np.random.PCG64DXSM(seed))
        if law == "exponential":
            waits = rng.exponential(float(scenario["scale"]), size=n_events)
        elif law == "lomax":
            waits = float(scenario["scale"]) * rng.pareto(
                float(scenario["shape"]), size=n_events
            )
        elif law == "pareto_I":
            waits = float(scenario["scale"]) * (
                1.0 + rng.pareto(float(scenario["shape"]), size=n_events)
            )
        else:
            raise ValueError(f"unsupported waiting-time law: {law}")
    if np.any(~np.isfinite(waits)) or np.any(waits <= 0.0):
        raise ValueError("waiting times must be finite and strictly positive")
    return waits


def event_timestamps(waits: np.ndarray) -> np.ndarray:
    """Return T_0=0 followed by cumulative event timestamps."""
    increments = np.asarray(waits, dtype=np.float64)
    if increments.ndim != 1 or np.any(increments <= 0.0):
        raise ValueError("waits must be a positive one-dimensional array")
    return np.concatenate(([0.0], np.cumsum(increments)))


def inverse_event_counter(timestamps: np.ndarray, calendar_times: np.ndarray) -> np.ndarray:
    """Right-continuous N_t=max{m:T_m<=t}, capped at the final event."""
    stamps = np.asarray(timestamps, dtype=np.float64)
    times = np.asarray(calendar_times, dtype=np.float64)
    if stamps.ndim != 1 or times.ndim != 1 or np.any(np.diff(stamps) <= 0.0):
        raise ValueError("timestamps must be strictly increasing")
    return np.searchsorted(stamps, times, side="right") - 1


def operational_clock(calendar_times: np.ndarray, activity: float) -> np.ndarray:
    """Deterministic monotone operational clock U(t)=activity*t."""
    times = np.asarray(calendar_times, dtype=np.float64)
    if activity <= 0.0 or np.any(times < 0.0):
        raise ValueError("activity must be positive and calendar time non-negative")
    return activity * times
