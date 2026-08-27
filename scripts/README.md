# Reproduction scripts

The public entry point is:

```bash
python scripts/run_all.py
```

It executes the retained scientific route in dependency order:

1. F02 route-separated clock projections;
2. F03 exact LMF autocorrelation **with the seeded Monte Carlo diagnostic**;
3. F05 finite-width child-order response;
4. F06 reaction-boundary impact and relaxation;
5. F07 completion-schedule and clock comparison;
6. T01--T04 table staging;
7. W09 robustness diagnostics; and
8. release-surface verification.

The F03 `--with-mc` option is part of the public route because W09 verifies the
full accepted F03 diagnostic, including ACC09. Each target script can also be
run separately when developing or inspecting a single output.
