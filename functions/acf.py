"""Exact LMF renewal correlations and raw autocorrelation estimators."""

from __future__ import annotations

import numpy as np
from scipy.special import zeta


def lmf_exact(alpha_l: float, lags: np.ndarray) -> np.ndarray:
    """Evaluate the infinite-support LMF renewal correlation."""
    if alpha_l <= 1.0:
        raise ValueError("alpha_l must exceed one")
    tau = np.asarray(lags, dtype=np.float64)
    if np.any(tau < 0) or np.any(tau != np.floor(tau)):
        raise ValueError("lags must be non-negative integers")
    numerator = zeta(alpha_l, tau + 1.0) - tau * zeta(
        alpha_l + 1.0, tau + 1.0
    )
    return numerator / zeta(alpha_l)


def lmf_asymptotic(alpha_l: float, lags: np.ndarray) -> np.ndarray:
    """Evaluate the leading large-lag LMF asymptotic reference."""
    if alpha_l <= 1.0:
        raise ValueError("alpha_l must exceed one")
    tau = np.asarray(lags, dtype=np.float64)
    if np.any(tau <= 0):
        raise ValueError("asymptotic lags must be strictly positive")
    coefficient = 1.0 / (
        alpha_l * (alpha_l - 1.0) * zeta(alpha_l)
    )
    return coefficient * tau ** (1.0 - alpha_l)


def raw_acf_direct(values: np.ndarray, max_lag: int) -> np.ndarray:
    """Raw lag-product estimator evaluated directly."""
    x = np.asarray(values, dtype=np.float64)
    if x.ndim != 1 or x.size <= max_lag or max_lag < 0:
        raise ValueError("require a one-dimensional series longer than max_lag")
    result = np.empty(max_lag + 1, dtype=np.float64)
    for lag in range(max_lag + 1):
        result[lag] = np.dot(x[: x.size - lag], x[lag:]) / (x.size - lag)
    return result


def raw_acf_fft(values: np.ndarray, max_lag: int) -> np.ndarray:
    """Raw lag-product estimator using a zero-padded FFT."""
    x = np.asarray(values, dtype=np.float64)
    if x.ndim != 1 or x.size <= max_lag or max_lag < 0:
        raise ValueError("require a one-dimensional series longer than max_lag")
    fft_size = 1 << (2 * x.size - 1).bit_length()
    spectrum = np.fft.rfft(x, n=fft_size)
    products = np.fft.irfft(spectrum * spectrum.conjugate(), n=fft_size)
    denominators = x.size - np.arange(max_lag + 1, dtype=np.float64)
    return products[: max_lag + 1] / denominators
