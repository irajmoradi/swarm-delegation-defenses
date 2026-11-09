# Run inventory and charge reconciliation

Every local run remains listed, including mock, smoke, failed preflight and superseded controls. Outcome reports do not pool those datasets. Charges from all paid runs still count.

| Run | Status | Logged completions | Returned cost | Conservative charge | Flags | Control audit |
|---|---|---:|---:|---:|---:|---|
| 20261107T063244850982Z-dry | complete | 0 | $0.000000 | $0.000000 | 0 | False |
| 20261107T063342700776Z-smoke | complete | 92 | $0.001452 | $0.001452 | 0 | False |
| 20261107T064013391682Z-full | complete | 1568 | $0.043033 | $0.043033 | 7 | False |
| 20261107T064426545704Z-diversity | preflight_failed | 14 | $0.000625 | $0.000625 | 3 | False |
| 20261107T064719208501Z-diversity | complete | 6185 | $0.184087 | $0.709087 | 23 | False |
| 20261107T065609538438Z-ledger | complete | 879 | $0.016725 | $0.016725 | 0 | True |
| 20261107T065945724810Z-ledger | complete | 922 | $0.017801 | $0.042801 | 1 | False |
| 20261107T080457234078Z-v2 | preflight_failed | 2 | $0.000057 | $0.000057 | 0 | False |
| 20261107T080627520471Z-v2 | preflight_failed | 5 | $0.000489 | $0.000489 | 2 | False |
| 20261107T080958276252Z-v2 | complete | 6679 | $0.309727 | $0.309727 | 0 | False |
| 20261107T083446934699Z-v2-memory | complete | 2506 | $0.072819 | $0.147819 | 4 | False |
| 20261107T085357565185Z-coordinator | complete | 1149 | $0.029445 | $0.104445 | 3 | False |
