
### FRESH split, attacks=orig: attack seqs=18, cal=200, held-out=100
| method | AUC | det@1% (realized FPR) | det@5% (realized FPR) | conformal det@5% (realized) | matched det @5% FPR | matched det @12% FPR |
|---|---|---|---|---|---|---|
| per-commit | 0.83 [0.70, 0.95] | 0.19 (0.01) | 0.30 (0.04) | 0.17 (0.00) | 0.33 [0.06, 0.71] | 0.52 [0.15, 0.86] |
| joint, boundary linker | 0.83 [0.77, 0.89] | 0.29 (0.05) | 0.81 (0.31) | 0.22 (0.02) | 0.28 [0.10, 0.48] | 0.42 [0.26, 0.59] |
| joint, boundary linker, NEW combined-effect question | 0.80 [0.71, 0.87] | 0.27 (0.07) | 0.83 (0.32) | 0.83 (0.30) | 0.21 [0.09, 0.35] | 0.39 [0.25, 0.55] |
| joint, structured-effect linker (S2) | 0.79 [0.71, 0.85] | 0.30 (0.08) | 0.83 (0.34) | 0.78 (0.33) | 0.24 [0.11, 0.37] | 0.38 [0.25, 0.51] |
| zmax(per-commit, boundary joint) | 0.84 [0.73, 0.94] | 0.29 (0.02) | 0.38 (0.06) | 0.28 (0.02) | 0.36 [0.10, 0.69] | 0.56 [0.19, 0.89] |
| zmax(per-commit, boundary joint NEW question) | 0.82 [0.69, 0.95] | 0.24 (0.02) | 0.33 (0.05) | 0.22 (0.01) | 0.33 [0.06, 0.67] | 0.51 [0.15, 0.86] |
| zmax(per-commit, structured joint) | 0.83 [0.70, 0.94] | 0.35 (0.02) | 0.42 (0.05) | 0.33 (0.01) | 0.42 [0.16, 0.74] | 0.56 [0.20, 0.89] |

| paired comparison (A - B) | FPR | diff | 95% CI | P(boot diff<=0) | McNemar A-only/B-only, p |
|---|---|---|---|---|---|
| joint, boundary linker - per-commit | 1% | +0.09 | [-0.11, +0.33] | 0.18 | 2/1, 1.00 |
| joint, boundary linker - per-commit | 5% | +0.51 | [+0.15, +0.87] | 0.00 | 2/1, 1.00 |
| joint, boundary linker, NEW combined-effect question - per-commit | 1% | +0.08 | [-0.18, +0.37] | 0.23 | 1/2, 1.00 |
| joint, boundary linker, NEW combined-effect question - per-commit | 5% | +0.53 | [+0.18, +0.77] | 0.00 | 12/0, 0.00 |
| joint, structured-effect linker (S2) - per-commit | 1% | +0.11 | [-0.27, +0.44] | 0.23 | 3/3, 1.00 |
| joint, structured-effect linker (S2) - per-commit | 5% | +0.53 | [+0.15, +0.77] | 0.00 | 11/0, 0.00 |
| joint, boundary linker, NEW combined-effect question - joint, boundary linker | 1% | -0.02 | [-0.20, +0.23] | 0.53 | 0/2, 0.50 |
| joint, boundary linker, NEW combined-effect question - joint, boundary linker | 5% | +0.03 | [-0.36, +0.28] | 0.51 | 11/0, 0.00 |
| zmax(per-commit, boundary joint) - per-commit | 1% | +0.10 | [-0.01, +0.22] | 0.10 | 2/0, 0.50 |
| zmax(per-commit, boundary joint) - per-commit | 5% | +0.08 | [-0.02, +0.19] | 0.12 | 2/0, 0.50 |
| zmax(per-commit, boundary joint NEW question) - per-commit | 1% | +0.05 | [+0.00, +0.15] | 0.33 | 1/0, 1.00 |
| zmax(per-commit, boundary joint NEW question) - per-commit | 5% | +0.03 | [+0.00, +0.11] | 0.33 | 1/0, 1.00 |

linking: {"boundary_union": {"pair_recall": 0.69, "full_chain": 0.39, "benign_linked": 0.25, "xfeature_pair_recall": 0.6}, "struct7_S2": {"pair_recall": 0.28, "full_chain": 0.17, "benign_linked": 0.19, "xfeature_pair_recall": 0.28}}
tokens per held-out benign seq: {"per_commit": 9334, "linked_boundary_union": 12640, "linkedQ6_boundary_union": 12213, "linked_struct7_S2": 11460}

