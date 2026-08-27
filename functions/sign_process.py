"""Sequential non-overlapping LMF sign-process simulation."""

from __future__ import annotations

import numpy as np


def simulate_lmf_signs(
    alpha_l: float,
    n_events: int,
    burn_events: int,
    seed_components: tuple[int, int, int, int],
    draw_batch: int = 4096,
) -> np.ndarray:
    """Simulate exactly ``n_events`` signs after a deterministic burn window."""
    if alpha_l <= 1.0:
        raise ValueError("alpha_l must exceed one")
    if n_events <= 0 or burn_events < 0:
        raise ValueError("event counts must be non-negative with n_events positive")

    seed = np.random.SeedSequence(seed_components)
    rng = np.random.Generator(np.random.PCG64DXSM(seed))
    total = n_events + burn_events
    signs = np.empty(total, dtype=np.int8)
    position = 0

    while position < total:
        remaining = total - position
        lengths = rng.zipf(alpha_l + 1.0, size=draw_batch).astype(np.int64)
        meta_signs = rng.choice(np.array([-1, 1], dtype=np.int8), size=draw_batch)
        cumulative = np.cumsum(lengths, dtype=np.int64)
        crossing = int(np.searchsorted(cumulative, remaining, side="left"))

        if crossing < draw_batch:
            used_lengths = lengths[: crossing + 1].copy()
            previous = int(cumulative[crossing - 1]) if crossing else 0
            used_lengths[-1] = remaining - previous
            block = np.repeat(meta_signs[: crossing + 1], used_lengths)
        else:
            block = np.repeat(meta_signs, lengths)

        signs[position : position + block.size] = block
        position += block.size

    return signs[burn_events:]
