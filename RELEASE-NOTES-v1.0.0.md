# Release notes — v1.0.0

This is the first public reproducibility release for:

Chris Angstmann and Tim Gebbie, *Revisiting Trade-sign Long-memory and
Square-root Law price impact*, arXiv:2606.16269.

The release contains the retained simulation and analytical verification route
for the RD2LMF project: event-time LMF correlation, route-separated clock
projections, finite-width child-order response, reaction-boundary impact and
relaxation, completion-schedule scaling, robustness diagnostics, four
science/methods tables, and the conditional sign-convention schematic.

The complete reproduction command is:

```bash
python scripts/run_all.py
```

The public route deliberately executes F03 with its seeded Monte Carlo option
before the aggregate W09 robustness gate. The release also corrects the compact
development package's stale table diagnostic so that it reports the four
retained public tables T01--T04 rather than removed governance tables.

No empirical market data, calibration, optimisation, trading strategy, or full
lattice/PDE latent-order-book simulation is included in v1.0.0.
