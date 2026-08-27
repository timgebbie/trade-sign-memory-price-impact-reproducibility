# RDL F02 Diagnostic Report v1.2

Date: 10 July 2026  
Workflow state: controlled pre-W10 F02 presentation revision  
Outcome: pass; operator accepted

## Requested presentation checks

| Check | Result | Evidence |
| --- | --- | --- |
| Route A mapping placement | PASS | The mapping label is centred in the open interior of Panel A at axes coordinates `(0.56, 0.82)`. |
| Mapping-label boundaries | PASS | Both mapping labels are plain black text with no bounding box or grey border. |
| Content preservation | PASS | Curves, axes, titles, annotation, legends, domains and clarification are unchanged from F02 v1.1. |
| PDF visual QA | PASS | The one-page PDF render has no clipping, overlap or obscured data. |

## Acceptance results

| Gate | Result | Evidence |
| --- | --- | --- |
| ACC15 | PASS | Every wait is positive; every timestamp sequence is strictly increasing; every displayed counter is nondecreasing. |
| ACC16 | PASS | `N(T_m)=m` exactly for all 257 timestamp nodes under every direct clock. |
| ACC17 | PASS | Event order is exact and terminal volume error is zero for every direct clock. |
| ACC18 | PASS | All activity clocks are monotone, every response value is finite, the identity-clock path error is zero, and `u=6` remains within the declared domain. |
| ACC19 | PASS | Every row declares its distinct native object and mapping, route-specific fields remain separated, and no composed path is present. |

## Output checksums

- Data CSV: `7d6cf80f347c24e7d6c3616d62815726f2f29662bc35c89e8d55ea907fb25e96`.
- Waiting-time CSV: `08f417bafa9269a1ab4f024b62905377329e75c9c45f61e8fb1a037f62ba0c05`.
- PDF: `324322b98541e6c3990f52829473a210e87f1293c49caecb91a4b0422ea414d6`.
- PNG: `40fc7a00a5309e7e421b763bc7792d6b0fb8e057bd8a34dbcd3e343a8568902f`.

The scientific interpretation remains that the panels are separate mappings
of different native objects. No pointwise correspondence, sequential double
subordination or joint stochastic coupling is implemented or implied.
