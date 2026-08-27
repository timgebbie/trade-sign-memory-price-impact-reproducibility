# RDL Configuration Policy v1.0

Artefact status: Stage 2 configuration-control policy.

## Governing principles

1. Scientific constants, numerical controls, scenario choices and random seeds
   must not be hidden in plotting scripts.
2. Every accepted output must map to a source object, configuration, script,
   derived-data file, caption and diagnostic status.
3. A changed parameter, seed, estimator, algorithm or caption claim requires a
   recorded version or controlled revision.
4. Frozen theory sources are never edited in place.
5. Exploratory outputs remain labelled exploratory until diagnostics justify
   promotion.

## Planned configuration classes

- baseline scientific and dimensionless parameters;
- parameter ranges and sensitivity grids;
- meta-order and sign-process scenarios;
- deterministic and stochastic clock scenarios;
- impact and execution-schedule scenarios;
- autocorrelation estimator and lag controls;
- figure and table production routes;
- random seeds and simulation sizes;
- numerical tolerances and acceptance thresholds.

The exact filenames and schemas will be frozen during Stages 3--5.

## Runtime policy

The controlling route will use standalone Python scripts and reusable helper
functions. A later `run_all.py` should separate validation (`--check`) from a
full rebuild (`--rebuild`). The release candidate will record explicit package
versions. Docker, cloud services, databases and package publication are not
part of the current project.

## Output policy

- `raw-outputs` preserves direct stochastic or numerical results where useful.
- `data/derived` contains plot-ready and table-ready CSV files.
- `figures` and `tables` contain publication objects, never the only evidence.
- `captions` contains rich standalone caption drafts.
- `diagnostics` records test inputs, outcomes and acceptance status.
- superseded accepted artefacts move to `archive`; they are not silently
  overwritten.

## Checkpoint rule

Every accepted checkpoint must contain the current source pointer/freeze,
theory-to-code map, parameter and configuration registers, active scripts and
functions, run notes, accepted outputs, captions, manifest, diagnostics and
unresolved issues appropriate to that stage.
