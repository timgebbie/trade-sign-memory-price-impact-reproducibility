"""Cell-integrated Abel response kernels for the reduced RDL model."""

from __future__ import annotations

import numpy as np
from scipy.special import erf


def abel_cell_weights(
    dt: float,
    n_points: int,
    diffusion: float,
    resilience: float,
) -> np.ndarray:
    """Return exact kernel integrals over uniform causal lag cells."""
    if dt <= 0.0 or n_points < 2 or diffusion <= 0.0 or resilience < 0.0:
        raise ValueError("invalid Abel-kernel grid or parameters")
    edges = np.arange(n_points, dtype=np.float64) * dt
    lower = edges[:-1]
    upper = edges[1:]
    weights = np.zeros(n_points, dtype=np.float64)
    if resilience == 0.0:
        weights[1:] = (np.sqrt(upper) - np.sqrt(lower)) / np.sqrt(
            np.pi * diffusion
        )
    else:
        scale = 2.0 * np.sqrt(diffusion * resilience)
        weights[1:] = (
            erf(np.sqrt(resilience * upper))
            - erf(np.sqrt(resilience * lower))
        ) / scale
    return weights


def piecewise_constant_response(
    interval_rates: np.ndarray,
    dt: float,
    liquidity_slope: float,
    diffusion: float,
    resilience: float,
) -> np.ndarray:
    """Apply the causal cell-integrated Abel convolution."""
    rates = np.asarray(interval_rates, dtype=np.float64)
    if rates.ndim != 1 or rates.size < 1 or liquidity_slope <= 0.0:
        raise ValueError("invalid rate array or liquidity slope")
    n_points = rates.size + 1
    weights = abel_cell_weights(dt, n_points, diffusion, resilience)
    convolution = np.convolve(rates, weights, mode="full")[:n_points]
    return convolution / liquidity_slope
