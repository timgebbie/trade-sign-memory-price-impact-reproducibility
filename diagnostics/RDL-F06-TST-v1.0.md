# RDL F06 Diagnostic Report v1.0

Date: 10 July 2026  
Workflow state: W06/F06 implementation plus W07/F06 diagnostics  
Outcome: pass

## Acceptance results

| Gate | Result | Evidence |
| --- | --- | --- |
| ACC11 | PASS | Undamped analytic/numerical relative L-infinity error is `3.936e-16`. |
| ACC12 | PASS | Worst positive-resilience analytic/numerical error is `4.266e-16`; the `nu_u -> 0` relative error is `9.353e-13`, below `1e-9`. |
| ACC13 | PASS | Execution and relaxation formulae agree exactly at completion for every declared resilience. |
| ACC14 | PASS | The worst front-loaded-schedule change from 2001 to 4001 points is `3.955e-5`, below `0.005`. |
| Visual QA | PASS | The one-page PDF has readable axes legends markers and completion annotation with no clipping or overlap. |

## Output checksums

- CSV: `8cd576aed83e208aa28852c4216b37df7aa3b3e9f58b04cf3b53d528ceb185cf`.
- PDF: `f7ce975af7a3c2149fb03e6a77ee9b52c7ee07ce91a7707a46f1de8a18b6b26f`.
- PNG: `03fba5ffb94730ff93ed66b0c1fdc4327d4542aa9f03128a45a077302286e83e`.

## Scope

The plotted paths verify the reduced locally linear full-line Abel response in
operational time. The nonlinear Volterra branch remains inactive. No finite
lattice/PDE simulation calibration or empirical comparison was performed.
