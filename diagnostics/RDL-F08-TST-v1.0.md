# RDL F08 Diagnostic Report v1.0

Date: 10 July 2026  
Workflow state: W06/F08 implementation plus W07/F08 diagnostics  
Outcome: pass

## Acceptance results

| Gate | Result | Evidence |
| --- | --- | --- |
| ACC25 | PASS | The primary-to-source arrow states signed localized forcing with nonnegative child-order magnitude and a strictly positive front-window aggregate. The source-to-flux arrow separately states local monotonicity, forcing dominance and common event resolution. |
| ACC26 | PASS | The figure reports no numerical agreement statistic or lattice/PDE result. It uses the event-induced flux increment rather than the raw flux and makes no price- or return-sign identification. |
| Visual QA | PASS | The standalone and A4 inclusion outputs compile without errors or warnings. High-resolution inspection found no clipping, overlap or unreadable label. |
| Repeatability | PASS | Two clean builds with fixed PDF metadata produced byte-identical PDF and PNG outputs. |

## Build evidence

- Standalone source: `figures/tikz/RDL-F08-v1.0.tex`.
- Standalone output: one page, `589.291 x 244.48 pt`.
- Source SHA-256:
  `f8140c1285fe2bb3eebf8a9d760285eca4bbefe898dc296f611e99ec3af42b7a`.
- PDF SHA-256:
  `162c08bc68cc0f92ae644043f23378c0bf5cab2853e9608ba62d1133ee349d23`.
- PNG SHA-256:
  `6d45f8d068e22642402a8b33d07778cd06f8548f61df7198f1ea2e5841d6e67f`.
- Inclusion fixture: `diagnostics/RDL-F08-INCLUDE-v1.0.tex`.
- Reference environment: pdfTeX from TeX Live 2023 and latexmk 4.83.

## Scope check

F08 is a conditional conceptual map, not a sign-agreement simulation. Its
failure branches identify diffusion delay, moving-front effects, curvature,
background sources, discretization and event-resolution effects without
claiming that any has been quantified in the current project.
