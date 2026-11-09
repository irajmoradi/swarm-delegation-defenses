
### calib=cal N=0: attack seqs=18, cal seqs=100, held-out benign seqs=100
linking recall (pairs) 0.28 CI[0.17, 0.33], full chain in one group 0.00; benign non-singleton groups 0.11, mean group size 1.12
| method | det@1% | det@2% | det@5% | AUC | emp. FPR@5% (other benign set) | tokens/seq (benign) |
|---|---|---|---|---|---|---|
| per-commit (nano) | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.25 [0.16, 0.34] | 0.02 | 2442 |
| per-commit strong (mini) | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.95 [0.89, 0.98] | 0.12 | 2862 |
| linked-joint (nano) | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.31 [0.20, 0.42] | 0.02 | 2610 |
| max(linked, per-commit) (nano) | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.29 [0.19, 0.42] | 0.02 | nan |
| oracle-joint (nano) | 0.00 [0.00, 0.67] | 0.17 [0.00, 0.70] | 0.53 [0.00, 0.90] | 0.78 [0.60, 0.92] | 0.13 | nan |

### calib=cal N=10: attack seqs=18, cal seqs=100, held-out benign seqs=100
linking recall (pairs) 0.31 CI[0.17, 0.44], full chain in one group 0.06; benign non-singleton groups 0.44, mean group size 1.62
| method | det@1% | det@2% | det@5% | AUC | emp. FPR@5% (other benign set) | tokens/seq (benign) |
|---|---|---|---|---|---|---|
| per-commit (nano) | 0.00 [0.00, 0.00] | 0.01 [0.00, 0.01] | 0.01 [0.01, 0.02] | 0.41 [0.31, 0.51] | 0.02 | 10667 |
| per-commit strong (mini) | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.77 [0.64, 0.89] | 0.47 | 12444 |
| linked-joint (nano) | 0.00 [0.00, 0.01] | 0.01 [0.00, 0.01] | 0.02 [0.00, 0.03] | 0.46 [0.34, 0.59] | 0.02 | 14319 |
| max(linked, per-commit) (nano) | 0.00 [0.00, 0.00] | 0.01 [0.00, 0.01] | 0.01 [0.01, 0.02] | 0.41 [0.30, 0.50] | 0.02 | nan |
| oracle-joint (nano) | 0.00 [0.00, 0.00] | 0.01 [0.00, 0.01] | 0.02 [0.01, 0.02] | 0.48 [0.38, 0.57] | 0.02 | nan |

### calib=cal N=10 (perturbed attacks): attack seqs=18, cal seqs=100, held-out benign seqs=100
linking recall (pairs) 0.26 CI[0.11, 0.41], full chain in one group 0.06; benign non-singleton groups 0.44, mean group size 1.62
| method | det@1% | det@2% | det@5% | AUC | emp. FPR@5% (other benign set) | tokens/seq (benign) |
|---|---|---|---|---|---|---|
| per-commit (nano) | 0.00 [0.00, 0.00] | 0.01 [0.00, 0.01] | 0.01 [0.01, 0.02] | 0.41 [0.31, 0.50] | 0.02 | 10667 |
| per-commit strong (mini) | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 1.00 [1.00, 1.00] | 0.79 [0.68, 0.90] | 0.47 | 12444 |
| linked-joint (nano) | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.01] | 0.01 [0.00, 0.02] | 0.46 [0.34, 0.59] | 0.02 | 14319 |
| max(linked, per-commit) (nano) | 0.00 [0.00, 0.00] | 0.01 [0.00, 0.01] | 0.01 [0.01, 0.02] | 0.41 [0.32, 0.50] | 0.02 | nan |
| oracle-joint (nano) | 0.00 [0.00, 0.00] | 0.01 [0.00, 0.01] | 0.02 [0.01, 0.02] | 0.48 [0.37, 0.57] | 0.02 | nan |

