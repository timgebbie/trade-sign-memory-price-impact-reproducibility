# RDL Source Freeze v1.0

Date: 10 July 2026  
Artefact status: Stage 2 source-freeze record

All frozen copies were compared byte-for-byte with the supplied files. The
short frozen filenames change paths only; they do not change file contents.

| Frozen file | Supplied file | SHA-256 | Role |
|---|---|---|---|
| `RDL-SRC-v0.tex` | `CATG-RD2LMF-arXiv-v3.tex` | `6b5851e15a0c8f1a489b2f74cf54f85bca43c961e0bb3141a1d2656ad0c0ae9b` | Primary theory |
| `RDL-REF-v0.bib` | `RD2LMF-v2.bib` | `8ff04e3e56afe28c14641ee55f84d1574628614fe648ae2aa623d0bf0971a777` | Primary bibliography |
| `RAP-SRC-v0.tex` | `CATG-AdjointProjection-arXiv-v1.6.tex` | `d304b0657d630303f465f7ef78f82479cd4820de2e870e25df10b6224806de95` | Prior theory/notation precedent |
| `RAP-REF-v0.bib` | `AdjointProjection-v1.6.bib` | `6f1070d3ca30644aa097990e06fbd3dae62273321ae7eeef8574df52916752b4` | Prior bibliography precedent |
| `RDL-PLN-SRC-v0.tex` | `LMF_SQRL_figure_supplement_project_plan_v1_0(1).tex` | `ed13d79f5d5991b6ab4ce0ba96a66d906b134eb7b9ad44d6f273c3068c8bf303` | Original provisional plan |
| `RBV-PRECEDENT-v1.0.md` | `reaction-boundary-vol-surface-stage13(2).zip` | `72e3afb5e141d295e0b300a6f75e2f49826fe29df16b63039d15a415f5605a10` | External prior-development precedent; large archive deliberately not embedded |
| `CPG-SRC-v0.zip` | `Computational-Project-Guide-Bundle-v1.0-rc(3).zip` | `abc230b0a2868fc0e728a6656c9776bbb632066efa2f7d32596bf003a858a21b` | Controlling workflow |

## Recorded observations

1. The AdjointProjection filename is v1.6 while its internal version comment
   says v1.5. The frozen source preserves this discrepancy.
2. The RD2LMF bibliography contains duplicated keys for
   `montroll1965random`, `metzler2000random`, `meerschaert2004limit` and
   `mainardi2010mwright`. The frozen bibliography is not repaired.
3. The original project-plan source has a local font-expansion compilation
   issue. It is retained unchanged. Any active revised plan will be a new
   versioned control artefact.

## Package-size rule

Primary theory, bibliographies, the original plan and the controlling workflow
remain local frozen inputs. The prior reaction-boundary project is retained by
verified pointer because it is a precedent rather than a runtime dependency.

## Protection rule

Never edit a file in `source` in place. If a corrected or updated paper source
is supplied later, preserve it as a new frozen version and update this record.