### FRESH split, attacks=adapt: attack seqs=18, cal=200, held-out=100
| method | AUC | det@1% (realized FPR) | det@5% (realized FPR) | conformal det@5% (realized) | matched det @5% FPR | matched det @12% FPR |
|---|---|---|---|---|---|---|
| per-commit | 0.87 [0.73, 0.98] | 0.36 (0.01) | 0.47 (0.04) | 0.33 (0.00) | 0.50 [0.17, 0.88] | 0.67 [0.30, 1.00] |
| joint, boundary linker | 0.85 [0.75, 0.93] | 0.44 (0.05) | 0.81 (0.31) | 0.39 (0.02) | 0.43 [0.17, 0.71] | 0.53 [0.31, 0.77] |
| joint, boundary linker, NEW combined-effect question | 0.82 [0.74, 0.91] | 0.36 (0.07) | 0.83 (0.32) | 0.83 (0.30) | 0.31 [0.09, 0.60] | 0.45 [0.25, 0.71] |
| joint, structured-effect linker (S2) | 0.77 [0.64, 0.88] | 0.35 (0.08) | 0.78 (0.34) | 0.78 (0.33) | 0.29 [0.12, 0.49] | 0.41 [0.25, 0.59] |
| zmax(per-commit, boundary joint) | 0.94 [0.87, 0.99] | 0.57 (0.02) | 0.68 (0.06) | 0.56 (0.02) | 0.66 [0.34, 1.00] | 0.89 [0.62, 1.00] |
| zmax(per-commit, boundary joint NEW question) | 0.92 [0.81, 0.99] | 0.53 (0.02) | 0.63 (0.05) | 0.50 (0.01) | 0.63 [0.32, 1.00] | 0.84 [0.50, 1.00] |
| zmax(per-commit, structured joint) | 0.85 [0.68, 0.98] | 0.46 (0.02) | 0.53 (0.05) | 0.44 (0.01) | 0.53 [0.21, 0.87] | 0.67 [0.31, 1.00] |

| paired comparison (A - B) | FPR | diff | 95% CI | P(boot diff<=0) | McNemar A-only/B-only, p |
|---|---|---|---|---|---|
| joint, boundary linker - per-commit | 1% | +0.08 | [-0.33, +0.51] | 0.36 | 4/3, 1.00 |
| joint, boundary linker - per-commit | 5% | +0.34 | [-0.07, +0.73] | 0.06 | 4/3, 1.00 |
| joint, boundary linker, NEW combined-effect question - per-commit | 1% | -0.00 | [-0.45, +0.51] | 0.48 | 3/5, 0.73 |
| joint, boundary linker, NEW combined-effect question - per-commit | 5% | +0.37 | [+0.02, +0.65] | 0.02 | 9/0, 0.00 |
| joint, structured-effect linker (S2) - per-commit | 1% | -0.01 | [-0.35, +0.31] | 0.47 | 2/4, 0.69 |
| joint, structured-effect linker (S2) - per-commit | 5% | +0.31 | [+0.01, +0.57] | 0.02 | 8/0, 0.01 |
| joint, boundary linker, NEW combined-effect question - joint, boundary linker | 1% | -0.08 | [-0.28, +0.17] | 0.72 | 0/3, 0.25 |
| joint, boundary linker, NEW combined-effect question - joint, boundary linker | 5% | +0.03 | [-0.28, +0.23] | 0.51 | 9/1, 0.02 |
| zmax(per-commit, boundary joint) - per-commit | 1% | +0.21 | [-0.02, +0.55] | 0.09 | 4/0, 0.12 |
| zmax(per-commit, boundary joint) - per-commit | 5% | +0.21 | [-0.03, +0.55] | 0.09 | 4/0, 0.12 |
| zmax(per-commit, boundary joint NEW question) - per-commit | 1% | +0.17 | [+0.00, +0.50] | 0.35 | 3/0, 0.25 |
| zmax(per-commit, boundary joint NEW question) - per-commit | 5% | +0.17 | [+0.00, +0.50] | 0.35 | 3/0, 0.25 |

linking: {"boundary_union": {"pair_recall": 0.63, "full_chain": 0.39, "benign_linked": 0.25, "xfeature_pair_recall": 0.6}, "struct7_S2": {"pair_recall": 0.28, "full_chain": 0.17, "benign_linked": 0.19, "xfeature_pair_recall": 0.28}}
tokens per held-out benign seq: {"per_commit": 9334, "linked_boundary_union": 12640, "linkedQ6_boundary_union": 12213, "linked_struct7_S2": 11460}