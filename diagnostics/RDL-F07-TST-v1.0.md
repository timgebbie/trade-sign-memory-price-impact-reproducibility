# RDL F07 Diagnostic Report v1.0

Date: 10 July 2026  
Workflow state: W06/F07 implementation plus W07/F07 diagnostics  
Outcome: pass

## Acceptance results

| Gate | Result | Evidence |
| --- | --- | --- |
| ACC22 | PASS | Fixed-rate and fixed-participation slopes are `0.5000000000000001`. |
| ACC23 | PASS | The fixed-horizon negative-control slope is `1.0000000000000004`. |
| ACC24 | PASS | Every CSV row records schedule rate horizon participation clock convention and fit window. |
| Additional | PASS | `Q=mu_0 T_u` errors and clock-induced operational-impact differences are exactly zero. |
| Visual QA | PASS | Log-log axes slopes overlapping square-root schedules and the slope-one negative control are clear and unclipped. |

## Output checksums

- CSV: `60cd914f17529e2a3298dcccae6f9d4d23c5350af98617e46168998013f6c345`.
- PDF: `fa76e27207d2a2dabe341472b592e36498eb9f3436217375433ae221569b5b5d`.
- PNG: `b1bae7d608738aaea10deb95a72f494bc44f8cd86839be68163a965d11664948`.

The reference slopes follow from declared analytic schedule identities. They
are not empirical fits or a universal claim across schedule conventions.
