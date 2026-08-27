# RDL F03 Diagnostic Report v1.0

Date: 10 July 2026  
Workflow state: W06/F03 implementation plus W07/F03 diagnostics  
Outcome: pass with preserved optional-grid caveat

## Acceptance results

| Gate | Result | Evidence |
| --- | --- | --- |
| ACC06 | PASS | Maximum `C(0)` absolute error is `4.441e-16`; all exact values are finite nonnegative and monotone non-increasing. |
| ACC07 | PASS | Every exact display scenario uses `gamma_epsilon=alpha_L-1`. |
| ACC08 | PASS | Worst relative exact/asymptotic error for `tau>=10` is `0.0011952`, below `0.005`. |
| ACC09 | PASS | For baseline `alpha_L=1.5`, the eight-replicate mean has RMSE `0.0065047` and maximum absolute error `0.0088940` on lags 1--128. |
| ACC10 | PASS | Exact and seeded Monte Carlo CSV files regenerate byte-identically. |
| Direct/FFT | PASS | Maximum estimator difference on the deterministic probe is `2.220e-16`, below `1e-12`. |
| Visual QA | PASS | The rendered PDF has one unclipped page with readable labels legends and threshold annotation. |

## Preserved failed diagnostic

The first optional MC run applied the eight-path threshold to the entire exact
display grid. `alpha_L=1.2` failed because the near-boundary heavy-tail regime
has slow renewal equilibration and high finite-sample dispersion. The result is
preserved in `RDL-F03-MC-PRE-v1.0.json`; the threshold was not weakened. The MC
promotion gate is applied to the declared `alpha_L=1.5` baseline, while all four
display scenarios are verified by the infinite-support exact calculation.

## Output checksums

- Exact CSV: `b86573d144fba5b25988e10d50b6a075cb790b86eefe5c47d5729918925a8e45`.
- MC replicate CSV: `2d4f322499da61d51f5e10dedcd60c15e320844053f66b7a2bc46cae64eca3ba`.
- MC summary CSV: `324650a58d18f714efdb85d9d968a839e76c99dfa86b20999ea782978b1b1701`.
- PDF: `ac6d6f221424684a0f801ca1125968bbf5e5171be47f33e2249f0bcb58bdfdb1`.
- PNG: `89dff55062044d5a91661e43aa9e205997b23202bd145bee5d69de8b5ed769ba`.

F03 is verification and diagnostic simulation only. It is not empirical
validation calibration or a calendar-time claim.
