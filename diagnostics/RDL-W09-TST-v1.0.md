# RDL W09 Sensitivity, Robustness and Edge-Case Report v1.0

Date: 10 July 2026  
Artefact status: diagnostic output  
Outcome: pass with retained finite-sample and clock fragilities

## Machine checks

All ten W09 checks pass:

- existing F02, F03, F05, F06 and F07 machine diagnostics and ACC03--ACC26;
- analytic LMF boundary checks;
- invalid-input rejection;
- deterministic stochastic-seed repeatability;
- direct and operational clock invariants;
- Abel grid-edge checks;
- finite-width pulse conservation and finiteness;
- completion-schedule and scale identities;
- simulation-only routing; and
- unchanged conditional, blocked, deferred and future-only scope.

The generated CSV and JSON are byte-identical across repeated runs. Their
SHA-256 values are:

- CSV: `22d2f80d09ca9b0ad6bd69bb4a96bf6b1fc7d032f680bc2669020a4f985990c3`;
- JSON: `4e6a5f08aae0d63d581eca54d6bce9abecd798624083f33a153349fdb2018207`.

## Robust results

The exact LMF working form remains finite, nonnegative and monotone at
`alpha_L=1.01`, `1.05`, `1.99` and `2.5` over sampled lags through 10000, with
`C(0)` agreeing with one within the declared identity tolerance. The
`alpha_L=2.5` special case is computationally valid but lies beyond the
non-summable long-memory range; it is an edge check, not an active display
scenario.

For the Abel response, the largest relative analytic-versus-cell-integrated
error over `nu_u` in `{0,4}` and grids `{1001,2001,4001}` is
`4.015586739209996e-15`. Fixed-area pulse checks at widths `0.0025` and `0.04`
have exactly zero area error and finite peaks. Extended volume tests from
`10^-6` to `10^6` retain slopes `0.5000000000000001` at fixed rate and
`1.0000000000000004` at fixed horizon. Doubling liquidity or multiplying
diffusion by four halves completion impact, as required by the analytic scale
identities.

Every direct-clock seed context preserves positive waits, strict timestamp
ordering and the documented inverse-counter identity. Operational clocks
remain monotone at activity edges `0.25` and `4`. All seven invalid or
degenerate input cases are rejected explicitly with `ValueError`.

## Retained fragilities

The reduced Monte Carlo sensitivity grid is deliberately not a promotion test.
For `alpha_L=1.2`, the mean replicate RMSE over lags 1--64 is approximately
`0.1024` at 16384 events and `0.1271` at 65536 events; the corresponding seed
ranges are approximately `0.1836` and `0.1423`. The lack of monotone
improvement in this small four-seed grid reinforces the near-boundary
finite-sample fragility already preserved in `RDL-F03-MC-PRE-v1.0.json`.

For `alpha_L=1.5`, increasing the short-run sample from 16384 to 65536 events
reduces mean RMSE from approximately `0.03240` to `0.02776` and the seed range
from `0.01055` to `0.00506`. These reduced runs remain above ACC09 and do not
replace the accepted eight-replicate 262144-event diagnostic.

Calendar completion time is intrinsically seed-sensitive for stochastic
waiting laws. Across four seed contexts the completion-time spreads are
`12.25` for exponential waits, `75.23` for finite-mean Lomax waits and
`14754.89` for the infinite-mean Pareto-I illustration. Event-order invariants
still pass. No population mean is assigned to the infinite-mean scenario.

Pulse peaks are regularisation-sensitive: the peak changes from approximately
`11.28` at width `0.0025` to `2.82` at width `0.04`, while area is preserved.
Completion scaling remains schedule-dependent, and F08 flux-sign equivalence
remains conditional. These are interpretation boundaries, not numerical
failures.

## Workflow boundary

No empirical data or data window exists in RDL, so empirical-window
sensitivity is not applicable. F04 remains conditional, F09 blocked, F10
deferred, the nonlinear Volterra solver inactive and the full lattice/PDE
model future-only. W09 therefore closes without adding a publication figure or
activating a new target.
