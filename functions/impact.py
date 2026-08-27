"""Analytic and gridded impact paths for target F06."""

from __future__ import annotations

import numpy as np
from scipy.special import erf

from .response import piecewise_constant_response


def integrated_abel_cell(
    lower: np.ndarray,
    upper: np.ndarray,
    diffusion: float,
    resilience: float,
) -> np.ndarray:
    """Integrate the damped Abel kernel between non-negative limits."""
    a = np.asarray(lower, dtype=np.float64)
    b = np.asarray(upper, dtype=np.float64)
    if diffusion <= 0.0 or resilience < 0.0 or np.any(a < 0.0) or np.any(b < a):
        raise ValueError("invalid integration limits or response parameters")
    if resilience == 0.0:
        return (np.sqrt(b) - np.sqrt(a)) / np.sqrt(np.pi * diffusion)
    return (
        erf(np.sqrt(resilience * b)) - erf(np.sqrt(resilience * a))
    ) / (2.0 * np.sqrt(diffusion * resilience))


def constant_rate_analytic(
    times: np.ndarray,
    rate: float,
    completion_time: float,
    liquidity_slope: float,
    diffusion: float,
    resilience: float,
) -> np.ndarray:
    """Closed execution and relaxation path for a constant-rate meta-order."""
    u = np.asarray(times, dtype=np.float64)
    if np.any(u < 0.0) or completion_time <= 0.0 or liquidity_slope <= 0.0:
        raise ValueError("invalid time grid or execution parameters")
    lower = np.maximum(u - completion_time, 0.0)
    return (
        rate
        * integrated_abel_cell(lower, u, diffusion, resilience)
        / liquidity_slope
    )


def constant_rate_numeric(
    times: np.ndarray,
    rate: float,
    completion_time: float,
    liquidity_slope: float,
    diffusion: float,
    resilience: float,
) -> np.ndarray:
    """Cell-integrated convolution for the constant-rate schedule."""
    u = np.asarray(times, dtype=np.float64)
    if u.ndim != 1 or u.size < 2 or not np.allclose(np.diff(u), u[1] - u[0]):
        raise ValueError("times must be a uniform one-dimensional grid")
    dt = float(u[1] - u[0])
    starts = u[:-1]
    rates = np.where(starts < completion_time, rate, 0.0)
    return piecewise_constant_response(
        rates, dt, liquidity_slope, diffusion, resilience
    )


def front_loaded_rates(
    times: np.ndarray,
    rate: float,
    completion_time: float,
) -> np.ndarray:
    """Midpoint-sampled triangular schedule with the same total target volume."""
    u = np.asarray(times, dtype=np.float64)
    dt = float(u[1] - u[0])
    midpoints = u[:-1] + 0.5 * dt
    return np.where(
        midpoints < completion_time,
        2.0 * rate * (1.0 - midpoints / completion_time),
        0.0,
    )


def undamped_completion_impact(
    rate: np.ndarray | float,
    completion_time: np.ndarray | float,
    liquidity_slope: float,
    diffusion: float,
) -> np.ndarray:
    """Completion impact for the undamped constant-rate Abel benchmark."""
    mu = np.asarray(rate, dtype=np.float64)
    horizon = np.asarray(completion_time, dtype=np.float64)
    if np.any(mu < 0.0) or np.any(horizon <= 0.0):
        raise ValueError("rate must be non-negative and completion time positive")
    if liquidity_slope <= 0.0 or diffusion <= 0.0:
        raise ValueError("liquidity slope and diffusion must be positive")
    return mu * np.sqrt(horizon / (np.pi * diffusion)) / liquidity_slope
