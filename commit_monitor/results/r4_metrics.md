
### N=10, original attacks: attack seqs=18, cal seqs=200, held-out benign seqs=100
| method | pair recall | full chain | det@1% | det@5% | AUC | held-out FPR @1%/@5% | tokens/benign seq |
|---|---|---|---|---|---|---|---|
| per-commit | - | - | 0.19 [0.02, 0.52] | 0.31 [0.09, 0.59] | 0.85 [0.75, 0.95] | 0.01/0.05 | 9137 |
| joint, dependency linker | 0.67 | 0.33 | 0.28 [0.00, 0.67] | 0.51 [0.22, 0.81] | 0.79 [0.59, 0.94] | 0.00/0.12 | 13373 |
| joint, dependency + sens-only 2-hop | 0.78 | 0.67 | 0.22 [0.00, 0.57] | 0.44 [0.21, 0.71] | 0.80 [0.65, 0.91] | 0.00/0.11 | 13719 |
| joint, effect-summary linker | 0.39 | 0.17 | 0.10 [0.00, 0.25] | 0.44 [0.24, 0.79] | 0.75 [0.63, 0.87] | 0.03/0.17 | 13031 |

### N=10, identifier renaming (round 1-3 perturbation): attack seqs=18, cal seqs=200, held-out benign seqs=100
| method | pair recall | full chain | det@1% | det@5% | AUC | held-out FPR @1%/@5% | tokens/benign seq |
|---|---|---|---|---|---|---|---|
| per-commit | - | - | 0.36 [0.03, 0.69] | 0.45 [0.15, 0.78] | 0.90 [0.78, 0.98] | 0.01/0.05 | 9137 |
| joint, dependency linker | 0.43 | 0.28 | 0.11 [0.00, 0.25] | 0.32 [0.14, 0.55] | 0.74 [0.60, 0.85] | 0.00/0.12 | 13373 |
| joint, dependency + sens-only 2-hop | 0.48 | 0.33 | 0.17 [0.00, 0.39] | 0.31 [0.10, 0.54] | 0.71 [0.51, 0.87] | 0.00/0.11 | 13719 |
| joint, effect-summary linker | 0.33 | 0.17 | 0.09 [0.00, 0.22] | 0.35 [0.15, 0.66] | 0.75 [0.63, 0.85] | 0.03/0.17 | 13031 |

### N=10, adaptive: dependency hiding: attack seqs=18, cal seqs=200, held-out benign seqs=100
| method | pair recall | full chain | det@1% | det@5% | AUC | held-out FPR @1%/@5% | tokens/benign seq |
|---|---|---|---|---|---|---|---|
| per-commit | - | - | 0.36 [0.03, 0.69] | 0.45 [0.15, 0.77] | 0.89 [0.78, 0.97] | 0.01/0.05 | 9137 |
| joint, dependency linker | 0.50 | 0.33 | 0.11 [0.00, 0.30] | 0.36 [0.17, 0.59] | 0.74 [0.56, 0.87] | 0.00/0.12 | 13373 |
| joint, dependency + sens-only 2-hop | 0.54 | 0.33 | 0.22 [0.07, 0.43] | 0.44 [0.24, 0.63] | 0.80 [0.66, 0.89] | 0.00/0.11 | 13719 |
| joint, effect-summary linker | 0.52 | 0.33 | 0.15 [0.00, 0.31] | 0.49 [0.29, 0.83] | 0.79 [0.67, 0.88] | 0.03/0.17 | 13031 |