### calib=benign_eval N=0: attack seqs=18, cal seqs=100, held-out benign seqs=100
linking recall (pairs) 0.28 CI[0.17, 0.33], full chain in one group 0.00; benign non-singleton groups 0.11, mean group size 1.12
| method | det@1% | det@2% | det@5% | AUC | emp. FPR@5% (other benign set) | tokens/seq (benign) |
|---|---|---|---|---|---|---|
| per-commit (nano) | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.25 [0.16, 0.34] | 0.15 | 2442 |
| per-commit strong (mini) | 0.22 [0.02, 0.57] | 0.28 [0.04, 0.67] | 0.44 [0.09, 1.00] | 0.95 [0.89, 0.98] | 0.00 | 2862 |
| linked-joint (nano) | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.31 [0.20, 0.42] | 0.12 | 2610 |
| max(linked, per-commit) (nano) | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.29 [0.19, 0.42] | 0.15 | nan |
| oracle-joint (nano) | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.00] | 0.00 [0.00, 0.50] | 0.78 [0.60, 0.92] | 0.01 | nan |

### calib=benign_eval N=10: attack seqs=18, cal seqs=100, held-out benign seqs=100
linking recall (pairs) 0.31 CI[0.17, 0.44], full chain in one group 0.06; benign non-singleton groups 0.44, mean group size 1.62
| method | det@1% | det@2% | det@5% | AUC | emp. FPR@5% (other benign set) | tokens/seq (benign) |
|---|---|---|---|---|---|---|
| per-commit (nano) | 0.01 [0.00, 0.01] | 0.01 [0.01, 0.03] | 0.04 [0.02, 0.06] | 0.41 [0.31, 0.50] | 0.13 | 10667 |
| per-commit strong (mini) | 0.18 [0.01, 0.51] | 0.19 [0.02, 0.52] | 0.24 [0.05, 0.55] | 0.77 [0.64, 0.89] | 0.00 | 12444 |
| linked-joint (nano) | 0.01 [0.00, 0.01] | 0.01 [0.00, 0.03] | 0.03 [0.01, 0.07] | 0.46 [0.34, 0.60] | 0.11 | 14319 |
| max(linked, per-commit) (nano) | 0.01 [0.00, 0.01] | 0.01 [0.01, 0.03] | 0.04 [0.02, 0.06] | 0.41 [0.31, 0.50] | 0.13 | nan |
| oracle-joint (nano) | 0.01 [0.00, 0.02] | 0.02 [0.01, 0.04] | 0.05 [0.02, 0.09] | 0.48 [0.38, 0.57] | 0.15 | nan |

### calib=benign_eval N=10 (perturbed attacks): attack seqs=18, cal seqs=100, held-out benign seqs=100
linking recall (pairs) 0.26 CI[0.11, 0.41], full chain in one group 0.06; benign non-singleton groups 0.44, mean group size 1.62
| method | det@1% | det@2% | det@5% | AUC | emp. FPR@5% (other benign set) | tokens/seq (benign) |
|---|---|---|---|---|---|---|
| per-commit (nano) | 0.01 [0.00, 0.01] | 0.01 [0.01, 0.03] | 0.04 [0.02, 0.07] | 0.41 [0.31, 0.51] | 0.13 | 10667 |
| per-commit strong (mini) | 0.18 [0.01, 0.51] | 0.19 [0.02, 0.52] | 0.24 [0.05, 0.55] | 0.79 [0.68, 0.90] | 0.00 | 12444 |
| linked-joint (nano) | 0.00 [0.00, 0.01] | 0.01 [0.00, 0.02] | 0.02 [0.00, 0.06] | 0.46 [0.33, 0.58] | 0.11 | 14319 |
| max(linked, per-commit) (nano) | 0.01 [0.00, 0.01] | 0.01 [0.01, 0.03] | 0.04 [0.02, 0.06] | 0.41 [0.31, 0.51] | 0.13 | nan |
| oracle-joint (nano) | 0.01 [0.00, 0.02] | 0.02 [0.01, 0.04] | 0.05 [0.02, 0.09] | 0.48 [0.38, 0.58] | 0.15 | nan |

leakage: {"trivial_feature_cv_auc": 0.4644097222222222, "n_benign": 192, "n_attack": 18, "lines_changed_benign_mean": 20.40625, "lines_changed_attack_mean": 19.11111111111111, "files_benign_mean": 1.046875, "files_attack_mean": 1.2222222222222223, "malicious_lines_mean": 3.6666666666666665, "splice_modes": {"applied": 13, "anchor_fallback": 5}}